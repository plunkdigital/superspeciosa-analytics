from superspeciosa_analytics.shopify import graphql


QUERY = """
query {
  shop {
    name
    myshopifyDomain
    currencyCode
  }

  currentAppInstallation {
    accessScopes {
      handle
    }
  }
}
"""


data = graphql(QUERY)

print("Shop:")
print(data["shop"])

print()
print("Granted scopes:")

for scope in sorted(
    item["handle"]
    for item in data["currentAppInstallation"]["accessScopes"]
):
    print(f"- {scope}")