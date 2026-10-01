import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from superspeciosa_analytics.data_quality import (
    get_everflow_coverage,
    get_meta_coverage,
)
from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
    MetaDailySpend,
    ThoughtMetricDailyChannel,
    ThoughtMetricDailyCoverage,
)
from superspeciosa_analytics.reporting import (
    CommercialSummary,
    get_commercial_summary,
)
from superspeciosa_analytics.reporting_presets import (
    previous_same_weekdays,
)
from superspeciosa_analytics.reporting_time import (
    reporting_date_range_to_utc,
)


ZERO = Decimal("0")
FOUR = Decimal("4")


class DailyChannelReportIncompleteError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class StoreMetrics:
    current_product_revenue: Decimal
    baseline_product_revenue: Decimal

    current_orders: Decimal
    baseline_orders: Decimal

    current_aov: Decimal
    baseline_aov: Decimal

    current_new_customers: Decimal
    baseline_new_customers: Decimal


@dataclass(frozen=True)
class ChannelMetrics:
    current_spend: Decimal
    baseline_spend: Decimal

    current_new_customers: Decimal
    baseline_new_customers: Decimal

    current_new_customer_revenue: Decimal
    baseline_new_customer_revenue: Decimal

    current_cac: Decimal | None
    baseline_cac: Decimal | None

    current_new_customer_roas: Decimal | None
    baseline_new_customer_roas: Decimal | None


@dataclass(frozen=True)
class DailyChannelReport:
    as_of: date
    current_date: date
    baseline_dates: tuple[date, ...]

    store: StoreMetrics

    meta: ChannelMetrics
    everflow: ChannelMetrics


def _keys_from_env(
    name: str,
) -> set[str]:
    return {
        value.strip()
        for value in os.getenv(
            name,
            "",
        ).split(",")
        if value.strip()
    }


def _average(
    values: list[Decimal],
) -> Decimal:
    if not values:
        return ZERO

    return (
        sum(
            values,
            ZERO,
        )
        / Decimal(
            len(values)
        )
    )


def _cac(
    spend: Decimal,
    new_customers: Decimal,
) -> Decimal | None:
    if new_customers <= ZERO:
        return None

    return (
        spend
        / new_customers
    )


def _roas(
    revenue: Decimal,
    spend: Decimal,
) -> Decimal | None:
    if spend <= ZERO:
        return None

    return (
        revenue
        / spend
    )


def _daily_commercial_summary(
    session: Session,
    report_date: date,
) -> CommercialSummary:
    end_date = (
        report_date
        + timedelta(days=1)
    )

    start_utc, end_utc = (
        reporting_date_range_to_utc(
            start=report_date,
            end=end_date,
        )
    )

    return get_commercial_summary(
        session,
        start=start_utc,
        end=end_utc,
        report_start_date=report_date,
        report_end_date=end_date,
    )


def _build_store_metrics(
    current: CommercialSummary,
    baselines: list[CommercialSummary],
) -> StoreMetrics:
    baseline_revenues = [
        summary.product_revenue
        for summary in baselines
    ]

    baseline_order_counts = [
        Decimal(
            summary.qualifying_orders
        )
        for summary in baselines
    ]

    baseline_new_customers = [
        Decimal(
            summary.new_customers
        )
        for summary in baselines
    ]

    total_baseline_revenue = sum(
        baseline_revenues,
        ZERO,
    )

    total_baseline_orders = sum(
        baseline_order_counts,
        ZERO,
    )

    if total_baseline_orders > ZERO:
        baseline_aov = (
            total_baseline_revenue
            / total_baseline_orders
        )

    else:
        baseline_aov = ZERO

    return StoreMetrics(
        current_product_revenue=(
            current.product_revenue
        ),
        baseline_product_revenue=(
            _average(
                baseline_revenues
            )
        ),

        current_orders=Decimal(
            current.qualifying_orders
        ),
        baseline_orders=_average(
            baseline_order_counts
        ),

        current_aov=(
            current.average_order_value
        ),
        baseline_aov=baseline_aov,

        current_new_customers=Decimal(
            current.new_customers
        ),
        baseline_new_customers=_average(
            baseline_new_customers
        ),
    )


def _meta_spend(
    session: Session,
    report_date: date,
) -> Decimal:
    return (
        session.scalar(
            select(
                func.sum(
                    MetaDailySpend.spend
                )
            )
            .where(
                MetaDailySpend.report_date
                == report_date
            )
        )
        or ZERO
    )


def _everflow_payout(
    session: Session,
    report_date: date,
) -> Decimal:
    return (
        session.scalar(
            select(
                func.sum(
                    EverflowDailyPerformance.payout
                )
            )
            .where(
                EverflowDailyPerformance.report_date
                == report_date
            )
        )
        or ZERO
    )


def _thoughtmetric_metric(
    session: Session,
    *,
    report_date: date,
    channel_keys: set[str],
    column,
) -> Decimal:
    if not channel_keys:
        return ZERO

    return (
        session.scalar(
            select(
                func.sum(
                    column
                )
            )
            .where(
                ThoughtMetricDailyChannel.report_date
                == report_date
            )
            .where(
                ThoughtMetricDailyChannel.channel_key.in_(
                    channel_keys
                )
            )
        )
        or ZERO
    )


def _thoughtmetric_new_customers(
    session: Session,
    *,
    report_date: date,
    channel_keys: set[str],
) -> Decimal:
    return _thoughtmetric_metric(
        session,
        report_date=report_date,
        channel_keys=channel_keys,
        column=(
            ThoughtMetricDailyChannel.new_customer_orders
        ),
    )


def _thoughtmetric_new_customer_revenue(
    session: Session,
    *,
    report_date: date,
    channel_keys: set[str],
) -> Decimal:
    return _thoughtmetric_metric(
        session,
        report_date=report_date,
        channel_keys=channel_keys,
        column=(
            ThoughtMetricDailyChannel.new_customer_sales
        ),
    )


def _thoughtmetric_covered(
    session: Session,
    report_date: date,
) -> bool:
    return bool(
        session.scalar(
            select(
                func.count(
                    ThoughtMetricDailyCoverage.id
                )
            )
            .where(
                ThoughtMetricDailyCoverage.report_date
                == report_date
            )
        )
    )


def _validate_coverage(
    session: Session,
    dates: tuple[date, ...],
) -> None:
    failures = []

    for report_date in dates:
        meta = get_meta_coverage(
            session,
            start=report_date,
            end=report_date,
        )

        if not meta.complete_daily_coverage:
            failures.append(
                f"Meta {report_date}"
            )

        everflow = get_everflow_coverage(
            session,
            start=report_date,
            end=report_date,
        )

        if not (
            everflow.complete_daily_coverage
        ):
            failures.append(
                f"Everflow {report_date}"
            )

        if not _thoughtmetric_covered(
            session,
            report_date,
        ):
            failures.append(
                f"ThoughtMetric {report_date}"
            )

    if failures:
        raise DailyChannelReportIncompleteError(
            "Incomplete source coverage: "
            + ", ".join(
                failures
            )
        )


def _build_channel_metrics(
    *,
    current_spend: Decimal,
    baseline_spends: list[Decimal],
    current_new_customers: Decimal,
    baseline_new_customers: list[Decimal],
    current_new_customer_revenue: Decimal,
    baseline_new_customer_revenues: list[
        Decimal
    ],
) -> ChannelMetrics:
    baseline_spend = _average(
        baseline_spends
    )

    baseline_customers = _average(
        baseline_new_customers
    )

    baseline_revenue = _average(
        baseline_new_customer_revenues
    )

    return ChannelMetrics(
        current_spend=current_spend,
        baseline_spend=baseline_spend,

        current_new_customers=(
            current_new_customers
        ),
        baseline_new_customers=(
            baseline_customers
        ),

        current_new_customer_revenue=(
            current_new_customer_revenue
        ),
        baseline_new_customer_revenue=(
            baseline_revenue
        ),

        current_cac=_cac(
            current_spend,
            current_new_customers,
        ),
        baseline_cac=_cac(
            baseline_spend,
            baseline_customers,
        ),

        current_new_customer_roas=_roas(
            current_new_customer_revenue,
            current_spend,
        ),
        baseline_new_customer_roas=_roas(
            baseline_revenue,
            baseline_spend,
        ),
    )


def build_daily_channel_report(
    session: Session,
    *,
    as_of: date,
) -> DailyChannelReport:
    current_date = (
        as_of
        - timedelta(days=1)
    )

    baseline_dates = (
        previous_same_weekdays(
            current_date,
            count=4,
        )
    )

    required_dates = (
        current_date,
        *baseline_dates,
    )

    _validate_coverage(
        session,
        required_dates,
    )

    current_commercial = (
        _daily_commercial_summary(
            session,
            current_date,
        )
    )

    baseline_commercial = [
        _daily_commercial_summary(
            session,
            report_date,
        )
        for report_date in baseline_dates
    ]

    store = _build_store_metrics(
        current_commercial,
        baseline_commercial,
    )

    meta_keys = _keys_from_env(
        "THOUGHTMETRIC_META_CHANNEL_KEYS"
    )

    everflow_keys = _keys_from_env(
        "THOUGHTMETRIC_EVERFLOW_CHANNEL_KEYS"
    )

    if not meta_keys:
        raise RuntimeError(
            "THOUGHTMETRIC_META_CHANNEL_KEYS "
            "is not configured."
        )

    if not everflow_keys:
        raise RuntimeError(
            "THOUGHTMETRIC_EVERFLOW_CHANNEL_KEYS "
            "is not configured."
        )

    meta = _build_channel_metrics(
        current_spend=_meta_spend(
            session,
            current_date,
        ),
        baseline_spends=[
            _meta_spend(
                session,
                report_date,
            )
            for report_date
            in baseline_dates
        ],

        current_new_customers=(
            _thoughtmetric_new_customers(
                session,
                report_date=current_date,
                channel_keys=meta_keys,
            )
        ),
        baseline_new_customers=[
            _thoughtmetric_new_customers(
                session,
                report_date=report_date,
                channel_keys=meta_keys,
            )
            for report_date
            in baseline_dates
        ],

        current_new_customer_revenue=(
            _thoughtmetric_new_customer_revenue(
                session,
                report_date=current_date,
                channel_keys=meta_keys,
            )
        ),
        baseline_new_customer_revenues=[
            _thoughtmetric_new_customer_revenue(
                session,
                report_date=report_date,
                channel_keys=meta_keys,
            )
            for report_date
            in baseline_dates
        ],
    )

    everflow = _build_channel_metrics(
        current_spend=_everflow_payout(
            session,
            current_date,
        ),
        baseline_spends=[
            _everflow_payout(
                session,
                report_date,
            )
            for report_date
            in baseline_dates
        ],

        current_new_customers=(
            _thoughtmetric_new_customers(
                session,
                report_date=current_date,
                channel_keys=everflow_keys,
            )
        ),
        baseline_new_customers=[
            _thoughtmetric_new_customers(
                session,
                report_date=report_date,
                channel_keys=everflow_keys,
            )
            for report_date
            in baseline_dates
        ],

        current_new_customer_revenue=(
            _thoughtmetric_new_customer_revenue(
                session,
                report_date=current_date,
                channel_keys=everflow_keys,
            )
        ),
        baseline_new_customer_revenues=[
            _thoughtmetric_new_customer_revenue(
                session,
                report_date=report_date,
                channel_keys=everflow_keys,
            )
            for report_date
            in baseline_dates
        ],
    )

    return DailyChannelReport(
        as_of=as_of,
        current_date=current_date,
        baseline_dates=baseline_dates,
        store=store,
        meta=meta,
        everflow=everflow,
    )