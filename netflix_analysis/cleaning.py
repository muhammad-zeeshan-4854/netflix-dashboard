"""Cleaning pipeline for the Kaggle "Netflix Movies and TV Shows" dataset.

The same steps as the exploratory notebook, packaged as functions so the
dashboard and the tests share one source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "show_id", "type", "title", "director", "cast", "country", "date_added",
    "release_year", "rating", "duration", "listed_in",
]


class DatasetError(ValueError):
    """Raised when the file is not the expected Netflix titles dataset."""


@dataclass
class CleaningReport:
    rows_before: int = 0
    rows_after: int = 0
    duplicates_removed: int = 0
    misplaced_durations_fixed: int = 0
    countries_filled_from_director: int = 0
    countries_set_unknown: int = 0
    people_set_unknown: int = 0
    ratings_filled: int = 0
    rows_dropped: int = 0
    missing_before: dict[str, int] = field(default_factory=dict)
    missing_after: dict[str, int] = field(default_factory=dict)

    @property
    def steps(self) -> list[dict]:
        return [
            {"Problem": "Duplicate rows", "Fix": "Removed", "Rows": self.duplicates_removed},
            {"Problem": "Duration stored in the rating column", "Fix": "Moved to duration",
             "Rows": self.misplaced_durations_fixed},
            {"Problem": "Missing country", "Fix": "Filled from the director's other titles",
             "Rows": self.countries_filled_from_director},
            {"Problem": "Missing country, no director match", "Fix": 'Set to "Unknown"',
             "Rows": self.countries_set_unknown},
            {"Problem": "Missing director or cast", "Fix": 'Set to "Unknown"', "Rows": self.people_set_unknown},
            {"Problem": "Missing rating", "Fix": "Most common rating for that content type",
             "Rows": self.ratings_filled},
            {"Problem": "Missing or invalid date added / duration", "Fix": "Dropped", "Rows": self.rows_dropped},
        ]


def validate(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DatasetError(
            "This doesn't look like the Netflix titles dataset. Missing columns: " + ", ".join(missing)
        )


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    validate(raw)
    df = raw.copy()
    report = CleaningReport(rows_before=len(df))
    report.missing_before = {k: int(v) for k, v in df[REQUIRED_COLUMNS].isnull().sum().items() if v}

    # 1. Duplicates
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    report.duplicates_removed = before - len(df)

    # 2. Strip whitespace in text columns
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip()

    # 3. Durations like "74 min" that ended up in the rating column
    wrong = df["rating"].str.contains("min", na=False)
    report.misplaced_durations_fixed = int(wrong.sum())
    fill = wrong & df["duration"].isnull()
    df.loc[fill, "duration"] = df.loc[fill, "rating"]
    df.loc[wrong, "rating"] = np.nan

    # 4. Country: borrow from the same director's other titles, else Unknown
    known = df.dropna(subset=["director", "country"])
    director_country = known.groupby("director")["country"].agg(lambda s: s.mode().iloc[0])
    gaps = df["country"].isnull() & df["director"].notnull()
    nulls_before = int(df["country"].isnull().sum())
    df.loc[gaps, "country"] = df.loc[gaps, "director"].map(director_country)
    report.countries_filled_from_director = nulls_before - int(df["country"].isnull().sum())
    report.countries_set_unknown = int(df["country"].isnull().sum())
    df["country"] = df["country"].fillna("Unknown")

    # 5. Director and cast can't be guessed
    report.people_set_unknown = int(df["director"].isnull().sum() + df["cast"].isnull().sum())
    df["director"] = df["director"].fillna("Unknown")
    df["cast"] = df["cast"].fillna("Unknown")

    # 6. Rating: most common rating within the same type
    report.ratings_filled = int(df["rating"].isnull().sum())
    df["rating"] = df.groupby("type")["rating"].transform(
        lambda s: s.fillna(s.mode().iloc[0] if not s.mode().empty else "NR")
    )

    # 7. Dates, then drop the few rows that still can't be used
    df["date_added"] = pd.to_datetime(df["date_added"], format="mixed", errors="coerce")
    before = len(df)
    df = df.dropna(subset=["date_added", "duration"]).reset_index(drop=True)
    report.rows_dropped = before - len(df)

    df = add_features(df)
    report.rows_after = len(df)
    report.missing_after = {k: int(v) for k, v in df[REQUIRED_COLUMNS].isnull().sum().items() if v}
    return df, report


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year_added"] = df["date_added"].dt.year.astype(int)
    df["month_added"] = df["date_added"].dt.month_name()
    df["duration_value"] = pd.to_numeric(df["duration"].str.extract(r"(\d+)")[0], errors="coerce")
    df["duration_unit"] = np.where(df["duration"].str.contains("min", na=False), "min", "Season")
    df["main_country"] = df["country"].str.split(",").str[0].str.strip()
    df["years_to_netflix"] = df["year_added"] - df["release_year"]
    return df


def explode_list(series: pd.Series, name: str) -> pd.Series:
    """Split a comma-separated column ("A, B") into one cleaned value per row."""
    values = series.fillna("").astype(str).str.split(",").explode().str.strip()
    return values[(values != "") & (values != "Unknown")].rename(name)
