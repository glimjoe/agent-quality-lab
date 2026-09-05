import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent_quality_lab.domain import BusinessTools, Identity, Store
from agent_quality_lab.runtime import ToolError


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "business.sqlite3"
        self.store = Store.create(self.path)
        self.addCleanup(self.store.close)
        self.finance = BusinessTools(self.store, Identity("tenant-a", "alice", "finance"))

    def assertError(self, code, action, *args):
        with self.assertRaises(ToolError) as raised:
            action(*args)
        self.assertEqual(raised.exception.code, code)

    def approved(self, business=None):
        business = business or self.finance
        proposal = business.propose_refund("payment-a-second")
        business.approve(proposal["proposal_id"])
        return proposal["proposal_id"]

    def test_pending_refund_and_ticket_preserve_source_records(self):
        before = self.store.snapshot()
        proposal = self.finance.propose_refund("payment-a-second")
        self.assertEqual(self.store.snapshot(), before)
        self.assertEqual(proposal["amount_cents"], 10000)
        self.finance.approve(proposal["proposal_id"])
        refund = self.finance.create_refund(proposal["proposal_id"])["refund"]
        self.assertEqual((refund["payment_id"], refund["amount_cents"], refund["currency"], refund["status"]),
                         ("payment-a-second", 10000, "CNY", "pending"))
        ticket = self.finance.record_ticket(refund["id"])["ticket"]
        after = self.store.snapshot()
        self.assertEqual(after["invoices"], before["invoices"])
        self.assertEqual(after["payments"], before["payments"])
        self.assertEqual(after["refunds"], [refund])
        self.assertEqual(after["tickets"], [ticket])

    def test_viewer_cannot_write_even_with_valid_identifiers(self):
        proposal = self.approved()
        refund = self.finance.create_refund(proposal)["refund"]
        viewer = BusinessTools(self.store, Identity("tenant-a", "bob", "viewer"))
        before = self.store.snapshot()
        for operation, identifier in [(viewer.propose_refund, "payment-a-second"),
                                      (viewer.approve, proposal), (viewer.create_refund, proposal),
                                      (viewer.record_ticket, refund["id"])]:
            with self.subTest(operation=operation.__name__):
                self.assertError("forbidden", operation, identifier)
        self.assertEqual(before, self.store.snapshot())

    def test_tenant_boundary_applies_to_reads_and_writes(self):
        other = BusinessTools(self.store, Identity("tenant-b", "bob", "finance"))
        proposal = other.propose_refund("payment-b-second")
        other.approve(proposal["proposal_id"])
        refund = other.create_refund(proposal["proposal_id"])["refund"]
        before = self.store.snapshot()
        self.assertEqual(self.finance.list_invoices("customer-b"), {"invoices": []})
        self.assertEqual(self.finance.get_refund("payment-b-second"), {"refund": None})
        self.assertError("not_found", self.finance.get_invoice, "invoice-b-double")
        self.assertError("not_found", self.finance.propose_refund, "payment-b-second")
        self.assertError("not_found", self.finance.record_ticket, refund["id"])
        self.assertEqual(before, self.store.snapshot())

    def test_first_and_single_payments_are_ineligible(self):
        for payment in ("payment-a-first", "payment-a-single"):
            with self.subTest(payment=payment):
                self.assertError("not_eligible", self.finance.propose_refund, payment)
        self.assertFalse(self.store.snapshot()["refunds"])

    def test_amount_currency_status_and_tied_timestamp_boundaries(self):
        mutations = [("amount_cents", 9999), ("currency", "USD"),
                     ("status", "failed"), ("paid_at", "2026-09-01T01:00:00Z")]
        original = dict(self.store.connection.execute("SELECT * FROM payments WHERE id='payment-a-second'").fetchone())
        for column, value in mutations:
            with self.subTest(column=column):
                with self.store.connection:
                    self.store.connection.execute(f"UPDATE payments SET {column}=? WHERE id='payment-a-second'", (value,))
                self.assertError("not_eligible", self.finance.propose_refund, "payment-a-second")
                with self.store.connection:
                    self.store.connection.execute(f"UPDATE payments SET {column}=? WHERE id='payment-a-second'", (original[column],))

    def test_third_successful_payment_requires_manual_review(self):
        with self.store.connection:
            self.store.connection.execute("INSERT INTO payments VALUES (?,?,?,?,?,?,?)",
                ("tenant-a", "payment-a-third", "invoice-a-double", 10000, "CNY", "succeeded", "2026-09-01T01:10:00Z"))
        self.assertError("not_eligible", self.finance.propose_refund, "payment-a-third")

    def test_confirmation_is_required_and_session_scoped(self):
        proposal = self.finance.propose_refund("payment-a-second")
        self.assertError("confirmation_required", self.finance.create_refund, proposal["proposal_id"])
        self.assertError("confirmation_required", self.finance.create_refund, "invented-id")
        self.finance.approve(proposal["proposal_id"])
        other_session = BusinessTools(self.store, self.finance.identity)
        self.assertError("confirmation_required", other_session.create_refund, proposal["proposal_id"])
        self.assertFalse(self.store.snapshot()["refunds"])

    def test_confirmed_amount_change_prevents_write(self):
        proposal_id = self.approved()
        with self.store.connection:
            self.store.connection.execute("UPDATE invoices SET amount_cents=12000 WHERE id='invoice-a-double'")
            self.store.connection.execute("UPDATE payments SET amount_cents=12000 WHERE invoice_id='invoice-a-double'")
        self.assertError("confirmation_stale", self.finance.create_refund, proposal_id)
        self.assertFalse(self.store.snapshot()["refunds"])

    def test_retry_and_new_proposal_return_same_refund_and_ticket(self):
        first = self.finance.create_refund(self.approved())
        repeated = self.finance.create_refund(self.approved())
        self.assertTrue(first["created"])
        self.assertFalse(repeated["created"])
        self.assertEqual(first["refund"], repeated["refund"])
        ticket = self.finance.record_ticket(first["refund"]["id"])
        repeated_ticket = self.finance.record_ticket(first["refund"]["id"])
        self.assertEqual(ticket["ticket"], repeated_ticket["ticket"])
        self.assertFalse(repeated_ticket["created"])

    def test_concurrent_connections_create_one_refund(self):
        barrier = threading.Barrier(2)
        def submit(user):
            store = Store(self.path)
            try:
                business = BusinessTools(store, Identity("tenant-a", user, "finance"))
                proposal_id = self.approved(business)
                barrier.wait(timeout=5)
                return business.create_refund(proposal_id)
            finally:
                store.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(submit, ("alice", "bob")))
        self.assertEqual(results[0]["refund"], results[1]["refund"])
        self.assertEqual(sum(result["created"] for result in results), 1)
        self.assertEqual(len(self.store.snapshot()["refunds"]), 1)

    def test_post_commit_timeout_can_be_queried_and_retried(self):
        business = BusinessTools(self.store, self.finance.identity, faults={"refund_response_timeout": 1})
        proposal_id = self.approved(business)
        self.assertError("result_unknown", business.create_refund, proposal_id)
        persisted = business.get_refund("payment-a-second")["refund"]
        self.assertIsNotNone(persisted)
        retried = business.create_refund(proposal_id)
        self.assertEqual(persisted, retried["refund"])
        self.assertFalse(retried["created"])
        self.assertEqual(len(self.store.snapshot()["refunds"]), 1)

    def test_ticket_failure_preserves_refund_and_can_be_repaired(self):
        business = BusinessTools(self.store, self.finance.identity, faults={"ticket_write_error": 1})
        refund = business.create_refund(self.approved(business))["refund"]
        self.assertError("ticket_write_error", business.record_ticket, refund["id"])
        self.assertEqual(self.store.snapshot()["refunds"], [refund])
        self.assertFalse(self.store.snapshot()["tickets"])
        business.record_ticket(refund["id"])
        self.assertEqual(len(self.store.snapshot()["tickets"]), 1)

    def test_database_initialization_never_overwrites_existing_run(self):
        before = self.store.snapshot()
        with self.assertRaises(FileExistsError):
            Store.create(self.path)
        self.assertEqual(before, self.store.snapshot())
