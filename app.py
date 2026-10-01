"""Netflix Content Explorer: an interactive dashboard on the Kaggle Netflix titles dataset.

Run locally with:  streamlit run app.py
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from netflix_analysis import charts
from netflix_analysis.cleaning import DatasetError, clean, explode_list
from netflix_analysis.filters import Filters, apply_filters, insights, options_by_frequency

DATA_FILE = Path(__file__).parent / "data" / "netflix_titles.csv"
DATASET_URL = "https://www.kaggle.com/datasets/shivamb/netflix-shows"
FILTER_KEYS = ["f_types", "f_year", "f_release", "f_genres", "f_countries", "f_ratings", "f_query"]

st.set_page_config(page_title="Netflix Content Explorer", page_icon="🎬", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.2rem; max-width: 1320px; }
      .hero h1 { font-size: 2.6rem; font-weight: 800; letter-spacing: -0.03em; margin: 0; line-height: 1.1; }
      .hero p { color: #A39E99; font-size: 1.05rem; margin: .4rem 0 0; }
      .hero h1::before { content: ""; display: block; width: 64px; height: 5px; background: #E50914;
                         border-radius: 3px; margin-bottom: 1rem; }
      .notice { border-left: 6px solid #E50914; background: #1F1D1C; padding: 18px 22px;
                border-radius: 8px; line-height: 1.7; margin: 1rem 0; }
      .notice b { font-size: 1.1rem; }
      .notice code { background: #141414; padding: 2px 6px; border-radius: 4px; }
      div[data-testid="stMetric"] { background: #1F1D1C; border-radius: 12px; padding: 14px 16px; }
      div[data-testid="stMetricValue"] { font-weight: 800; }
    </style>
    """,
    unsafe_allow_html=True,
)


def notice(title: str, body: str) -> None:
    st.markdown(f'<div class="notice"><b>{title}</b><br>{body}</div>', unsafe_allow_html=True)


@st.cache_data(show_spinner="Cleaning the dataset…")
def load_and_clean(raw_bytes: bytes):
    raw = pd.read_csv(io.BytesIO(raw_bytes))
    return clean(raw)


def get_data():
    """Use data/netflix_titles.csv if present, otherwise ask for an upload."""
    if "uploaded_bytes" in st.session_state:
        return st.session_state["uploaded_bytes"], st.session_state.get("uploaded_name", "uploaded file")
    if DATA_FILE.exists():
        return DATA_FILE.read_bytes(), f"data/{DATA_FILE.name}"

    notice(
        "📂 Dataset file not found",
        f'Download <code>netflix_titles.csv</code> from <a href="{DATASET_URL}" target="_blank">Kaggle</a> '
        f"and either place it here:<br><code>{DATA_FILE}</code><br>"
        "and refresh the page, or upload it below.",
    )
    upload = st.file_uploader("Upload netflix_titles.csv", type="csv")
    if upload is None:
        st.stop()
    st.session_state["uploaded_bytes"] = upload.getvalue()
    st.session_state["uploaded_name"] = upload.name
    st.rerun()


def reset_filters() -> None:
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


# ---------------------------------------------------------------- data
raw_bytes, source_name = get_data()
try:
    df, report = load_and_clean(raw_bytes)
except (DatasetError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
    notice("⚠️ This file could not be used", f"{exc}<br>Download the dataset again from Kaggle and upload it.")
    st.session_state.pop("uploaded_bytes", None)
    if st.button("Upload a different file"):
        st.rerun()
    st.stop()

# ---------------------------------------------------------------- sidebar filters
with st.sidebar:
    st.markdown("### Filters")
    types = st.pills("Type", ["Movie", "TV Show"], selection_mode="multi",
                     default=["Movie", "TV Show"], key="f_types")
    y_min, y_max = int(df["year_added"].min()), int(df["year_added"].max())
    year_added = st.slider("Year added to Netflix", y_min, y_max, (y_min, y_max), key="f_year")
    r_min, r_max = int(df["release_year"].min()), int(df["release_year"].max())
    release = st.slider("Release year", r_min, r_max, (r_min, r_max), key="f_release")
    genres = st.multiselect("Genres", options_by_frequency(df["listed_in"], "genre"),
                            placeholder="All genres", key="f_genres")
    countries = st.multiselect("Countries", options_by_frequency(df["country"], "country"),
                               placeholder="All countries", key="f_countries")
    ratings = st.multiselect("Ratings", df["rating"].value_counts().index.tolist(),
                             placeholder="All ratings", key="f_ratings")
    query = st.text_input("Search title, director or cast", key="f_query", placeholder="e.g. Christopher Nolan")
    st.button("Reset filters", on_click=reset_filters, width="stretch")

    st.divider()
    st.caption(f"Data: {source_name} · {report.rows_after:,} titles after cleaning")
    if "uploaded_bytes" in st.session_state and st.button("Remove uploaded file", type="tertiary"):
        st.session_state.pop("uploaded_bytes")
        st.rerun()

view = apply_filters(df, Filters(types=types or [], year_added=year_added, release_year=release,
                                 genres=genres, countries=countries, ratings=ratings, query=query))

# ---------------------------------------------------------------- header + KPIs
st.markdown(
    '<div class="hero"><h1>Netflix Content Explorer</h1>'
    "<p>What's on Netflix, where it comes from and how the catalogue has grown. "
    "Use the filters on the left to explore.</p></div>",
    unsafe_allow_html=True,
)
st.write("")

if view.empty:
    notice("No titles match these filters", "Remove a filter or press <b>Reset filters</b> in the sidebar.")
    st.stop()

movies = view[view["type"] == "Movie"]
shows = view[view["type"] == "TV Show"]
k = st.columns(5)
k[0].metric("Titles", f"{len(view):,}")
k[1].metric("Movies", f"{len(movies):,}")
k[2].metric("TV shows", f"{len(shows):,}")
k[3].metric("Countries", f"{explode_list(view['country'], 'country').nunique():,}")
k[4].metric("Median movie length", f"{movies['duration_value'].median():.0f} min" if len(movies) else "–")

tabs = st.tabs(["Overview", "Where it's from", "What it is", "Who makes it", "Data cleaning", "Browse titles"])

with tabs[0]:
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        st.subheader("Titles added each year")
        st.plotly_chart(charts.added_per_year(view))
    with right:
        st.subheader("Movies vs TV shows")
        st.plotly_chart(charts.type_split(view))
    left, right = st.columns([2.2, 1], gap="large")
    with left:
        st.subheader("When titles were added")
        st.plotly_chart(charts.month_heatmap(view))
    with right:
        st.subheader("Key findings")
        with st.container(border=True):
            for line in insights(view):
                st.markdown(f"- {line}")
        st.caption("Calculated live from the titles currently selected.")

with tabs[1]:
    st.subheader("Titles by country")
    st.plotly_chart(charts.world_map(view))
    st.subheader("Top 10 countries")
    st.plotly_chart(charts.top_countries(view))
    st.caption("Co-productions count once for every country involved.")

with tabs[2]:
    st.subheader("Top 10 genres")
    st.plotly_chart(charts.top_genres(view))
    st.subheader("Ratings")
    st.plotly_chart(charts.rating_distribution(view))
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Movie length")
        st.plotly_chart(charts.movie_lengths(view))
    with right:
        st.subheader("TV show seasons")
        st.plotly_chart(charts.show_seasons(view))

with tabs[3]:
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Top 10 directors")
        st.plotly_chart(charts.top_people(view, "director"))
    with right:
        st.subheader("Top 10 cast members")
        st.plotly_chart(charts.top_people(view, "cast"))
    st.caption('Titles with an unknown director or cast are left out of these charts.')

with tabs[4]:
    st.subheader("How the raw data was cleaned")
    c = st.columns(3)
    c[0].metric("Rows in raw file", f"{report.rows_before:,}")
    removed = report.rows_before - report.rows_after
    c[1].metric("Rows after cleaning", f"{report.rows_after:,}",
                delta=f"-{removed:,} rows" if removed else None, delta_color="off")
    c[2].metric("Missing values left", f"{sum(report.missing_after.values()):,}")
    st.dataframe(pd.DataFrame(report.steps), hide_index=True)
    if report.missing_before:
        st.subheader("Missing values before and after")
        st.plotly_chart(charts.missing_before_after(report.missing_before, report.missing_after))

with tabs[5]:
    st.subheader(f"{len(view):,} titles")
    table = view[["title", "type", "release_year", "year_added", "rating", "duration",
                  "country", "director", "listed_in"]].sort_values("year_added", ascending=False)
    st.dataframe(
        table, hide_index=True, height=520,
        column_config={
            "title": "Title", "type": "Type", "rating": "Rating", "duration": "Duration",
            "country": "Country", "director": "Director", "listed_in": "Genres",
            "release_year": st.column_config.NumberColumn("Released", format="%d"),
            "year_added": st.column_config.NumberColumn("Added", format="%d"),
        },
    )
    st.download_button("Download these titles as CSV", table.to_csv(index=False).encode(),
                        file_name="netflix_filtered.csv", mime="text/csv")

st.divider()
st.caption(
    f'Data: [Netflix Movies and TV Shows]({DATASET_URL}) on Kaggle. '
    "Built by [Muhammad Zeeshan](https://muhammad-zeeshan-4854.github.io) with Python, pandas, Plotly and Streamlit."
)
