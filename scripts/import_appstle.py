import argparse

from superspeciosa_analytics.appstle_ingest import (
    import_appstle,
)
from superspeciosa_analytics.database import (
    SessionLocal,
)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--shopify-batch-size",
        type=int,
        default=50,
    )

    args = parser.parse_args()

    with SessionLocal() as session:
        stats = import_appstle(
            session,
            limit=args.limit,
            shopify_batch_size=(
                args.shopify_batch_size
            ),
        )

        session.commit()

    print()
    print("APPSTLE IMPORT")
    print("=" * 72)

    for key, value in stats.items():
        print(
            f"{key}: {value}"
        )


if __name__ == "__main__":
    main()