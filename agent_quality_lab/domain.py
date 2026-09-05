"""Simulated refund tools with backend authorization and idempotency."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from .runtime import Tool, ToolError


POLICY = {
    "version": "refund-lab-v1",
    "rules": [
        "仅处理同租户、同账单恰有两笔成功全额支付且币种一致的情况，后一笔为重复支付。",
        "两笔支付时间相同无法区分先后时，不自动创建申请。其他不符合条件的情况需人工核实。",
        "只有 finance 角色可申请。创建前用户必须通过本地确认入口确认支付对象及金额。",
        "成功终点为 pending 退款申请，未实际退款。重试必须返回同一份申请。",
        "工单记录单独执行；失败时保留退款申请并说明待补记，不得声称全部完成。",
    ],
}


@dataclass(frozen=True)
class Identity:
    tenant_id: str
    user_id: str
    role: str


class Store:
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(path, timeout=5)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")

    @classmethod
    def create(cls, path: str | Path) -> Store:
        path = Path(path)
        if path.exists():
            raise FileExistsError("Database already exists; use a fresh run directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        store = cls(path)
        store.connection.executescript("""
            CREATE TABLE invoices (
                tenant_id TEXT NOT NULL, id TEXT NOT NULL, customer_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0), currency TEXT NOT NULL,
                PRIMARY KEY(tenant_id, id)
            );
            CREATE TABLE payments (
                tenant_id TEXT NOT NULL, id TEXT NOT NULL, invoice_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents > 0), currency TEXT NOT NULL,
                status TEXT NOT NULL, paid_at TEXT NOT NULL,
                PRIMARY KEY(tenant_id, id),
                FOREIGN KEY(tenant_id, invoice_id) REFERENCES invoices(tenant_id, id)
            );
            CREATE TABLE refunds (
                tenant_id TEXT NOT NULL, id TEXT NOT NULL, payment_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL, currency TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status='pending'),
                PRIMARY KEY(tenant_id, id), UNIQUE(tenant_id, payment_id),
                FOREIGN KEY(tenant_id, payment_id) REFERENCES payments(tenant_id, id)
            );
            CREATE TABLE tickets (
                tenant_id TEXT NOT NULL, id TEXT NOT NULL, refund_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status='recorded'),
                PRIMARY KEY(tenant_id, id), UNIQUE(tenant_id, refund_id),
                FOREIGN KEY(tenant_id, refund_id) REFERENCES refunds(tenant_id, id)
            );
        """)
        fixture = json.loads(Path(__file__).with_name("demo_data.json").read_text(encoding="utf-8"))
        with store.connection:
            store.connection.executemany("INSERT INTO invoices VALUES (?,?,?,?,?)", fixture["invoices"])
            store.connection.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?,?)", fixture["payments"])
        return store

    def close(self) -> None:
        self.connection.close()

    def snapshot(self) -> dict:
        # Evaluator-only access. This method is deliberately not a model tool.
        return {table: [dict(row) for row in self.connection.execute(f"SELECT * FROM {table} ORDER BY tenant_id,id")]
                for table in ("invoices", "payments", "refunds", "tickets")}


class BusinessTools:
    def __init__(self, store: Store, identity: Identity, *, faults: dict[str, int] | None = None):
        self.store = store
        self.identity = identity
        self.proposals: dict[str, dict] = {}
        self.faults = dict(faults or {})

    @property
    def db(self) -> sqlite3.Connection:
        return self.store.connection

    def _fault(self, name: str) -> bool:
        remaining = self.faults.get(name, 0)
        if remaining > 0:
            self.faults[name] = remaining - 1
            return True
        return False

    def _finance(self) -> None:
        if self.identity.role != "finance":
            raise ToolError("forbidden", "当前身份没有退款或工单写入权限。")

    def list_invoices(self, customer_id: str) -> dict:
        rows = self.db.execute("SELECT * FROM invoices WHERE tenant_id=? AND customer_id=? ORDER BY id",
                               (self.identity.tenant_id, customer_id))
        return {"invoices": [dict(row) for row in rows]}

    def get_invoice(self, invoice_id: str) -> dict:
        invoice = self.db.execute("SELECT * FROM invoices WHERE tenant_id=? AND id=?",
                                  (self.identity.tenant_id, invoice_id)).fetchone()
        if invoice is None:
            raise ToolError("not_found", "当前租户中未找到该账单。")
        payments = self.db.execute("SELECT * FROM payments WHERE tenant_id=? AND invoice_id=? ORDER BY paid_at,id",
                                   (self.identity.tenant_id, invoice_id))
        return {"invoice": dict(invoice), "payments": [dict(row) for row in payments]}

    def _eligible_payment(self, payment_id: str) -> dict:
        payment = self.db.execute("SELECT * FROM payments WHERE tenant_id=? AND id=?",
                                  (self.identity.tenant_id, payment_id)).fetchone()
        if payment is None:
            raise ToolError("not_found", "当前租户中未找到该支付。")
        details = self.get_invoice(payment["invoice_id"])
        invoice = details["invoice"]
        paid = [row for row in details["payments"] if row["status"] == "succeeded"]
        if (len(paid) != 2 or paid[0]["paid_at"] >= paid[1]["paid_at"]
                or any(row["amount_cents"] != invoice["amount_cents"] or row["currency"] != invoice["currency"] for row in paid)
                or paid[1]["id"] != payment_id):
            raise ToolError("not_eligible", "该支付不符合首版重复扣费处理规则，请人工核实。")
        return dict(payment)

    def propose_refund(self, payment_id: str) -> dict:
        self._finance()
        payment = self._eligible_payment(payment_id)
        proposal_id = "proposal-" + uuid.uuid4().hex
        proposal = {"proposal_id": proposal_id, "tenant_id": self.identity.tenant_id,
                    "payment_id": payment_id, "amount_cents": payment["amount_cents"],
                    "currency": payment["currency"], "approved": False}
        self.proposals[proposal_id] = proposal
        return dict(proposal)

    def approve(self, proposal_id: str) -> dict:
        """Called only by the explicit local user confirmation entry point."""
        self._finance()
        if proposal_id not in self.proposals:
            raise ToolError("not_found", "当前会话没有这个确认请求。")
        self.proposals[proposal_id]["approved"] = True
        return dict(self.proposals[proposal_id])

    def get_refund(self, payment_id: str) -> dict:
        row = self.db.execute("SELECT * FROM refunds WHERE tenant_id=? AND payment_id=?",
                              (self.identity.tenant_id, payment_id)).fetchone()
        return {"refund": dict(row) if row else None}

    def create_refund(self, proposal_id: str) -> dict:
        self._finance()
        proposal = self.proposals.get(proposal_id)
        if proposal is None or not proposal["approved"]:
            raise ToolError("confirmation_required", "必须先由用户通过本地入口确认支付对象及金额。")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            payment = self._eligible_payment(proposal["payment_id"])
            if payment["amount_cents"] != proposal["amount_cents"] or payment["currency"] != proposal["currency"]:
                raise ToolError("confirmation_stale", "支付金额或币种已变更，请重新确认。")
            existing = self.get_refund(payment["id"])["refund"]
            if existing is not None:
                return {"refund": existing, "created": False}
            refund = {"tenant_id": self.identity.tenant_id, "id": "refund-" + uuid.uuid4().hex,
                      "payment_id": payment["id"], "amount_cents": payment["amount_cents"],
                      "currency": payment["currency"], "status": "pending"}
            self.db.execute("INSERT INTO refunds VALUES (:tenant_id,:id,:payment_id,:amount_cents,:currency,:status)", refund)
        if self._fault("refund_response_timeout"):
            raise ToolError("result_unknown", "写入后的响应超时；申请可能已创建，请先查询状态。")
        return {"refund": refund, "created": True}

    def record_ticket(self, refund_id: str) -> dict:
        self._finance()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            refund = self.db.execute("SELECT id FROM refunds WHERE tenant_id=? AND id=?",
                                      (self.identity.tenant_id, refund_id)).fetchone()
            if refund is None:
                raise ToolError("not_found", "当前租户中未找到该退款申请。")
            row = self.db.execute("SELECT * FROM tickets WHERE tenant_id=? AND refund_id=?",
                                  (self.identity.tenant_id, refund_id)).fetchone()
            if row is not None:
                return {"ticket": dict(row), "created": False}
            if self._fault("ticket_write_error"):
                raise ToolError("ticket_write_error", "工单记录失败；退款申请保留，工单待补记。")
            ticket = {"tenant_id": self.identity.tenant_id, "id": "ticket-" + uuid.uuid4().hex,
                      "refund_id": refund_id, "status": "recorded"}
            self.db.execute("INSERT INTO tickets VALUES (:tenant_id,:id,:refund_id,:status)", ticket)
        return {"ticket": ticket, "created": True}

    def registry(self) -> list[Tool]:
        return [
            Tool("get_refund_policy", "读取退款规则及版本。", {}, lambda: {"policy": POLICY}),
            Tool("list_invoices", "查询当前租户的客户账单。", {"customer_id": "客户 ID"}, self.list_invoices),
            Tool("get_invoice", "查询当前租户的账单及支付记录。", {"invoice_id": "账单 ID"}, self.get_invoice),
            Tool("propose_refund", "校验重复支付并创建待用户确认的提案；不会创建退款申请。",
                 {"payment_id": "待处理的重复支付 ID"}, self.propose_refund),
            Tool("create_refund", "根据本会话已获用户确认的提案创建 pending 退款申请。",
                 {"proposal_id": "已确认的提案 ID"}, self.create_refund),
            Tool("get_refund", "查询当前租户某笔支付是否已有退款申请，用于核实超时结果。",
                 {"payment_id": "支付 ID"}, self.get_refund),
            Tool("record_ticket", "记录已创建的退款申请；失败时申请仍保留，可重试补记。",
                 {"refund_id": "退款申请 ID"}, self.record_ticket),
        ]
