from sqlalchemy import func, select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import MetaDailySpend


with SessionLocal() as session:
    result = session.execute(
        select(
            func.count(),
            func.min(
                MetaDailySpend.report_date
            ),
            func.max(
                MetaDailySpend.report_date
            ),
            func.sum(
                MetaDailySpend.spend
            ),
        )
    ).one()


print("META DATA COVERAGE")
print("=" * 60)

print(
    "Daily rows:",
    result[0],
)

print(
    "First date:",
    result[1],
)

print(
    "Last date:",
    result[2],
)

print(
    "Total spend:",
    result[3],
)