import copy
import tempfile
import unittest
from pathlib import Path

from agent_quality_lab.domain import BusinessTools, Identity, Store
from agent_quality_lab.money import amount_view, format_amount
from agent_quality_lab.runtime import ToolError


class MoneyDisplayTests(unittest.TestCase):
    def test_integer_cents_keep_small_fraction_and_large_amount_exact(self):
        # AQL-001: display units must agree with the persisted integer cents.
        for cents, expected in [(1, "CNY 0.01"), (105, "CNY 1.05"), (9999, "CNY 99.99"),
                                (10000, "CNY 100.00"), (9223372036854775807, "CNY 92233720368547758.07")]:
            with self.subTest(cents=cents):
                self.assertEqual(format_amount(cents, "CNY"), expected)

    def test_nested_view_preserves_source_and_absent_refund(self):
        original = {"invoices": [{"id": "a", "amount_cents": 105, "currency": "CNY"}], "refund": None}
        before = copy.deepcopy(original)
        view = amount_view(original)
        self.assertEqual(view, {"invoices": [{"id": "a", "amount_cents": 105, "currency": "CNY",
                                             "amount_display": "CNY 1.05"}], "refund": None})
        self.assertEqual(original, before)

    def test_tool_views_match_approval_and_storage_through_refund_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store.create(Path(directory) / "business.sqlite3")
            try:
                # Non-whole amount prevents a fix hard-coded to the demo's 100.00.
                with store.connection:
                    store.connection.execute("UPDATE invoices SET amount_cents=105 WHERE id='invoice-a-double'")
                    store.connection.execute("UPDATE payments SET amount_cents=105 WHERE invoice_id='invoice-a-double'")
                business = BusinessTools(store, Identity("tenant-a", "test-user", "finance"))
                tools = {tool.name: tool for tool in business.registry()}
                before = store.snapshot()
                invoice = tools["get_invoice"].invoke({"invoice_id": "invoice-a-double"})
                listed = tools["list_invoices"].invoke({"customer_id": "customer-a"})
                proposal = tools["propose_refund"].invoke({"payment_id": "payment-a-second"})
                for row in [invoice["invoice"], *invoice["payments"], listed["invoices"][0], proposal]:
                    self.assertEqual((row["amount_cents"], row["amount_display"]), (105, "CNY 1.05"))
                self.assertEqual(store.snapshot(), before)
                self.assertEqual(tools["get_refund"].invoke({"payment_id": "payment-a-second"}), {"refund": None})
                with self.assertRaises(ToolError) as raised:
                    tools["create_refund"].invoke({"proposal_id": proposal["proposal_id"]})
                self.assertEqual(raised.exception.code, "confirmation_required")
                approved = business.approve(proposal["proposal_id"])
                self.assertEqual(format_amount(approved["amount_cents"], approved["currency"]), proposal["amount_display"])
                created = tools["create_refund"].invoke({"proposal_id": proposal["proposal_id"]})["refund"]
                queried = tools["get_refund"].invoke({"payment_id": "payment-a-second"})["refund"]
                self.assertEqual(queried, created)
                self.assertEqual((created["amount_cents"], created["amount_display"], created["status"]),
                                 (105, "CNY 1.05", "pending"))
                self.assertEqual(store.snapshot()["refunds"], [{key: value for key, value in created.items()
                                                               if key != "amount_display"}])
                self.assertNotIn("amount_display", business.proposals[proposal["proposal_id"]])
            finally:
                store.close()
