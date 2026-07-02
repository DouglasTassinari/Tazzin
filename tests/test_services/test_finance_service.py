from datetime import date

import pytest

from app.core.exceptions import EntityNotFoundError, ValidationError
from app.database.models.finance import Account, AccountType, InvoiceDirection, InvoiceStatus, TransactionType
from app.services.finance_service import FinanceService


def _make_account(session) -> Account:
    account = Account(code="1000", name="Cash", account_type=AccountType.ASSET)
    session.add(account)
    session.flush()
    return account


def test_create_invoice_persists_as_open(session):
    service = FinanceService(session)

    invoice = service.create_invoice(
        invoice_number="INV-100",
        direction=InvoiceDirection.RECEIVABLE,
        counterparty_name="Acme Corp",
        amount=750,
        issue_date=date(2026, 3, 1),
        due_date=date(2026, 4, 1),
    )

    assert invoice.id is not None
    assert invoice.status == InvoiceStatus.OPEN


def test_create_invoice_rejects_non_positive_amount(session):
    service = FinanceService(session)

    with pytest.raises(ValidationError):
        service.create_invoice(
            invoice_number="INV-101",
            direction=InvoiceDirection.RECEIVABLE,
            counterparty_name="Acme Corp",
            amount=0,
            issue_date=date(2026, 3, 1),
            due_date=date(2026, 4, 1),
        )


def test_transition_invoice_follows_allowed_path(session):
    service = FinanceService(session)
    invoice = service.create_invoice(
        invoice_number="INV-102",
        direction=InvoiceDirection.RECEIVABLE,
        counterparty_name="Acme Corp",
        amount=300,
        issue_date=date(2026, 3, 1),
        due_date=date(2026, 4, 1),
    )

    updated = service.transition_invoice(invoice.id, InvoiceStatus.OVERDUE)
    assert updated.status == InvoiceStatus.OVERDUE

    with pytest.raises(ValidationError):
        service.transition_invoice(invoice.id, InvoiceStatus.OPEN)


def test_transition_unknown_invoice_raises_not_found(session):
    service = FinanceService(session)
    with pytest.raises(EntityNotFoundError):
        service.transition_invoice(999, InvoiceStatus.PAID)


def test_record_transaction_persists(session):
    account = _make_account(session)
    service = FinanceService(session)

    transaction = service.record_transaction(
        account_id=account.id,
        transaction_type=TransactionType.CREDIT,
        amount=250,
        transaction_date=date(2026, 3, 5),
        description="Customer payment",
    )

    assert transaction.id is not None
    assert transaction.amount == 250


def test_record_transaction_rejects_non_positive_amount(session):
    account = _make_account(session)
    service = FinanceService(session)

    with pytest.raises(ValidationError):
        service.record_transaction(
            account_id=account.id,
            transaction_type=TransactionType.DEBIT,
            amount=-5,
            transaction_date=date(2026, 3, 5),
            description="Invalid",
        )


def test_outstanding_summary_returns_receivables_and_payables(session):
    service = FinanceService(session)
    service.create_invoice(
        invoice_number="INV-200",
        direction=InvoiceDirection.RECEIVABLE,
        counterparty_name="Acme Corp",
        amount=400,
        issue_date=date(2026, 3, 1),
        due_date=date(2026, 4, 1),
    )
    service.create_invoice(
        invoice_number="INV-201",
        direction=InvoiceDirection.PAYABLE,
        counterparty_name="Supplier Co",
        amount=150,
        issue_date=date(2026, 3, 1),
        due_date=date(2026, 4, 1),
    )

    summary = service.outstanding_summary()

    assert summary == {"receivables": 400.0, "payables": 150.0}


def test_cash_position_wraps_repository(session):
    account = _make_account(session)
    service = FinanceService(session)
    service.record_transaction(
        account_id=account.id,
        transaction_type=TransactionType.CREDIT,
        amount=100,
        transaction_date=date(2026, 5, 10),
        description="Payment",
    )

    rows = service.cash_position(date(2026, 5, 1), date(2026, 5, 31))

    assert rows == [("2026-05", 100.0)]
