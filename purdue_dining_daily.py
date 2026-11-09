#!/usr/bin/env python3
"""Purdue daily nutrition exporter for macOS.
how to run 
python3 -m pip install requests
cd ~/Downloads
python3 purdue_dining_daily.py --install

Install registers a per-user macOS LaunchAgent for 8:00 AM local time.
The Mac needs to be powered on (a sleeping Mac may run the job upon waking).
"""

import argparse
import csv
import os
import plistlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

API = "https://api.hfs.purdue.edu/menus/v3/GraphQL"
TZ = ZoneInfo("America/Indiana/Indianapolis")
DINING_HALLS = ["Wiley"]  # Add: "Ford", "Earhart", "Windsor", "Hillenbrand"
OUTPUT_DIR = Path.home() / "Documents" / "PurdueDiningNutrition"
LABEL = "com.purdue.dining.nutrition.daily"
AGENT = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"

QUERY = """
query DailyMenu($name: String!, $date: Date!) {
  diningCourtByName(name: $name) {
    dailyMenu(date: $date) {
      meals {
        name
        stations {
          name
          items {
            displayName
            item {
              name
              ingredients
              isNutritionReady
              nutritionFacts { name value label }
            }
          }
        }
      }
    }
  }
}
"""

COLUMNS = [
    "Date", "Dining Hall", "Meal", "Station", "Food", "Serving Size",
    "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)",
    "Fiber (g)", "Sodium (mg)", "Ingredients", "Nutrition Available",
]


def nutrient(facts, *names, serving=False):
    """Return Purdue's published value, never an estimated number."""
    wanted = {n.casefold().strip() for n in names}
    for fact in facts:
        if (fact.get("name") or "").casefold().strip() in wanted:
            if serving:
                return fact.get("label") or fact.get("value") or ""
            value = fact.get("value")
            return value if value is not None else ""
    return ""


def fetch_menu(session, hall, date):
    response = session.post(
        API,
        json={"query": QUERY, "variables": {"name": hall, "date": date}},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("errors"):
        raise RuntimeError(str(result["errors"]))
    court = (result.get("data") or {}).get("diningCourtByName")
    if not court:
        raise RuntimeError(f"No dining court returned for {hall}")
    return court.get("dailyMenu")


def menu_rows(menu, hall, date):
    rows = []
    for meal in (menu or {}).get("meals") or []:
        for station in meal.get("stations") or []:
            for entry in station.get("items") or []:
                food = entry.get("item")
                if not food:
                    continue
                ready = food.get("isNutritionReady") is True
                facts = (food.get("nutritionFacts") or []) if ready else []
                rows.append({
                    "Date": date,
                    "Dining Hall": hall,
                    "Meal": meal.get("name") or "",
                    "Station": station.get("name") or "",
                    "Food": entry.get("displayName") or food.get("name") or "",
                    "Serving Size": nutrient(facts, "Serving Size", "ServingSize", serving=True),
                    "Calories (kcal)": nutrient(facts, "Calories"),
                    "Protein (g)": nutrient(facts, "Protein"),
                    "Carbs (g)": nutrient(facts, "Total Carbohydrate", "Carbohydrates", "Carbohydrate"),
                    "Fat (g)": nutrient(facts, "Total Fat", "Fat"),
                    "Fiber (g)": nutrient(facts, "Dietary Fiber", "Fiber"),
                    "Sodium (mg)": nutrient(facts, "Sodium"),
                    "Ingredients": food.get("ingredients") or "",
                    "Nutrition Available": "Yes" if ready else "No",
                })
    return rows


def export_today():
    date = datetime.now(TZ).strftime("%Y-%m-%d")
    rows = []
    errors = []
    with requests.Session() as session:
        for hall in DINING_HALLS:
            try:
                new_rows = menu_rows(fetch_menu(session, hall, date), hall, date)
                rows.extend(new_rows)
                print(f"{hall}: {len(new_rows)} foods", flush=True)
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                errors.append(f"{hall}: {exc}")
                print(f"ERROR: {hall}: {exc}", file=sys.stderr, flush=True)
    if not rows:
        raise RuntimeError("No published food items were received. CSV not created.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"purdue_dining_{date}.csv"
    with filename.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} foods to {filename}", flush=True)
    if errors:
        print("Some dining halls failed; see errors above.", file=sys.stderr)


def launchctl(*args):
    return subprocess.run(["launchctl", *args], text=True, capture_output=True)


def install():
    if sys.platform != "darwin":
        raise RuntimeError("Automatic LaunchAgent installation is for macOS only.")
    script = Path(__file__).resolve()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AGENT.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "Label": LABEL,
        "ProgramArguments": [sys.executable, str(script), "--once"],
        "StartCalendarInterval": {"Hour": 8, "Minute": 0},
        "RunAtLoad": True,
        "StandardOutPath": str(OUTPUT_DIR / "daily.log"),
        "StandardErrorPath": str(OUTPUT_DIR / "errors.log"),
    }
    # Unload previous version if already installed.
    if AGENT.exists():
        launchctl("bootout", f"gui/{os.getuid()}", str(AGENT))
    with AGENT.open("wb") as f:
        plistlib.dump(config, f)
    result = launchctl("bootstrap", f"gui/{os.getuid()}", str(AGENT))
    if result.returncode:
        raise RuntimeError("Could not install daily job: " + result.stderr.strip())
    print(f"Installed daily 8:00 AM job. Files will be in {OUTPUT_DIR}")
    print("It also runs once on installation. Check daily.log for results.")


def uninstall():
    if sys.platform != "darwin":
        raise RuntimeError("LaunchAgent removal is for macOS only.")
    if AGENT.exists():
        launchctl("bootout", f"gui/{os.getuid()}", str(AGENT))
        AGENT.unlink()
        print("Daily scheduled task removed. Existing CSVs were kept.")
    else:
        print("No scheduled task installed.")


def main():
    parser = argparse.ArgumentParser(description="Export Purdue dining nutrition daily")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Download today's CSV now")
    group.add_argument("--install", action="store_true", help="Schedule daily on macOS at 8:00 AM")
    group.add_argument("--uninstall", action="store_true", help="Remove daily macOS schedule")
    args = parser.parse_args()
    try:
        if args.install:
            install()
        elif args.uninstall:
            uninstall()
        else:
            export_today()
    except (RuntimeError, OSError, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
