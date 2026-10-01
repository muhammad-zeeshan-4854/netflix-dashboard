"""Smoke tests that run the whole Streamlit app headlessly."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_missing_file_shows_notice(monkeypatch, tmp_path):

    at = AppTest.from_file(APP)
    at.run(timeout=30)
    if Path(APP).with_name("data").joinpath("netflix_titles.csv").exists():
        return  # real data present locally; covered by the next test
    assert not at.exception
    assert any("Dataset file not found" in m.value for m in at.markdown)
    assert len(at.get("file_uploader")) == 1


def test_dashboard_renders_with_data(raw):
    at = AppTest.from_file(APP)
    at.session_state["uploaded_bytes"] = raw.to_csv(index=False).encode()
    at.session_state["uploaded_name"] = "test.csv"
    at.run(timeout=60)
    assert not at.exception
    assert at.metric[0].value == "6"           # titles after cleaning
    assert len(at.tabs) == 6
