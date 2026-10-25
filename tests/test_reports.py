from app.services.reports import build_report

def test_build_report_creates_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.reports.get_settings", lambda: type("Settings", (), {"report_dir": tmp_path})())
    output = build_report([{"department": "Sales", "revenue": 42}], "Weekly")
    assert output.exists() and output.suffix == ".pdf"
