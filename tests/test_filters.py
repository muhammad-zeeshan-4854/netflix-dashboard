from netflix_analysis.cleaning import clean
from netflix_analysis.filters import Filters, apply_filters, insights, options_by_frequency


def test_filters_combine(raw):
    df, _ = clean(raw)
    assert len(apply_filters(df, Filters(types=["TV Show"]))) == 2
    assert set(apply_filters(df, Filters(genres=["Comedies"]))["title"]) == {"Alpha", "Zeta"}
    assert set(apply_filters(df, Filters(countries=["United Kingdom"]))["title"]) == {"Gamma"}
    assert set(apply_filters(df, Filters(year_added=(2020, 2021)))["title"]) == {"Alpha", "Beta", "Eta"}
    assert set(apply_filters(df, Filters(query="jane"))["title"]) == {"Alpha", "Beta"}
    assert apply_filters(df, Filters(types=["Movie"], countries=["Japan"])).empty


def test_search_is_literal_not_regex(raw):
    df, _ = clean(raw)
    assert apply_filters(df, Filters(query="(")).empty


def test_options_sorted_by_frequency(raw):
    df, _ = clean(raw)
    assert options_by_frequency(df["listed_in"], "genre")[:2] == ["Dramas", "Comedies"] or \
        options_by_frequency(df["listed_in"], "genre")[:2] == ["Comedies", "Dramas"]


def test_insights_are_computed(raw):
    df, _ = clean(raw)
    lines = insights(df)
    assert any("Movies" in line and "67%" in line for line in lines)
    assert any("median movie" in line.lower() for line in lines)
    assert insights(df.iloc[0:0]) == []
