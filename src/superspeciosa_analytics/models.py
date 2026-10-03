from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Integer,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
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

    woo_customer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
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

    shopify_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reporting_order_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    source_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_system: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
        index=True,
    )

    source_order_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    woo_customer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
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

class ManualSpend(Base):
    __tablename__ = "manual_spend"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    record_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    vendor: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    channel: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    campaign: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    cost_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    service_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    service_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class MetaDailySpend(Base):
    __tablename__ = "meta_daily_spend"

    __table_args__ = (
        UniqueConstraint(
            "ad_account_id",
            "report_date",
            name="uq_meta_daily_spend_account_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    ad_account_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    spend: Mapped[Decimal] = mapped_column(
        MONEY,
        nullable=False,
    )

    impressions: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    clicks: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class MetaDailyCoverage(Base):
    __tablename__ = "meta_daily_coverage"

    __table_args__ = (
        UniqueConstraint(
            "ad_account_id",
            "report_date",
            name="uq_meta_daily_coverage_account_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    ad_account_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class EverflowDailyPerformance(Base):
    __tablename__ = "everflow_daily_performance"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    payout: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    revenue: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    gross_sales: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    conversions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    clicks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    source_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class ThoughtMetricDailyChannel(Base):
    __tablename__ = "thoughtmetric_daily_channel"

    __table_args__ = (
        UniqueConstraint(
            "report_date",
            "channel_key",
            name="uq_thoughtmetric_daily_channel_date_key",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    channel_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    orders: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    new_customer_orders: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    new_customer_sales: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    attributed_total_sales: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    converted_spend: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class ThoughtMetricDailyCoverage(Base):
    __tablename__ = "thoughtmetric_daily_coverage"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        unique=True,
        index=True,
    )

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class AppstleSubscriptionContract(Base):
    __tablename__ = "appstle_subscription_contract"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    contract_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    shopify_customer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    shopify_customer_gid: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_billing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    origin_shopify_order_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    origin_order_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    origin_link_method: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AppstleSubscriptionOrder(Base):
    __tablename__ = "appstle_subscription_order"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    appstle_row_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        index=True,
    )

    source_key: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
    )

    contract_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    billing_attempt_id: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
        index=True,
    )

    billing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    attempt_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    shopify_order_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    shopify_order_name: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    order_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )

    order_amount_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )

    order_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )