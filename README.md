# Netflix Content Explorer

An interactive Streamlit dashboard for exploring the Netflix catalogue: what's on the platform, where it comes from, and how it has grown over time. It is built on the [Netflix Movies and TV Shows](https://www.kaggle.com/datasets/shivamb/netflix-shows) dataset from Kaggle.

**Live demo:** _add your Streamlit Cloud link here_

<!-- Add a screenshot of the dashboard here, saved as docs/dashboard.png:
![Netflix Content Explorer](docs/dashboard.png) -->

## Features

- **Filters** for type, year added, release year, genres, countries, ratings and a free-text search across title, director and cast. Every chart and number updates instantly.
- **Six views:** an overview with yearly growth, a month-by-year heatmap and the movie / TV show split; an interactive world map and top countries; genres, ratings, movie lengths and TV seasons; top directors and cast; a data cleaning report; and a searchable table of titles.
- **Live key findings** written in plain English and recalculated for whatever is currently selected, rather than hard-coded.
- **Data cleaning report** showing every problem found in the raw file and how it was fixed, with missing values before and after.
- **CSV export** of the filtered titles.
- **Friendly file handling:** if the dataset is missing, the app explains where to put it and offers an upload button, instead of crashing.

## How the data is cleaned

| Problem in the raw data | Fix |
|---|---|
| Duplicate rows | Removed |
| Durations such as "74 min" stored in the `rating` column | Moved to `duration`, rating refilled |
| Missing `country` | Filled from the same director's other titles, otherwise "Unknown" |
| Missing `director` / `cast` | Marked "Unknown", since they can't be guessed |
| Missing `rating` | Most common rating for that content type |
| `date_added` as text with stray spaces and mixed formats | Stripped and parsed to dates |
| A few rows with no usable date or duration | Dropped |

New columns are derived for analysis: `year_added`, `month_added`, `duration_value`, `duration_unit`, `main_country` and `years_to_netflix`.

## Run it locally

```bash
git clone https://github.com/muhammad-zeeshan-4854/netflix-dashboard.git
cd netflix-dashboard
python -m venv .venv
.venv\Scripts\activate          # macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Download `netflix_titles.csv` from Kaggle and put it in the `data/` folder, or upload it from the app.

## Deploy for free

1. Push this repository to GitHub, including `data/netflix_titles.csv`.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io) with GitHub.
3. Choose **Create app**, select this repository, set the main file to `app.py` and deploy.

## Project structure

```
app.py                       Streamlit dashboard
netflix_analysis/
  cleaning.py                cleaning pipeline and cleaning report
  filters.py                 filtering logic and live insights
  charts.py                  Plotly charts with a shared theme
tests/                       pytest tests for cleaning, filters and the app itself
.streamlit/config.toml       dark theme
```

The cleaning and filtering logic lives outside `app.py`, so it is tested independently of the UI:

```bash
pip install -r requirements-dev.txt
pytest
```

## Tech

Python, pandas, NumPy, Plotly, Streamlit, pytest.
