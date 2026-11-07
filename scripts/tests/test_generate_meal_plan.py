import datetime

import pytest
from generate_meal_plan import (
    build_mealplan_entry,
    calculate_planning_window,
    get_season_context,
    parse_date_or_day_name,
    parse_skip_spec,
    validate_gemini_selection,
)


def test_calculate_planning_window_default():
    # Sunday Nov 8, 2026
    start = datetime.date(2026, 11, 8)
    window = calculate_planning_window(start, days=7)
    assert len(window) == 7
    assert window[0] == datetime.date(2026, 11, 8)
    assert window[-1] == datetime.date(2026, 11, 14)


def test_calculate_planning_window_custom_days():
    start = datetime.date(2026, 11, 8)
    window = calculate_planning_window(start, days=5)
    assert len(window) == 5
    assert window[-1] == datetime.date(2026, 11, 12)


def test_parse_date_or_day_name():
    # Sunday Nov 8 to Saturday Nov 14, 2026
    start = datetime.date(2026, 11, 8)
    window = calculate_planning_window(start, days=7)

    # Day names
    assert parse_date_or_day_name("wed", window) == datetime.date(2026, 11, 11)
    assert parse_date_or_day_name("Wednesday", window) == datetime.date(2026, 11, 11)
    assert parse_date_or_day_name("Sunday", window) == datetime.date(2026, 11, 8)

    # Exact ISO date
    assert parse_date_or_day_name("2026-11-12", window) == datetime.date(2026, 11, 12)

    # Invalid day or outside window
    with pytest.raises(ValueError):
        parse_date_or_day_name("2026-11-20", window)
    with pytest.raises(ValueError):
        parse_date_or_day_name("Funday", window)


def test_parse_skip_spec():
    start = datetime.date(2026, 11, 8)
    window = calculate_planning_window(start, days=7)

    # Day name with reason
    d1, reason1 = parse_skip_spec("Wednesday: Dinner with team", window)
    assert d1 == datetime.date(2026, 11, 11)
    assert reason1 == "Dinner with team"

    # Day name without reason (default note)
    d2, reason2 = parse_skip_spec("Friday", window)
    assert d2 == datetime.date(2026, 11, 13)
    assert "Not cooking" in reason2

    # ISO date with reason
    d3, reason3 = parse_skip_spec("2026-11-09: Date Night", window)
    assert d3 == datetime.date(2026, 11, 9)
    assert reason3 == "Date Night"


def test_build_mealplan_entry_recipe():
    entry = build_mealplan_entry(
        date_str="2026-11-08",
        recipe_id="11111111-2222-3333-4444-555555555555",
        note_title=None,
        note_text="High protein fall dinner",
    )
    assert entry["date"] == "2026-11-08"
    assert entry["entryType"] == "dinner"
    assert entry["recipeId"] == "11111111-2222-3333-4444-555555555555"
    assert entry["text"] == "High protein fall dinner"


def test_build_mealplan_entry_note():
    entry = build_mealplan_entry(
        date_str="2026-11-11",
        recipe_id=None,
        note_title="Dinner with team",
        note_text="Obligation - not cooking",
    )
    assert entry["date"] == "2026-11-11"
    assert entry["entryType"] == "dinner"
    assert entry["recipeId"] is None
    assert entry["title"] == "Dinner with team"
    assert entry["text"] == "Obligation - not cooking"


def test_get_season_context():
    # November -> Fall
    fall_date = datetime.date(2026, 11, 8)
    season, notes = get_season_context(fall_date)
    assert season.lower() in ("fall", "autumn")
    assert "comfort" in notes.lower() or "warm" in notes.lower() or "fall" in notes.lower()


def test_validate_gemini_selection():
    catalog = {
        "uuid-1": {"id": "uuid-1", "name": "Butternut Squash Soup"},
        "uuid-2": {"id": "uuid-2", "name": "Grilled Chicken"},
    }
    selections = [
        {"date": "2026-11-08", "recipe_id": "uuid-1", "recipe_name": "Butternut Squash Soup", "rationale": "Seasonal"},
        {"date": "2026-11-09", "recipe_id": "invalid-uuid", "recipe_name": "Ghost Stew", "rationale": "Missing"},
    ]
    valid, invalid = validate_gemini_selection(selections, catalog)
    assert len(valid) == 1
    assert len(invalid) == 1
    assert valid[0]["recipe_id"] == "uuid-1"
    assert invalid[0]["recipe_id"] == "invalid-uuid"
