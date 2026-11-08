#!/usr/bin/env python3
"""
generate_meal_plan.py

Automated weekly meal planner for Mealie powered by Google Gemini.
Selects dinner recipes matching weekly goals, seasonality, and untried/least-recently made preferences.
Supports note entries for schedule obligations and customizable planning windows.

Usage:
    uv run --with google-genai --with requests --with pydantic generate_meal_plan.py [options]

Options:
    --start-date YYYY-MM-DD  Start date of planning window (defaults to today/Sunday)
    --days INT               Number of days to plan (default: 7)
    --goals TEXT             Weekly goals (e.g. "high protein, seasonal fall recipes")
    --skip TEXT              Days to exclude with notes (e.g. "Wednesday: Dinner with team")
    --confirm, -y            Automatically write to Mealie without interactive confirmation
    --dry-run                Simulate plan generation without modifying Mealie
    --log-file PATH          Optional path to append execution log
"""

import argparse
import datetime
import json
import os
import sys
from typing import Any

import requests
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# --------------------------------------------------------------------------
# Date & Planning Window Helpers
# --------------------------------------------------------------------------

DAY_NAMES = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "tues": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}


def calculate_planning_window(start_date: datetime.date, days: int = 7) -> list[datetime.date]:
    """Returns a list of consecutive datetime.date objects for the planning window."""
    if days < 1:
        raise ValueError("Days must be at least 1.")
    return [start_date + datetime.timedelta(days=i) for i in range(days)]


def parse_date_or_day_name(val: str, window: list[datetime.date]) -> datetime.date:
    """
    Parses a string representing either an ISO date (YYYY-MM-DD) or a day name (e.g., 'Wed', 'Wednesday')
    and resolves it to a date within the given planning window.
    """
    cleaned = val.strip().lower()

    # Try ISO date first
    try:
        dt = datetime.date.fromisoformat(cleaned)
        if dt in window:
            return dt
        raise ValueError(f"Date {dt} is not within the planning window ({window[0]} to {window[-1]}).")
    except ValueError as e:
        if "planning window" in str(e):
            raise

    # Try day name
    if cleaned in DAY_NAMES:
        target_weekday = DAY_NAMES[cleaned]
        for dt in window:
            if dt.weekday() == target_weekday:
                return dt
        raise ValueError(f"Day '{val}' does not fall within the planning window ({window[0]} to {window[-1]}).")

    raise ValueError(f"Could not parse '{val}' as an ISO date or day name within the window.")


def parse_skip_spec(skip_str: str, window: list[datetime.date]) -> tuple[datetime.date, str]:
    """
    Parses a skip argument string like:
    - 'Wednesday: Dinner with team'
    - 'Friday'
    - '2026-11-11: Work obligation'
    Returns (date_obj, note_text).
    """
    parts = skip_str.split(":", 1)
    date_val = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "Obligation (Not cooking)"

    resolved_date = parse_date_or_day_name(date_val, window)
    return resolved_date, reason


def get_season_context(dt: datetime.date) -> tuple[str, str]:
    """Returns season name and culinary theme guidance based on month."""
    month = dt.month
    if month in (12, 1, 2):
        return (
            "Winter",
            "Focus on hearty warm dishes, slow-cooked stews, root vegetables, casseroles, and rich comfort soups.",
        )
    elif month in (3, 4, 5):
        return (
            "Spring",
            "Focus on fresh seasonal greens, tender asparagus, peas, herbs, bright citrus notes, and lighter dishes.",
        )
    elif month in (6, 7, 8):
        return (
            "Summer",
            "Focus on grilled mains, crisp salads, vibrant summer vegetables (tomatoes, zucchini, corn), and lighter fare.",
        )
    else:
        return (
            "Fall",
            "Focus on seasonal squashes, roasted root vegetables, apples, hearty chili, warm curries, and comforting fall flavors.",
        )


def build_mealplan_entry(
    date_str: str,
    recipe_id: str | None = None,
    note_title: str | None = None,
    note_text: str | None = None,
) -> dict[str, Any]:
    """Builds Mealie CreatePlanEntry payload for a dinner slot."""
    return {
        "date": date_str,
        "entryType": "dinner",
        "recipeId": recipe_id,
        "title": note_title or "",
        "text": note_text or "",
    }


# --------------------------------------------------------------------------
# Mealie API Client
# --------------------------------------------------------------------------


class MealieClient:
    def __init__(self, base_url: str, api_token: str, session: requests.Session | None = None, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.session = session or requests.Session()
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def get_all_recipes(self) -> list[dict[str, Any]]:
        """Fetches all recipes from Mealie using pagination."""
        recipes = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.base_url}/api/recipes"
            params = {"page": page, "perPage": per_page}
            resp = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            if not items:
                break
            recipes.extend(items)

            total_pages = data.get("total_pages", data.get("totalPages", 1))
            if page >= total_pages or len(items) < per_page:
                break
            page += 1

        return recipes

    def get_recent_mealplans(self, limit: int = 150) -> list[dict[str, Any]]:
        """Queries recent meal plan entries from Mealie to determine recipe recency."""
        url = f"{self.base_url}/api/households/mealplans"
        params = {"perPage": limit, "orderBy": "date", "orderDirection": "desc"}
        resp = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])

    def get_existing_mealplans(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Queries existing meal plan entries within date range."""
        url = f"{self.base_url}/api/households/mealplans"
        params = {"start_date": start_date, "end_date": end_date}
        resp = self.session.get(url, headers=self.headers, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])

    def create_mealplan_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Posts a new meal plan entry."""
        url = f"{self.base_url}/api/households/mealplans"
        resp = self.session.post(url, headers=self.headers, json=entry, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()


# --------------------------------------------------------------------------
# Gemini Structured Plan Generator
# --------------------------------------------------------------------------


class PlannedMeal(BaseModel):
    date: str = Field(description="ISO date YYYY-MM-DD for this meal")
    recipe_id: str = Field(description="Exact UUID of the chosen recipe from catalog")
    recipe_name: str = Field(description="Exact title of the chosen recipe")
    rationale: str = Field(description="Brief reason for selecting this meal based on goals, season, and variety")


class PlanResponse(BaseModel):
    selected_meals: list[PlannedMeal] = Field(description="List of planned meals for cook days")
    summary_of_week: str = Field(description="Brief weekly theme and nutritional overview")


def get_recipe_last_made_map(mealplan_items: list[dict[str, Any]]) -> dict[str, str]:
    """Returns a dict mapping recipe_id -> most recent date (YYYY-MM-DD) it was planned/made."""
    last_made: dict[str, str] = {}
    for entry in mealplan_items:
        rid = entry.get("recipeId")
        dt = entry.get("date")
        if rid and dt and rid not in last_made:
            last_made[rid] = dt
    return last_made


def format_recipe_time(r: dict[str, Any]) -> str | None:
    """Formats recipe duration from string description or totalTimeSeconds."""
    if r.get("totalTime"):
        return str(r["totalTime"]).strip()
    secs = r.get("totalTimeSeconds")
    if not secs:
        prep = r.get("prepTimeSeconds") or 0
        perf = r.get("performTimeSeconds") or 0
        if prep + perf > 0:
            secs = prep + perf
    if secs and secs > 0:
        hrs = secs // 3600
        mins = (secs % 3600) // 60
        if hrs > 0 and mins > 0:
            return f"{hrs} hr {mins} min"
        elif hrs > 0:
            return f"{hrs} hr"
        elif mins > 0:
            return f"{mins} min"
        else:
            return f"{secs} sec"
    return None


NON_DINNER_CATEGORIES = {"dessert", "cocktails", "drinks", "homemade essentials", "snack"}


def is_dinner_eligible(recipe: dict[str, Any], goals: str = "") -> bool:
    """Checks if a recipe is eligible as a dinner dish unless user goals request dessert/snack/etc."""
    goals_lower = goals.lower()
    categories = [
        (c.get("name") if isinstance(c, dict) else str(c)).lower() for c in (recipe.get("recipeCategory") or [])
    ]
    for cat in categories:
        if cat in NON_DINNER_CATEGORIES:
            if cat not in goals_lower:
                return False
    return True


def validate_gemini_selection(
    selections: list[dict[str, Any]], catalog: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validates that Gemini returned recipe IDs that actually exist in catalog."""
    valid = []
    invalid = []
    for item in selections:
        rid = item.get("recipe_id")
        if rid in catalog:
            valid.append(item)
        else:
            invalid.append(item)
    return valid, invalid


def generate_plan_with_gemini(
    api_key: str,
    recipe_catalog: list[dict[str, Any]],
    cook_dates: list[datetime.date],
    goals: str,
    skip_map: dict[str, str],
    last_made_map: dict[str, str] | None = None,
) -> PlanResponse:
    """Calls Gemini API using structured JSON output to assign recipes to cook dates."""
    if not genai:
        raise RuntimeError("google-genai package is not installed. Run with 'uv run --with google-genai'.")

    client = genai.Client(api_key=api_key)
    last_made_map = last_made_map or {}

    # Prepare compact catalog representation to fit token budgets efficiently
    compact_catalog = []
    for r in recipe_catalog:
        if not is_dinner_eligible(r, goals):
            continue

        rid = r.get("id")
        last_made = last_made_map.get(rid) or r.get("lastMade")
        formatted_time = format_recipe_time(r)

        compact_catalog.append(
            {
                "id": rid,
                "name": r.get("name"),
                "tags": [t.get("name") if isinstance(t, dict) else str(t) for t in (r.get("tags") or [])],
                "categories": [
                    c.get("name") if isinstance(c, dict) else str(c) for c in (r.get("recipeCategory") or [])
                ],
                "rating": r.get("rating"),
                "total_time": formatted_time,
                "last_made": last_made,
                "date_added": r.get("dateAdded"),
                "description": (r.get("description") or "")[:150],
            }
        )

    first_date = cook_dates[0] if cook_dates else datetime.date.today()
    season, season_notes = get_season_context(first_date)

    prompt_data = {
        "season": season,
        "season_notes": season_notes,
        "user_goals": goals,
        "dates_needing_dinners": [{"date": d.isoformat(), "day_of_week": d.strftime("%A")} for d in cook_dates],
        "excluded_dates_with_notes": {d: reason for d, reason in skip_map.items()},
        "available_recipe_catalog_count": len(compact_catalog),
        "recipe_catalog": compact_catalog,
    }

    system_instruction = (
        "You are an expert culinary meal planner. Your job is to select the perfect dinner recipes for a home cook.\n"
        "Strict Requirements:\n"
        "1. ONLY assign meals for the dates listed in 'dates_needing_dinners'. DO NOT assign meals for excluded dates.\n"
        "2. You MUST select recipes exclusively from the provided 'recipe_catalog'. Every recipe_id and recipe_name MUST match exactly.\n"
        "3. Prioritize user goals (e.g. high protein, high fiber, comfort food, quick prep, new/untried recipes).\n"
        "4. Variety & Recency: If 'new recipes', 'untried recipes', or 'variety' is requested, strictly prioritize recipes with 'last_made' = null (untried recipes) or oldest 'last_made'. DO NOT select recipes that were made within the last 30 days unless requested.\n"
        "5. Day of week context: Take into account the day of the week (e.g. recommend quicker or simpler meals for busy weeknights, and more elaborate or slow-cooking dishes on weekends).\n"
        "6. Balance styles and proteins across the week (e.g. avoid scheduling heavy chicken or pasta dishes on 3 consecutive days).\n"
        "7. Return the plan conforming strictly to the requested JSON schema."
    )

    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=json.dumps(prompt_data))],
            )
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=PlanResponse,
            temperature=0.4,
        ),
    )

    # Parse and validate response text against Pydantic schema
    raw_json = response.text
    return PlanResponse.model_validate_json(raw_json)


# --------------------------------------------------------------------------
# Terminal UI & Formatting
# --------------------------------------------------------------------------


def display_plan_table(
    window: list[datetime.date],
    skip_map: dict[str, str],
    selected_meals: dict[str, PlannedMeal],
    summary: str,
):
    """Prints a styled terminal table showing the full planned week."""
    print("\n" + "=" * 80)
    print("  WEEKLY MEAL PLAN PROPOSAL")
    print("=" * 80)
    print(f"Theme & Summary: {summary}\n")
    print(f"{'Date':<12} {'Day':<10} {'Type':<8} {'Dinner / Note':<32} {'Details / Rationale'}")
    print("-" * 80)

    for dt in window:
        dt_str = dt.isoformat()
        day_name = dt.strftime("%A")

        if dt_str in skip_map:
            entry_type = "[Note]"
            title = skip_map[dt_str]
            details = "Excluded day - not cooking"
        elif dt_str in selected_meals:
            entry_type = "[Meal]"
            meal = selected_meals[dt_str]
            title = meal.recipe_name[:30]
            details = meal.rationale
        else:
            entry_type = "[Empty]"
            title = "(No recipe assigned)"
            details = "-"

        print(f"{dt_str:<12} {day_name:<10} {entry_type:<8} {title:<32} {details}")

    print("=" * 80 + "\n")


# --------------------------------------------------------------------------
# Interactive Prompt
# --------------------------------------------------------------------------


def prompt_interactive(window_start: datetime.date) -> tuple[datetime.date, int, str, list[str]]:
    """Gathers user preferences interactively when no CLI flags are passed."""
    print("\n🍽️  Mealie Weekly Meal Planner Setup")
    print("-" * 50)

    # 1. Start date
    start_str = input(f"Start date (YYYY-MM-DD) [default: {window_start}]: ").strip()
    if start_str:
        try:
            start_date = datetime.date.fromisoformat(start_str)
        except ValueError:
            print(f"[!] Invalid date format '{start_str}', defaulting to {window_start}")
            start_date = window_start
    else:
        start_date = window_start

    # 2. Days
    days_str = input("Number of days to plan [default: 7]: ").strip()
    days = 7
    if days_str:
        try:
            days = int(days_str)
        except ValueError:
            print("[!] Invalid integer, defaulting to 7.")

    # 3. Goals
    print("\nGoals for this week (e.g. 'high protein, high fiber, seasonal fall, new untried recipes'):")
    goals = input("Goals: ").strip()
    if not goals:
        goals = "Nutritious, balanced dinners matching the current season."

    # 4. Skips
    print(
        "\nAny days to exclude? (Enter comma-separated or one per prompt, e.g. 'Wed: Team Dinner, Friday: Date Night')"
    )
    print("Leave empty if you cook every day.")
    skips_raw = input("Excluded days: ").strip()
    skips = []
    if skips_raw:
        for part in skips_raw.split(","):
            if part.strip():
                skips.append(part.strip())

    return start_date, days, goals, skips


# --------------------------------------------------------------------------
# Main Workflow
# --------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Weekly Mealie Meal Planner with Gemini")
    parser.add_argument("--start-date", help="Planning start date (YYYY-MM-DD, defaults to Sunday/today)")
    parser.add_argument("--days", type=int, default=None, help="Number of days to plan (default: 7)")
    parser.add_argument("--goals", help="Weekly nutritional/flavor goals")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Exclude days with notes (repeatable, e.g. --skip 'Wed: Dinner out')",
    )
    parser.add_argument("--confirm", "-y", action="store_true", help="Auto-confirm and write directly to Mealie")
    parser.add_argument("--dry-run", action="store_true", help="Simulate generation without writing to Mealie")
    parser.add_argument("--log-file", help="Path to append log file")

    args = parser.parse_args()

    # Determine default start date (default to today)
    today = datetime.date.today()
    default_start = today

    # Environment variables
    mealie_url = os.environ.get("MEALIE_URL", "https://mealie.mattdies.com")
    mealie_token = os.environ.get("MEALIE_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not mealie_token and not args.dry_run:
        print("[!] ERROR: MEALIE_API_KEY environment variable is not set.", file=sys.stderr)
        print("    Add it to ~/.envvars or supply it before running.", file=sys.stderr)
        sys.exit(1)

    if not gemini_key:
        print("[!] ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("    Add it to ~/.envvars or supply it before running.", file=sys.stderr)
        sys.exit(1)

    # Interactive vs Flag mode
    is_interactive = args.goals is None and not args.confirm and not args.dry_run
    if is_interactive:
        start_date, days, goals, raw_skips = prompt_interactive(default_start)
    else:
        if args.start_date:
            try:
                start_date = datetime.date.fromisoformat(args.start_date)
            except ValueError:
                print(f"[!] Invalid --start-date '{args.start_date}', expected YYYY-MM-DD", file=sys.stderr)
                sys.exit(1)
        else:
            start_date = default_start

        days = args.days if args.days is not None else 7
        goals = args.goals or "Balanced, nutritious dinners matching the current season."
        raw_skips = args.skip

    window = calculate_planning_window(start_date, days)

    # Parse skips
    skip_map: dict[str, str] = {}
    for item in raw_skips:
        try:
            d_obj, reason = parse_skip_spec(item, window)
            skip_map[d_obj.isoformat()] = reason
        except ValueError as exc:
            print(f"[!] Warning: Skipping invalid exclusion '{item}': {exc}", file=sys.stderr)

    cook_dates = [d for d in window if d.isoformat() not in skip_map]

    print(f"\n[+] Planning window: {window[0]} to {window[-1]} ({len(window)} days)")
    print(f"[+] Cook days: {len(cook_dates)} | Excluded days: {len(skip_map)}")
    print(f"[+] Goals: {goals}")

    # Connect to Mealie and fetch catalog
    mealie = MealieClient(base_url=mealie_url, api_token=mealie_token or "")
    print(f"\n[+] Fetching recipes from Mealie at {mealie_url}...")
    try:
        catalog = mealie.get_all_recipes()
    except Exception as exc:
        print(f"[!] Failed to fetch recipes from Mealie: {exc}", file=sys.stderr)
        sys.exit(1)

    if not catalog:
        print("[!] No recipes found in Mealie library.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Found {len(catalog)} recipes in Mealie.")

    # Fetch recent meal plan history to track when recipes were last made
    print("[+] Fetching meal plan history to determine recipe recency...")
    last_made_map: dict[str, str] = {}
    try:
        recent_entries = mealie.get_recent_mealplans(limit=150)
        last_made_map = get_recipe_last_made_map(recent_entries)
        print(f"[+] Loaded recency history for {len(last_made_map)} recipes.")
    except Exception as exc:
        print(
            f"[!] Warning: Could not fetch meal plan history ({exc}); proceeding without recency data.", file=sys.stderr
        )

    catalog_map = {r["id"]: r for r in catalog if r.get("id")}

    # Gemini Selection Loop (with re-roll support)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    while True:
        print(f"\n[+] Consulting Google Gemini ({model_name}) for recipe selection...")
        try:
            plan_response = generate_plan_with_gemini(
                api_key=gemini_key,
                recipe_catalog=catalog,
                cook_dates=cook_dates,
                goals=goals,
                skip_map=skip_map,
                last_made_map=last_made_map,
            )
        except Exception as exc:
            print(f"[!] Gemini generation failed: {exc}", file=sys.stderr)
            sys.exit(1)

        # Validate recipe IDs
        raw_selections = [m.model_dump() for m in plan_response.selected_meals]
        valid, invalid = validate_gemini_selection(raw_selections, catalog_map)
        if invalid:
            print(f"[!] Warning: Gemini returned {len(invalid)} unverified recipe IDs; filtering them out.")

        meal_lookup: dict[str, PlannedMeal] = {
            m.date: m for m in plan_response.selected_meals if m.recipe_id in catalog_map
        }

        # Display proposed plan
        display_plan_table(window, skip_map, meal_lookup, plan_response.summary_of_week)

        if args.dry_run:
            print("[Dry-Run] Plan generated successfully. No changes written to Mealie.")
            return

        if args.confirm:
            action = "c"
        else:
            action = input("Proceed with this plan? ([c]onfirm / [r]e-roll with Gemini / [a]bort): ").strip().lower()

        if action in ("c", "yes", "y"):
            break
        elif action in ("r", "reroll"):
            print("\n[~] Re-rolling with Gemini...")
            continue
        else:
            print("Operation aborted by user.")
            sys.exit(0)

    # Check existing entries in Mealie to avoid accidental overwrites
    start_iso = window[0].isoformat()
    end_iso = window[-1].isoformat()
    try:
        existing = mealie.get_existing_mealplans(start_iso, end_iso)
        if existing and not args.confirm:
            overwrite = (
                input(f"[!] Found {len(existing)} existing meal plan entry(ies) in this window. Overwrite? (y/N): ")
                .strip()
                .lower()
            )
            if overwrite not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)
    except Exception as exc:
        print(f"[!] Warning: Could not inspect existing meal plans: {exc}", file=sys.stderr)

    # Post entries to Mealie
    print("\n[+] Posting meal plan entries to Mealie...")
    success_count = 0
    for dt in window:
        dt_str = dt.isoformat()
        if dt_str in skip_map:
            # Note entry
            payload = build_mealplan_entry(
                date_str=dt_str,
                recipe_id=None,
                note_title=skip_map[dt_str],
                note_text="Auto-planned obligation",
            )
        elif dt_str in meal_lookup:
            # Recipe entry
            meal = meal_lookup[dt_str]
            payload = build_mealplan_entry(
                date_str=dt_str,
                recipe_id=meal.recipe_id,
                note_title="",
                note_text=f"Auto-planned: {meal.rationale}",
            )
        else:
            continue

        try:
            mealie.create_mealplan_entry(payload)
            success_count += 1
            print(f"  [✓] {dt_str}: {payload.get('title') or meal_lookup[dt_str].recipe_name}")
        except Exception as exc:
            print(f"  [✗] Failed to post entry for {dt_str}: {exc}", file=sys.stderr)

    print(f"\n[✓] Successfully created {success_count} meal plan entries in Mealie!")
    print(f"[i] View your calendar at: {mealie_url}/meal-planner")


if __name__ == "__main__":
    main()
