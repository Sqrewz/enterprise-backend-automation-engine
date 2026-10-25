from pathlib import Path
from uuid import uuid4
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors
from app.core.config import get_settings

def build_report(records: list[dict], title: str) -> Path:
    df=pd.DataFrame(records)
    settings=get_settings(); settings.report_dir.mkdir(parents=True, exist_ok=True)
    path=settings.report_dir / f"report-{uuid4()}.pdf"
    story=[Paragraph(title, getSampleStyleSheet()["Title"]), Spacer(1, 12)]
    story.append(Paragraph(f"Records analysed: {len(df)}", getSampleStyleSheet()["BodyText"]))
    if not df.empty:
        summary=df.describe(include="all").fillna("").astype(str).reset_index()
        rows=[summary.columns.tolist(), *summary.values.tolist()]
        table=Table(rows, repeatRows=1); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),7)])); story.append(table)
    SimpleDocTemplate(str(path), pagesize=A4).build(story); return path
