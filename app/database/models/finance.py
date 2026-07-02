"""Finance module schema: Account, Invoice, Transaction.

Invoices link back to Sales/Purchasing loosely via nullable id columns
(an invoice can exist without a matching order in the demo data set,
same as in a real ERP when invoices are entered manually).
"""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.models.core import TimestampMixin


class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class InvoiceDirection(str, enum.Enum):
    RECEIVABLE = "receivable"
    PAYABLE = "payable"


class InvoiceStatus(str, enum.Enum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class TransactionType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class Account(TimestampMixin, Base):
    __tablename__ = "finance_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType))


class Invoice(TimestampMixin, Base):
    __tablename__ = "finance_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    direction: Mapped[InvoiceDirection] = mapped_column(Enum(InvoiceDirection))
    counterparty_name: Mapped[str] = mapped_column(String(150))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.OPEN)
    source_sales_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales_orders.id"), nullable=True
    )
    source_purchase_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchasing_orders.id"), nullable=True
    )


class Transaction(Base):
    __tablename__ = "finance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("finance_accounts.id"), index=True)
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("finance_invoices.id"), nullable=True, index=True
    )
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    transaction_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String(200))
