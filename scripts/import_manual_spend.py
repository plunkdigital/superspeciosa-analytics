import argparse
import csv
from pathlib import Path

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.manual_spend import (
    parse_manual_spend_row,
)
from superspeciosa_analytics.manual_spend_ingest import (
    upsert_manual_spend,
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "file",
    type=Path,
)

args = parser.parse_args()


with args.file.open(
    newline="",
    encoding="utf-8",
) as file:
    reader = csv.DictReader(file)

    records = [
        parse_manual_spend_row(row)
        for row in reader
    ]


with SessionLocal() as session:
    created = upsert_manual_spend(
        session,
        records,
    )

    session.commit()


print(
    f"Imported {len(records)} records "
    f"({created} new)."
)