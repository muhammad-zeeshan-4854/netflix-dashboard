"""Filtering logic for the dashboard, kept separate so it can be tested."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from netflix_analysis.cleaning import explode_list


@dataclass
class Filters:
    types: list[str] = field(default_factory=list)
    year_added: tuple[int, int] | None = None
    release_year: tuple[int, int] | None = None
    genres: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    ratings: list[str] = field(default_factory=list)
    query: str = ""


def _has_any(series: pd.Series, wanted: list[str]) -> pd.Series:
    """True where a comma-separated cell contains at least one wanted value."""
    wanted_set = set(wanted)
    return series.fillna("").str.split(",").apply(lambda items: any(i.strip() in wanted_set for i in items))


def apply_filters(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if f.types:
        mask &= df["type"].isin(f.types)
    if f.year_added:
        mask &= df["year_added"].between(*f.year_added)
    if f.release_year:
        mask &= df["release_year"].between(*f.release_year)
    if f.genres:
        mask &= _has_any(df["listed_in"], f.genres)
    if f.countries:
        mask &= _has_any(df["country"], f.countries)
    if f.ratings:
        mask &= df["rating"].isin(f.ratings)
    if f.query.strip():
        q = f.query.strip()
        text = df["title"].fillna("") + " " + df["director"].fillna("") + " " + df["cast"].fillna("")
        mask &= text.str.contains(q, case=False, regex=False)
    return df[mask]


def options_by_frequency(series: pd.Series, name: str) -> list[str]:
    """Distinct values of a comma-separated column, most common first."""
    return explode_list(series, name).value_counts().index.tolist()


def insights(df: pd.DataFrame) -> list[str]:
    """Plain-English findings computed from whatever is currently filtered."""
    out: list[str] = []
    if df.empty:
        return out
    share = df["type"].value_counts(normalize=True)
    lead = share.index[0]
    out.append(f"**{lead}s** make up **{share.iloc[0]:.0%}** of these titles.")

    per_year = df["year_added"].value_counts()
    out.append(f"The most titles were added in **{per_year.idxmax()}** ({per_year.max():,}).")

    countries = explode_list(df["country"], "country").value_counts()
    if len(countries):
        top3 = ", ".join(countries.index[:3])
        out.append(f"Top producing countries: **{top3}**.")

    genres = explode_list(df["listed_in"], "genre").value_counts()
    if len(genres):
        out.append(f"The most common genre is **{genres.index[0]}**.")

    movies = df[(df["type"] == "Movie") & df["duration_value"].notna()]
    if len(movies):
        out.append(f"The median movie runs **{movies['duration_value'].median():.0f} minutes**.")

    shows = df[(df["type"] == "TV Show") & df["duration_value"].notna()]
    if len(shows):
        one = (shows["duration_value"] == 1).mean()
        out.append(f"**{one:.0%}** of TV shows have only one season.")
    return out
