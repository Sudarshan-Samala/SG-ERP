import unittest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.finance import AccountCreate, JournalEntryCreate
from app.schemas.helpdesk import TicketCreate
from app.schemas.inventory_assets import AssetCreate, InventoryItemCreate


class FinanceAssetsHelpdeskValidationTests(unittest.TestCase):
    def test_finance_rejects_unknown_account_type(self):
        with self.assertRaises(ValidationError):
            AccountCreate(name="Cash", type="UNKNOWN")

    def test_finance_rejects_non_positive_journal_amount(self):
        with self.assertRaises(ValidationError):
            JournalEntryCreate(account_id=uuid4(), date=datetime.now(timezone.utc), description="Entry", amount=0, type="DEBIT")

    def test_inventory_rejects_negative_quantity(self):
        with self.assertRaises(ValidationError):
            InventoryItemCreate(name="Paper", quantity=-1)

    def test_asset_rejects_unknown_status(self):
        with self.assertRaises(ValidationError):
            AssetCreate(name="Laptop", asset_tag="IT-1", status="LOST")

    def test_helpdesk_rejects_unknown_priority(self):
        with self.assertRaises(ValidationError):
            TicketCreate(subject="Network down", description="Internet unavailable", priority="URGENT")

    def test_helpdesk_accepts_critical_priority(self):
        ticket = TicketCreate(subject="Server down", description="Production service unavailable", priority="CRITICAL")
        self.assertEqual(ticket.priority, "CRITICAL")


if __name__ == "__main__":
    unittest.main()
