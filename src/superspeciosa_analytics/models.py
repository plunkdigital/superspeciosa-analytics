from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


MONEY = Numeric(14, 2)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    shopify_customer_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    shopify_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    shopify_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    shopify_order_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    shopify_order_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    has_successful_payment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    display_financial_status: Mapped[str | None] = mapped_column(
        String(40)
    )

    is_test: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    # Revenue after discounts, excluding shipping, tax and fees.
    product_revenue: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    shipping_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    fee_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
        default=Decimal("0"),
    )

    total_charged: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    shopify_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    customer: Mapped[Customer | None] = relationship(
        back_populates="orders"
    )

    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order"
    )

    refunds: Mapped[list["Refund"]] = relationship(
        back_populates="order"
    )


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    shopify_line_item_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    shopify_product_id: Mapped[str | None] = mapped_column(
        String(100)
    )

    shopify_variant_id: Mapped[str | None] = mapped_column(
        String(100)
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    gross_product_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    product_revenue: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    order: Mapped[Order] = relationship(
        back_populates="lines"
    )


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    shopify_refund_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    product_refund_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    shipping_refund_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    tax_refund_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    fee_refund_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
        default=Decimal("0"),
    )

    unallocated_refund_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
        default=Decimal("0"),
    )

    total_refund_amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    order: Mapped[Order] = relationship(
        back_populates="refunds"
    )