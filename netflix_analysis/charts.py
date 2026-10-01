"""Plotly figures used by the dashboard. Each takes the filtered dataframe."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from netflix_analysis.cleaning import explode_list

RED = "#E50914"
RED_SOFT = "#F5838A"
INK = "#F4F1EE"
MUTED = "#A39E99"
GRID = "rgba(255,255,255,0.07)"
TYPE_COLORS = {"Movie": RED, "TV Show": "#F2C14E"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hoverlabel=dict(bgcolor="#1C1A19", bordercolor=RED, font_color=INK),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, title_font_color=MUTED)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title_font_color=MUTED)
    return fig


def added_per_year(df: pd.DataFrame) -> go.Figure:
    data = df.groupby(["year_added", "type"]).size().reset_index(name="titles")
    fig = px.area(data, x="year_added", y="titles", color="type", color_discrete_map=TYPE_COLORS,
                  labels={"year_added": "Year added", "titles": "Titles"})
    fig.update_traces(line_width=2)
    return style(fig)


def type_split(df: pd.DataFrame) -> go.Figure:
    counts = df["type"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.62, sort=False,
        marker=dict(colors=[TYPE_COLORS.get(t, MUTED) for t in counts.index], line=dict(color="#141414", width=3)),
        textinfo="percent", textfont=dict(size=15, color="#141414"),
        hovertemplate="%{label}: %{value:,} titles<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{counts.sum():,}</b><br>titles", showarrow=False, font=dict(size=18, color=INK))
    return style(fig)


def top_bar(values: pd.Series, n: int = 10, color: str = RED, label: str = "Titles") -> go.Figure:
    top = values.value_counts().head(n).sort_values()
    fig = px.bar(x=top.values, y=top.index, orientation="h", labels={"x": label, "y": ""})
    fig.update_traces(marker_color=color, hovertemplate="%{y}: %{x:,}<extra></extra>")
    return style(fig, height=max(260, 34 * len(top) + 40))


def top_genres(df: pd.DataFrame, n: int = 10) -> go.Figure:
    return top_bar(explode_list(df["listed_in"], "genre"), n)


def top_countries(df: pd.DataFrame, n: int = 10) -> go.Figure:
    return top_bar(explode_list(df["country"], "country"), n)


def top_people(df: pd.DataFrame, column: str, n: int = 10) -> go.Figure:
    return top_bar(explode_list(df[column], column), n, color=RED_SOFT)


def world_map(df: pd.DataFrame) -> go.Figure:
    counts = explode_list(df["country"], "country").value_counts().reset_index()
    counts.columns = ["country", "titles"]
    fig = px.choropleth(counts, locations="country", locationmode="country names", color="titles",
                        color_continuous_scale=["#3A1416", "#8E0B12", RED, "#FF8A8F"],
                        hover_name="country", hover_data={"country": False, "titles": ":,"})
    fig.update_geos(bgcolor="rgba(0,0,0,0)", showframe=False, showcoastlines=False,
                    landcolor="#2A2726", showland=True, projection_type="natural earth")
    fig.update_layout(coloraxis_colorbar=dict(title="Titles", thickness=12, len=0.7))
    return style(fig, height=430)


def rating_distribution(df: pd.DataFrame) -> go.Figure:
    order = df["rating"].value_counts().index.tolist()
    data = df.groupby(["rating", "type"]).size().reset_index(name="titles")
    fig = px.bar(data, x="rating", y="titles", color="type", barmode="group",
                 category_orders={"rating": order}, color_discrete_map=TYPE_COLORS,
                 labels={"rating": "Rating", "titles": "Titles"})
    return style(fig)


def movie_lengths(df: pd.DataFrame) -> go.Figure:
    movies = df[(df["type"] == "Movie") & df["duration_value"].notna()]
    fig = px.histogram(movies, x="duration_value", nbins=40, labels={"duration_value": "Minutes"})
    fig.update_traces(marker_color=RED, hovertemplate="%{x} min: %{y:,} movies<extra></extra>")
    if len(movies):
        median = movies["duration_value"].median()
        fig.add_vline(x=median, line_dash="dash", line_color=INK,
                      annotation_text=f"Median {median:.0f} min", annotation_font_color=INK)
    fig.update_yaxes(title="Movies")
    return style(fig)


def show_seasons(df: pd.DataFrame) -> go.Figure:
    shows = df[(df["type"] == "TV Show") & df["duration_value"].notna()]
    counts = shows["duration_value"].astype(int).value_counts().sort_index()
    fig = px.bar(x=counts.index.astype(str), y=counts.values, labels={"x": "Seasons", "y": "TV shows"})
    fig.update_traces(marker_color=TYPE_COLORS["TV Show"], hovertemplate="%{x} seasons: %{y:,}<extra></extra>")
    return style(fig)


def month_heatmap(df: pd.DataFrame) -> go.Figure:
    heat = (df.groupby(["year_added", "month_added"]).size().unstack(fill_value=0)
              .reindex(columns=MONTHS, fill_value=0))
    heat = heat[heat.index >= 2015] if (heat.index >= 2015).any() else heat
    fig = px.imshow(heat, color_continuous_scale=["#1C1A19", "#8E0B12", RED, "#FF8A8F"], aspect="auto",
                    labels=dict(x="", y="Year", color="Titles"), text_auto=True)
    fig.update_xaxes(tickvals=list(range(12)), ticktext=[m[:3] for m in MONTHS], side="top")
    fig.update_yaxes(type="category", autorange="reversed")
    return style(fig, height=420)


def missing_before_after(before: dict, after: dict) -> go.Figure:
    cols = sorted(before, key=before.get, reverse=True)
    fig = go.Figure([
        go.Bar(name="Before", x=cols, y=[before[c] for c in cols], marker_color=RED),
        go.Bar(name="After", x=cols, y=[after.get(c, 0) for c in cols], marker_color="#4CC38A"),
    ])
    fig.update_layout(barmode="group", yaxis_title="Missing values")
    return style(fig)
