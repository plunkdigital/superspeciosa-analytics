from superspeciosa_analytics.meta import (
    MetaConfigurationError,
    ad_account_path,
    get,
)


try:
    data = get(
        ad_account_path(),
        params={
            "fields": (
                "id,"
                "name,"
                "account_status,"
                "currency,"
                "timezone_name"
            )
        },
    )

except MetaConfigurationError as error:
    raise SystemExit(
        f"Meta is not configured yet: {error}"
    )


print("META AD ACCOUNT")
print("=" * 60)

print(
    "ID:",
    data.get("id"),
)

print(
    "Name:",
    data.get("name"),
)

print(
    "Status:",
    data.get("account_status"),
)

print(
    "Currency:",
    data.get("currency"),
)

print(
    "Timezone:",
    data.get("timezone_name"),
)