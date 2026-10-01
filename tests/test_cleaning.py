import pandas as pd
import pytest

from netflix_analysis.cleaning import DatasetError, clean, explode_list


def test_report_counts(raw):
    df, report = clean(raw)
    assert report.rows_before == 8
    assert report.duplicates_removed == 1
    assert report.misplaced_durations_fixed == 1
    assert report.countries_filled_from_director == 1   # Beta borrows Jane Doe's country
    assert report.rows_dropped == 1                     # Epsilon has no date_added
    assert report.rows_after == len(df) == 6
    assert report.missing_after == {}


def test_misplaced_duration_is_moved(raw):
    df, _ = clean(raw)
    delta = df.set_index("title").loc["Delta"]
    assert delta["duration"] == "74 min"
    assert delta["rating"] != "74 min"
    assert delta["duration_value"] == 74


def test_country_filled_from_director_then_unknown(raw):
    df, _ = clean(raw)
    by_title = df.set_index("title")
    assert by_title.loc["Beta", "country"] == "United States"
    assert by_title.loc["Delta", "country"] == "Unknown"


def test_rating_filled_with_mode_of_same_type(raw):
    df, _ = clean(raw)
    assert df["rating"].notna().all()
    # TV shows in the sample are rated TV-MA or TV-14, never a movie rating
    assert df.set_index("title").loc["Eta", "rating"] in {"TV-MA", "TV-14"}


def test_dates_and_features(raw):
    df, _ = clean(raw)
    beta = df.set_index("title").loc["Beta"]
    assert beta["year_added"] == 2020 and beta["month_added"] == "August"
    assert beta["years_to_netflix"] == 1
    gamma = df.set_index("title").loc["Gamma"]
    assert gamma["duration_unit"] == "Season" and gamma["main_country"] == "India"


def test_wrong_file_is_rejected():
    with pytest.raises(DatasetError, match="Missing columns"):
        clean(pd.DataFrame({"a": [1]}))


def test_explode_list_skips_unknown_and_blanks():
    values = explode_list(pd.Series(["India, United Kingdom", "Unknown", None, "India"]), "country")
    assert values.value_counts().to_dict() == {"India": 2, "United Kingdom": 1}
