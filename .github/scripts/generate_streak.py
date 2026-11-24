import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = os.environ.get("GITHUB_USERNAME", "BhuvanExpo")
TOKEN = os.environ["GITHUB_TOKEN"]
OUTPUT_PATH = "output/streak.svg"


def fetch_contributions(username: str, token: str) -> list[dict]:
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Streak-Fireball-Generator",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for week in weeks:
        days.extend(week["contributionDays"])
    return sorted(days, key=lambda d: d["date"])


def calculate_streaks(days: list[dict]) -> tuple[int, int, int]:
    total = sum(d["contributionCount"] for d in days)
    longest = 0
    running = 0
    for d in days:
        if d["contributionCount"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    # Calculate current streak up to today (IST / UTC+5:30)
    ist = timezone(timedelta(hours=5, minutes=30))
    today_str = datetime.now(ist).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now(ist) - timedelta(days=1)).strftime("%Y-%m-%d")

    day_map = {d["date"]: d["contributionCount"] for d in days}

    current = 0
    if day_map.get(today_str, 0) > 0:
        check_date = datetime.now(ist)
    elif day_map.get(yesterday_str, 0) > 0:
        check_date = datetime.now(ist) - timedelta(days=1)
    else:
        return 0, longest, total

    while True:
        ds = check_date.strftime("%Y-%m-%d")
        if day_map.get(ds, 0) > 0:
            current += 1
            check_date -= timedelta(days=1)
        else:
            break

    return current, longest, total


def build_active_fireball_svg(current: int, longest: int, total: int) -> str:
    # Scale flame intensity slightly with streak length
    scale = min(1.25, 1.0 + (current * 0.015))
    return f"""<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="495" y2="195" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0B132B"/>
      <stop offset="100%" stop-color="#1C2541"/>
    </linearGradient>
    <radialGradient id="fireGlow" cx="50%" cy="55%" r="50%">
      <stop offset="0%" stop-color="#FF6D00" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#FF6D00" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="outerFlame" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FF9100"/>
      <stop offset="100%" stop-color="#DD2C00"/>
    </linearGradient>
    <linearGradient id="innerFlame" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFF59D"/>
      <stop offset="100%" stop-color="#FFAB00"/>
    </linearGradient>
  </defs>

  <!-- Card Background -->
  <rect width="495" height="195" rx="12" fill="url(#bgGrad)"/>

  <!-- Ambient Fire Glow -->
  <circle cx="247" cy="92" r="78" fill="url(#fireGlow)">
    <animate attributeName="r" values="72;84;72" dur="1.8s" repeatCount="indefinite"/>
  </circle>

  <!-- Left Stat: Total Contributions -->
  <text x="82" y="88" fill="#E0E6ED" font-family="Segoe UI, Ubuntu, sans-serif" font-size="26" font-weight="700" text-anchor="middle">{total}</text>
  <text x="82" y="112" fill="#8DA9C4" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" font-weight="600" text-anchor="middle">TOTAL COMMITS</text>
  <text x="82" y="130" fill="#5C7AEA" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" text-anchor="middle">Past 12 Months</text>

  <!-- Dividers -->
  <line x1="165" y1="35" x2="165" y2="160" stroke="#2B3A67" stroke-width="1.5"/>
  <line x1="330" y1="35" x2="330" y2="160" stroke="#2B3A67" stroke-width="1.5"/>

  <!-- Center: Animated Fireball -->
  <g transform="translate(247, 72) scale({scale:.2f})">
    <!-- Pulsing Ring -->
    <circle cx="0" cy="0" r="46" stroke="#FF6D00" stroke-width="3" fill="none" opacity="0.85">
      <animate attributeName="stroke-width" values="2.5;4.5;2.5" dur="1.5s" repeatCount="indefinite"/>
    </circle>

    <!-- Outer Animated Flame -->
    <path d="M0 -42 C18 -20, 32 -4, 24 20 C19 34, 8 40, 0 40 C-8 40, -19 34, -24 20 C-32 -4, -18 -20, 0 -42 Z" fill="url(#outerFlame)">
      <animateTransform attributeName="transform" type="scale" values="1 1; 1.06 0.95; 0.96 1.07; 1 1" dur="1.1s" repeatCount="indefinite"/>
    </path>

    <!-- Inner Core Flame -->
    <path d="M0 -22 C10 -8, 16 4, 12 18 C9 26, 4 30, 0 30 C-4 30, -9 26, -12 18 C-16 4, -10 -8, 0 -22 Z" fill="url(#innerFlame)">
      <animateTransform attributeName="transform" type="scale" values="1 1; 0.92 1.08; 1.05 0.94; 1 1" dur="0.85s" repeatCount="indefinite"/>
    </path>

    <!-- Floating Embers -->
    <circle cx="-14" cy="-10" r="2.2" fill="#FFD54F">
      <animate attributeName="cy" values="-10;-48" dur="1.6s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;0" dur="1.6s" repeatCount="indefinite"/>
    </circle>
    <circle cx="15" cy="-5" r="1.8" fill="#FF9100">
      <animate attributeName="cy" values="-5;-45" dur="1.3s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;0" dur="1.3s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- Current Streak Count -->
  <text x="247" y="142" fill="#FFD54F" font-family="Segoe UI, Ubuntu, sans-serif" font-size="24" font-weight="800" text-anchor="middle">{current} DAYS</text>
  <text x="247" y="162" fill="#FF9100" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" font-weight="700" text-anchor="middle">🔥 STREAK ON FIRE</text>

  <!-- Right Stat: Longest Streak -->
  <text x="412" y="88" fill="#E0E6ED" font-family="Segoe UI, Ubuntu, sans-serif" font-size="26" font-weight="700" text-anchor="middle">{longest}</text>
  <text x="412" y="112" fill="#8DA9C4" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" font-weight="600" text-anchor="middle">LONGEST STREAK</text>
  <text x="412" y="130" fill="#5C7AEA" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" text-anchor="middle">Personal Best</text>
</svg>"""


def build_cold_spark_svg(longest: int, total: int) -> str:
    return f"""<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgCold" x1="0" y1="0" x2="495" y2="195" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0B132B"/>
      <stop offset="100%" stop-color="#16213E"/>
    </linearGradient>
    <radialGradient id="sparkGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00E5FF" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#00E5FF" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="495" height="195" rx="12" fill="url(#bgCold)"/>

  <!-- Left Stat -->
  <text x="82" y="88" fill="#B0BEC5" font-family="Segoe UI, Ubuntu, sans-serif" font-size="26" font-weight="700" text-anchor="middle">{total}</text>
  <text x="82" y="112" fill="#78909C" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" font-weight="600" text-anchor="middle">TOTAL COMMITS</text>

  <line x1="165" y1="35" x2="165" y2="160" stroke="#233554" stroke-width="1.5"/>
  <line x1="330" y1="35" x2="330" y2="160" stroke="#233554" stroke-width="1.5"/>

  <!-- Center: Pulsing Re-ignite Spark -->
  <circle cx="247" cy="72" r="55" fill="url(#sparkGlow)">
    <animate attributeName="r" values="40;62;40" dur="2.2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="247" cy="72" r="38" stroke="#37474F" stroke-width="2.5" stroke-dasharray="6 6" fill="none">
    <animateTransform attributeName="transform" type="rotate" from="0 247 72" to="360 247 72" dur="12s" repeatCount="indefinite"/>
  </circle>

  <!-- Dimmed Flame Outline + Spark Core -->
  <path d="M247 44 C258 58, 266 68, 261 84 C258 93, 252 97, 247 97 C242 97, 236 93, 233 84 C228 68, 236 58, 247 44 Z" fill="#263238" stroke="#546E7A" stroke-width="1.5"/>
  <circle cx="247" cy="82" r="5" fill="#00E5FF">
    <animate attributeName="r" values="4;7;4" dur="1.4s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.4;1;0.4" dur="1.4s" repeatCount="indefinite"/>
  </circle>

  <text x="247" y="136" fill="#ECEFF1" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="800" text-anchor="middle">0 DAYS STREAK</text>
  <text x="247" y="156" fill="#00E5FF" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11.5" font-weight="600" text-anchor="middle">⚡ Push a commit to ignite!</text>

  <!-- Right Stat -->
  <text x="412" y="88" fill="#B0BEC5" font-family="Segoe UI, Ubuntu, sans-serif" font-size="26" font-weight="700" text-anchor="middle">{longest}</text>
  <text x="412" y="112" fill="#78909C" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" font-weight="600" text-anchor="middle">LONGEST STREAK</text>
  <text x="412" y="130" fill="#546E7A" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" text-anchor="middle">Beat your record!</text>
</svg>"""


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    days = fetch_contributions(USERNAME, TOKEN)
    current, longest, total = calculate_streaks(days)

    if current > 0:
        svg = build_active_fireball_svg(current, longest, total)
    else:
        svg = build_cold_spark_svg(longest, total)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Generated {OUTPUT_PATH}: current={current}, longest={longest}, total={total}")


if __name__ == "__main__":
    main()
