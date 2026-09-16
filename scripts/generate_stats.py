import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from html import escape


# ============================================================
# SETTINGS
# ============================================================

TOKEN = os.environ.get("GH_TOKEN")
REPO = os.environ.get("GH_REPO")

if not TOKEN:
    raise RuntimeError("GH_TOKEN is missing")

if not REPO:
    raise RuntimeError("GH_REPO is missing")

OWNER = REPO.split("/")[0]

API_URL = "https://api.github.com/graphql"

OUTPUT_JSON = "assets/github_stats.json"
OUTPUT_SVG = "assets/github_stats.svg"


# ============================================================
# GITHUB GRAPHQL
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
        result = json.loads(
            response.read().decode("utf-8")
        )

    if "errors" in result:
        raise RuntimeError(result["errors"])

    return result["data"]


# ============================================================
# DATE RANGE
# ============================================================

today = datetime.now(timezone.utc).date()

from_date = today - timedelta(days=364)

from_iso = f"{from_date}T00:00:00Z"
to_iso = f"{today}T23:59:59Z"


# ============================================================
# GRAPHQL QUERY
# ============================================================

query = f"""
query {{

  user(login: "{OWNER}") {{

    login
    name

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

    repositories(
      first: 100
      ownerAffiliations: OWNER
      privacy: PUBLIC
      isFork: false
    ) {{

      nodes {{

        name

        languages(
          first: 10
          orderBy: {{field: SIZE, direction: DESC}}
        ) {{

          edges {{
            size

            node {{
              name
            }}
          }}
        }}

      }}
    }}
  }}
}}
"""


# ============================================================
# FETCH DATA
# ============================================================

print("Fetching GitHub data...")

data = github_graphql(query)

user = data["user"]

calendar = (
    user["contributionsCollection"]
    ["contributionCalendar"]
)

total_contributions = calendar["totalContributions"]


# ============================================================
# DAILY CONTRIBUTIONS
# ============================================================

days = []

for week in calendar["weeks"]:

    for day in week["contributionDays"]:

        days.append({
            "date": day["date"],
            "count": day["contributionCount"]
        })


days.sort(key=lambda x: x["date"])


# ============================================================
# WEEKLY TOTALS
# ============================================================

weekly_totals = []

for week in calendar["weeks"]:

    total = sum(
        day["contributionCount"]
        for day in week["contributionDays"]
    )

    weekly_totals.append(total)


# ============================================================
# CURRENT STREAK
# ============================================================

current_streak = 0

for day in reversed(days):

    if day["date"] == str(today) and day["count"] == 0:
        continue

    if day["count"] > 0:
        current_streak += 1
    else:
        break


# ============================================================
# LONGEST STREAK
# ============================================================

longest_streak = 0
running_streak = 0

for day in days:

    if day["count"] > 0:

        running_streak += 1

        longest_streak = max(
            longest_streak,
            running_streak
        )

    else:
        running_streak = 0


# ============================================================
# TOP LANGUAGES
# ============================================================

language_bytes = {}

for repository in user["repositories"]["nodes"]:

    for edge in repository["languages"]["edges"]:

        language = edge["node"]["name"]
        size = edge["size"]

        language_bytes[language] = (
            language_bytes.get(language, 0)
            + size
        )


top_languages = sorted(
    language_bytes.items(),
    key=lambda item: item[1],
    reverse=True
)[:6]


# ============================================================
# SAVE JSON
# ============================================================

stats = {
    "username": user["login"],
    "name": user["name"],
    "total_contributions": total_contributions,
    "current_streak": current_streak,
    "longest_streak": longest_streak,
    "weekly_totals": weekly_totals,
    "top_languages": [
        {
            "name": name,
            "bytes": size
        }
        for name, size in top_languages
    ],
    "days": days
}

os.makedirs("assets", exist_ok=True)

with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        stats,
        file,
        indent=2
    )


# ============================================================
# SVG HELPERS
# ============================================================

def esc(value):
    return escape(str(value))


def svg_text(
    x,
    y,
    text,
    size=16,
    weight="400"
):

    return (
        f'<text x="{x}" y="{y}" '
        f'font-size="{size}px" '
        f'font-weight="{weight}" '
        f'font-family="monospace" fill="#e6edf3">'
        f'{esc(text)}'
        f'</text>'
    )


# ============================================================
# SVG CANVAS
# ============================================================

width = 900
height = 500

svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">'
)

svg.append(

)


# ============================================================
# HEADER
# ============================================================

svg.append(
    svg_text(
        35,
        45,
        "GITHUB ACTIVITY",
        18,
        "700"
    )
)

svg.append(
    svg_text(
        35,
        72,
        f"{total_contributions:,} contributions",
        30,
        "700"
    )
)


# ============================================================
# WEEKLY GRAPH
# ============================================================

graph_x = 35
graph_y = 105
graph_width = 830
graph_height = 125

maximum = max(weekly_totals) if weekly_totals else 1

points = []

for i, value in enumerate(weekly_totals):

    x = (
        graph_x
        + (i / max(len(weekly_totals) - 1, 1))
        * graph_width
    )

    y = (
        graph_y
        + graph_height
        - (value / maximum) * graph_height
    )

    points.append(
        f"{x:.2f},{y:.2f}"
    )


svg.append(
    '<polyline '
    f'points="{" ".join(points)}" '
    'fill="none" '
    'stroke="#00e5ff" '
    'stroke-width="2"/>'
)


# ============================================================
# STREAKS
# ============================================================

svg.append(
    svg_text(
        35,
        275,
        "CURRENT STREAK",
        13,
        "700"
    )
)

svg.append(
    svg_text(
        35,
        305,
        f"{current_streak} days",
        25,
        "700"
    )
)

svg.append(
    svg_text(
        300,
        275,
        "LONGEST STREAK",
        13,
        "700"
    )
)

svg.append(
    svg_text(
        300,
        305,
        f"{longest_streak} days",
        25,
        "700"
    )
)


# ============================================================
# TOP LANGUAGES
# ============================================================

svg.append(
    svg_text(
        35,
        355,
        "TOP LANGUAGES",
        13,
        "700"
    )
)

if top_languages:

    total_language_bytes = sum(
        size
        for _, size in top_languages
    )

    language_x = 35

    for name, size in top_languages:

        percentage = (
            size / total_language_bytes * 100
        )

        label = (
            f"{name}  "
            f"{percentage:.1f}%"
        )

        svg.append(
            svg_text(
                language_x,
                390,
                label,
                14
            )
        )

        language_x += 135


# ============================================================
# YEAR ACTIVITY
# ============================================================

svg.append(
    svg_text(
        35,
        435,
        "YEAR",
        13,
        "700"
    )
)

ramp = " .:-=+*#%@"

year_x = 95
year_y = 430

for day in days:

    count = day["count"]

    if count == 0:
        char = " "

    else:

        # Cap the value so very large days
        # don't dominate the visualization.
        level = min(count, 12)

        index = int(
            level / 12
            * (len(ramp) - 1)
        )

        char = ramp[index]

    svg.append(
        svg_text(
            year_x,
            year_y,
            char,
            10
        )
    )

    year_x += 8

    if year_x > 850:
        break


# ============================================================
# CLOSE SVG
# ============================================================

svg.append("</svg>")


# ============================================================
# SAVE SVG
# ============================================================

with open(
    OUTPUT_SVG,
    "w",
    encoding="utf-8"
) as file:

    file.write("\n".join(svg))


# ============================================================
# DONE
# ============================================================

print()
print("===================================")
print("GitHub stats generated!")
print("===================================")
print("User:", user["login"])
print("Total contributions:", total_contributions)
print("Current streak:", current_streak)
print("Longest streak:", longest_streak)
print("Top languages:", len(top_languages))
print()
print("Created:")
print("-", OUTPUT_JSON)
print("-", OUTPUT_SVG)