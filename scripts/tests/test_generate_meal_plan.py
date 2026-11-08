import datetime

import pytest
from generate_meal_plan import (
    MealieClient,
    build_mealplan_entry,
    calculate_planning_window,
    format_recipe_time,
    get_recipe_last_made_map,
    get_season_context,
    is_dinner_eligible,
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


def test_format_recipe_time():
    # String representation
    assert format_recipe_time({"totalTime": "45 min"}) == "45 min"
    # Seconds only - minutes
    assert format_recipe_time({"totalTime": None, "totalTimeSeconds": 1800}) == "30 min"
    # Seconds only - hours and minutes
    assert format_recipe_time({"totalTime": None, "totalTimeSeconds": 4500}) == "1 hr 15 min"
    # Seconds only - exact hours
    assert format_recipe_time({"totalTime": None, "totalTimeSeconds": 7200}) == "2 hr"
    # Fallback to prep + perform
    assert (
        format_recipe_time(
            {"totalTime": None, "totalTimeSeconds": None, "prepTimeSeconds": 600, "performTimeSeconds": 1200}
        )
        == "30 min"
    )
    # Neither
    assert format_recipe_time({"totalTime": None, "totalTimeSeconds": None}) is None


def test_is_dinner_eligible():
    dinner_recipe = {"name": "Tofu Stir Fry", "recipeCategory": [{"name": "Dinner"}]}
    dessert_recipe = {"name": "Chocolate Cake", "recipeCategory": [{"name": "Dessert"}]}
    cocktail_recipe = {"name": "Old Fashioned", "recipeCategory": [{"name": "Cocktails"}]}

    # Standard dinner goals should filter out dessert and cocktail
    assert is_dinner_eligible(dinner_recipe, "healthy autumn food") is True
    assert is_dinner_eligible(dessert_recipe, "healthy autumn food") is False
    assert is_dinner_eligible(cocktail_recipe, "healthy autumn food") is False

    # But if dessert is explicitly requested
    assert is_dinner_eligible(dessert_recipe, "autumn dinner with a nice dessert") is True


def test_get_recipe_last_made_map():
    mealplan_items = [
        {"date": "2026-11-05", "recipeId": "rec-1"},
        {"date": "2026-10-20", "recipeId": "rec-2"},
        {"date": "2026-09-01", "recipeId": "rec-1"},  # older entry for rec-1
    ]
    last_made = get_recipe_last_made_map(mealplan_items)
    assert last_made["rec-1"] == "2026-11-05"
    assert last_made["rec-2"] == "2026-10-20"
    assert len(last_made) == 2


def test_pagination_multiple_pages():
    class FakeSession:
        def __init__(self):
            self.calls = 0

        def get(self, url, headers=None, params=None, timeout=None):
            page = params.get("page", 1)
            self.calls += 1

            class FakeResponse:
                def raise_for_status(self):
                    pass

                def json(self):
                    if page == 1:
                        return {"page": 1, "total_pages": 2, "items": [{"id": f"p1-{i}"} for i in range(100)]}
                    elif page == 2:
                        return {"page": 2, "total_pages": 2, "items": [{"id": f"p2-{i}"} for i in range(50)]}
                    return {"page": page, "total_pages": 2, "items": []}

            return FakeResponse()

    client = MealieClient(base_url="https://fake.mealie", api_token="fake", session=FakeSession())
    all_recipes = client.get_all_recipes()
    assert len(all_recipes) == 150
    assert client.session.calls == 2
