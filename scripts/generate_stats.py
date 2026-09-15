import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

# ============================================================
# GitHub API settings
# ============================================================

TOKEN = os.environ.get("GH_TOKEN")
REPO = os.environ.get("GH_REPO")

if not TOKEN:
    raise RuntimeError("GH_TOKEN is missing")

if not REPO:
    raise RuntimeError("GH_REPO is missing")

OWNER = REPO.split("/")[0]

API_URL = "https://api.github.com/graphql"


# ============================================================
# GraphQL request
# ============================================================

def github_graphql(query):
    data = json.dumps({
        "query": query
    }).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "github-profile-generator"
        }
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    if "errors" in result:
        raise RuntimeError(result["errors"])

    return result["data"]


# ============================================================
# Date range
# ============================================================

today = datetime.now(timezone.utc).date()

from_date = today - timedelta(days=364)

from_iso = f"{from_date}T00:00:00Z"
to_iso = f"{today}T23:59:59Z"


# ============================================================
# GraphQL query
# ============================================================

query = f"""
query {{
  user(login: "{OWNER}") {{

    name
    login

    contributionsCollection(
      from: "{from_iso}"
      to: "{to_iso}"
    ) {{

      contributionCalendar {{
        totalContributions

        weeks {{
          contributionDays {{
            date
            contributionCount
          }}
        }}
      }}

    }}
  }}
}}
"""


# ============================================================
# Get GitHub data
# ============================================================

print("Fetching GitHub contribution data...")

data = github_graphql(query)

user = data["user"]

calendar = user["contributionsCollection"]["contributionCalendar"]

total_contributions = calendar["totalContributions"]

print("User:", user["login"])
print("Total contributions:", total_contributions)


# ============================================================
# Flatten daily contributions
# ============================================================

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": day["date"],
            "count": day["contributionCount"]
        })


# ============================================================
# Weekly totals
# ============================================================

weekly_totals = []

for week in calendar["weeks"]:
    total = sum(
        day["contributionCount"]
        for day in week["contributionDays"]
    )

    weekly_totals.append(total)


# ============================================================
# Current streak
# ============================================================

current_streak = 0

for day in reversed(days):

    if day["date"] > str(today):
        continue

    if day["contributionCount"] > 0:
        current_streak += 1
    else:
        break


# ============================================================
# Longest streak
# ============================================================

longest_streak = 0
running_streak = 0

for day in days:

    if day["contributionCount"] > 0:
        running_streak += 1
        longest_streak = max(
            longest_streak,
            running_streak
        )
    else:
        running_streak = 0


# ============================================================
# Save raw stats
# ============================================================

output = {
    "username": user["login"],
    "name": user["name"],
    "total_contributions": total_contributions,
    "current_streak": current_streak,
    "longest_streak": longest_streak,
    "weekly_totals": weekly_totals,
    "days": days
}

os.makedirs("assets", exist_ok=True)

with open(
    "assets/github_stats.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        output,
        file,
        indent=2
    )

print()
print("===================================")
print("GitHub stats generated successfully!")
print("===================================")
print("Saved: assets/github_stats.json")