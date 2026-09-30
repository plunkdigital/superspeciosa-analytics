from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
    ManualSpend,
    MetaDailyCoverage,
    Order,
)


@dataclass(frozen=True)
class SourceFreshness:
    shopify: datetime | None
    meta: datetime | None
    everflow: datetime | None
    manual_spend: datetime | None


def get_source_freshness(
    session: Session,
) -> SourceFreshness:
    shopify = session.scalar(
        select(
            func.max(Order.ingested_at)
        )
    )

    meta = session.scalar(
        select(
            func.max(
                MetaDailyCoverage.checked_at
            )
        )
    )

    everflow = session.scalar(
        select(
            func.max(
                EverflowDailyPerformance.ingested_at
            )
        )
    )

    manual_spend = session.scalar(
        select(
            func.max(
                ManualSpend.ingested_at
            )
        )
    )

    return SourceFreshness(
        shopify=shopify,
        meta=meta,
        everflow=everflow,
        manual_spend=manual_spend,
    )