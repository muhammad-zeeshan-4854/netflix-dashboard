import pandas as pd
import pytest


@pytest.fixture
def raw():
    """A small file with the same problems as the real dataset."""
    rows = [
        # show_id, type, title, director, cast, country, date_added, release_year, rating, duration, listed_in
        ("s1", "Movie", "Alpha", "Jane Doe", "A, B", "United States", "September 25, 2021", 2020, "PG-13", "90 min",
         "Dramas, Comedies"),
        ("s2", "Movie", "Beta", "Jane Doe", None, None, " August 1, 2020", 2019, "R", "120 min", "Dramas"),
        ("s3", "TV Show", "Gamma", None, "C", "India, United Kingdom", "June 3, 2019", 2018, "TV-MA", "2 Seasons",
         "International TV Shows"),
        ("s4", "Movie", "Delta", "Lou Grey", "D", None, "May 5, 2018", 2017, "74 min", None, "Stand-Up Comedy"),
        ("s5", "TV Show", "Epsilon", None, None, "India", None, 2021, "TV-14", "1 Season", "Kids' TV"),
        ("s6", "Movie", "Zeta", "Max Mint", "E", "Canada", "2019-03-04", 2015, None, "100 min", "Comedies"),
        ("s7", "TV Show", "Eta", "Ann Ash", "F", "Japan", "January 9, 2021", 2021, None, "1 Season", "Anime Series"),
    ]
    cols = ["show_id", "type", "title", "director", "cast", "country", "date_added", "release_year",
            "rating", "duration", "listed_in"]
    df = pd.DataFrame(rows, columns=cols)
    return pd.concat([df, df.iloc[[0]]], ignore_index=True)  # one exact duplicate
