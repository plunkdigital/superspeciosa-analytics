from superspeciosa_analytics.appstle import (
    get,
)


response = get(
    "/activity-logs",
    params={
        "page": 0,
        "size": 5,
        "sort": "createAt,desc",
    },
)


data = response.json()


print()
print("APPSTLE CONNECTION CHECK")
print("=" * 72)

print(
    "Status:",
    response.status_code,
)

print(
    "Recent activity rows:",
    len(data),
)

print()


for row in data:
    print("-" * 72)

    print(
        "Date:",
        row.get("createAt"),
    )

    print(
        "Entity:",
        row.get("entityType"),
    )

    print(
        "Event:",
        row.get("eventType"),
    )

    print(
        "Status:",
        row.get("status"),
    )

    print(
        "Entity ID:",
        row.get("entityId"),
    )


print()
print(
    "Appstle connection check passed."
)