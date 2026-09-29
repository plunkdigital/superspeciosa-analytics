from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
    MetaDailyCoverage,
)


@dataclass(frozen=True)
class MetaCoverage:
    start: date
    end: date
    expected_days: int
    rows_present: int
    first_date: date | None
    last_date: date | None

    @property
    def has_any_data(self) -> bool:
        return self.rows_present > 0

    @property
    def complete_daily_coverage(self) -> bool:
        return (
            self.rows_present == self.expected_days
            and self.first_date == self.start
            and self.last_date == self.end
        )

@dataclass(frozen=True)
class EverflowCoverage:
    start: date
    end: date
    expected_days: int
    rows_present: int
    first_date: date | None
    last_date: date | None

    @property
    def has_any_data(self) -> bool:
        return self.rows_present > 0

    @property
    def complete_daily_coverage(self) -> bool:
        return (
            self.rows_present == self.expected_days
            and self.first_date == self.start
            and self.last_date == self.end
        )


def get_meta_coverage(
    session: Session,
    *,
    start: date,
    end: date,
) -> MetaCoverage:
    if start > end:
        raise ValueError(
            "Start date must not be after end date."
        )

    expected_days = (
        end - start
    ).days + 1

    row = session.execute(
        select(
            func.count(
                MetaDailyCoverage.id
            ),
            func.min(
                MetaDailyCoverage.report_date
            ),
            func.max(
                MetaDailyCoverage.report_date
            ),
        )
        .where(
            MetaDailyCoverage.report_date >= start
        )
        .where(
            MetaDailyCoverage.report_date <= end
        )
    ).one()

    return MetaCoverage(
        start=start,
        end=end,
        expected_days=expected_days,
        rows_present=int(row[0]),
        first_date=row[1],
        last_date=row[2],
    )

def get_everflow_coverage(
    session: Session,
    *,
    start: date,
    end: date,
) -> EverflowCoverage:
    if start > end:
        raise ValueError(
            "Start date must not be after end date."
        )

    expected_days = (
        end - start
    ).days + 1

    row = session.execute(
        select(
            func.count(
                EverflowDailyPerformance.id
            ),
            func.min(
                EverflowDailyPerformance.report_date
            ),
            func.max(
                EverflowDailyPerformance.report_date
            ),
        )
        .where(
            EverflowDailyPerformance.report_date
            >= start
        )
        .where(
            EverflowDailyPerformance.report_date
            <= end
        )
    ).one()

    return EverflowCoverage(
        start=start,
        end=end,
        expected_days=expected_days,
        rows_present=int(row[0]),
        first_date=row[1],
        last_date=row[2],
    )