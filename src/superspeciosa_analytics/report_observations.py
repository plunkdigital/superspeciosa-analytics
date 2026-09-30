from decimal import Decimal

from superspeciosa_analytics.reporting_compare import (
    CommercialComparison,
)


ZERO = Decimal("0")


def _percent(
    value: Decimal | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:+.1f}%"


def _direction(
    value: Decimal | None,
) -> str:
    if value is None:
        return "unchanged"

    if value > ZERO:
        return "up"

    if value < ZERO:
        return "down"

    return "flat"


def build_observations(
    *,
    yesterday: CommercialComparison,
    last_7: CommercialComparison,
    month_to_date: CommercialComparison,
    yesterday_marketing_complete: bool,
    last_7_marketing_complete: bool,
    mtd_marketing_complete: bool,
) -> list[str]:
    observations = []

    #
    # Yesterday
    #

    revenue_change = (
        yesterday.product_revenue.percentage_change
    )

    order_change = (
        yesterday.qualifying_orders.percentage_change
    )

    aov_change = (
        yesterday.average_order_value.percentage_change
    )

    observations.append(
        (
            "Yesterday revenue was "
            f"{_direction(revenue_change)} "
            f"{_percent(revenue_change)}; "
            f"orders were {_percent(order_change)} "
            f"and AOV was {_percent(aov_change)}."
        )
    )

    #
    # Trailing seven days
    #

    observations.append(
        (
            "Over the last 7 days, revenue was "
            f"{_percent(last_7.product_revenue.percentage_change)} "
            f"versus the prior 7 days, while new customers were "
            f"{_percent(last_7.new_customers.percentage_change)}."
        )
    )

    #
    # Month to date
    #

    if mtd_marketing_complete:
        observations.append(
            (
                "Month to date, marketing spend was "
                f"{_percent(month_to_date.total_marketing_spend.percentage_change)} "
                f"versus the equivalent prior-month period, "
                f"with blended efficiency at "
                f"{month_to_date.current.blended_marketing_efficiency:.2f}x."
            )
        )

    else:
        observations.append(
            (
                "Month-to-date marketing metrics are "
                "not interpreted because source coverage "
                "is incomplete."
            )
        )

    return observations