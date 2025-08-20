
import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
import json

# ================== UTILS ==================
def get_ranking(score):
    if score < 2:
        return "Very Low"
    elif score < 4:
        return "Low"
    elif score < 6:
        return "Average"
    elif score < 8:
        return "High"
    else:
        return "Very High"

ranking_colors = {
    "Very Low": "#ff4d4d",
    "Low": "#ff944d",
    "Average": "#ffeb3b",
    "High": "#81c784",
    "Very High": "#42a5f5"
}

# Excel helper (XlsxWriter)
def _build_excel_report(df_summary, df_questions, project_name, eval_date_str):
    import pandas as pd
    import numpy as np
    from io import BytesIO

    summary = df_summary.copy() if df_summary is not None else pd.DataFrame()
    qdf     = df_questions.copy() if df_questions is not None else pd.DataFrame()

    if "Score" in summary.columns:
        summary["Score"] = pd.to_numeric(summary["Score"], errors="coerce")
    if "Domain" in summary.columns:
        summary["Domain"] = summary["Domain"].astype(str)

    if "Lowest Questions" in summary.columns:
        summary = summary.drop(columns=["Lowest Questions"])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        # Summary sheet
        start_row = 2
        summary.to_excel(writer, index=False, sheet_name="Summary", startrow=start_row)
        workbook  = writer.book
        ws        = writer.sheets["Summary"]

        # Row 1: Project and Date
        merge_format = workbook.add_format({"align": "center", "bold": True})
        ws.merge_range(0, 0, 0, max(0, len(summary.columns)-1), f"Project: {project_name} | Evaluation Date: {eval_date_str}", merge_format)

        # Column widths
        for col_idx, col_name in enumerate(summary.columns):
            width = 50 if col_name.lower().startswith("improvement") else 20
            ws.set_column(col_idx, col_idx, width)

        # Radar chart (validated)
        can_chart = (("Domain" in summary.columns) and ("Score" in summary.columns) and (len(summary) > 0) and (summary["Score"].notna().any()))
        if can_chart:
            r0 = start_row + 1  # first data row
            r1 = r0 + len(summary) - 1
            c_domain = list(summary.columns).index("Domain")
            c_score  = list(summary.columns).index("Score")

            chart = workbook.add_chart({"type": "radar", "subtype": "filled"})
            chart.add_series({
                "name":       "Score",
                "categories": ["Summary", r0, c_domain, r1, c_domain],
                "values":     ["Summary", r0, c_score,  r1, c_score],
                "line":       {"width": 2.0, "color": "#1f4e79"},
                "fill":       {"color": "#8FAADC", "transparency": 20},
            })
            chart.set_style(18)
            chart.set_title({"name": "Domain Score Radar Chart"})
            chart.set_legend({"none": True})
            chart.set_y_axis({"min": 0, "max": 10, "major_unit": 2})

            ws.insert_chart(r1 + 5, 0, chart)
            ws.write(r1 + 21, 0, "RAICESP - PSPA Tool version 1.2")
        else:
            warn_fmt = workbook.add_format({"italic": True, "font_color": "#7f7f7f"})
            ws.write(start_row, 0, "No valid 'Domain'/'Score' data for radar chart.", warn_fmt)

        # Questions sheet
        if "Question" in qdf.columns and len(qdf) > 0:
            def _split_q(s):
                s = str(s or "")
                parts = s.split(" ", 1)
                return (parts[0], parts[1]) if len(parts) == 2 else (s, "")
            qnums, qtexts = zip(*qdf["Question"].apply(_split_q)) if len(qdf) else ([], [])
            qdf["Question Number"] = qnums
            qdf["Question Text"]   = qtexts
        else:
            qdf["Question Number"] = ""
            qdf["Question Text"]   = ""

        out = pd.DataFrame({
            "Domain":          qdf.get("Domain", ""),
            "Question Number": qdf.get("Question Number", ""),
            "Question":        qdf.get("Question Text", qdf.get("Question", "")),
            "Notes":           qdf.get("Notes", ""),
            "Score":           pd.to_numeric(qdf.get("Score", ""), errors="coerce"),
        })
        out.to_excel(writer, index=False, sheet_name="Questions")
        wsq = writer.sheets["Questions"]
        for ci, cname in enumerate(out.columns):
            wsq.set_column(ci, ci, 28 if cname=="Question" else (40 if cname=="Notes" else 18))

    buffer.seek(0)
    return buffer.getvalue()

# PDF helper (FPDF) con header/footer
class PSPAPDF(FPDF):
    def __init__(self, project_name):
        super().__init__()
        self.project_name = project_name

    def header(self):
        self.set_font("Arial", "", 9)
        self.set_text_color(80)
        self.cell(0, 8, _latin1(f"Project: {self.project_name}"), ln=True, align="L")
        self.cell(0, 6, _latin1(f"Date: {date.today()}"), ln=True, align="L")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100)
        self.cell(0, 10, f"RAICESP - PSPA Tool version 1.2 | Page {self.page_no()} of {{nb}}", 0, 0, "C")

def _latin1(s: str) -> str:
    try:
        return (s or "").encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        return str(s)

def pdf_add_safe_multicell(pdf, text, w=0, h=6, txt_color=(0,0,0), italic=False):
    pdf.set_text_color(*txt_color)
    style = "" if not italic else "I"
    pdf.set_font("Arial", style, 10 if italic else 11)
    pdf.multi_cell(w, h, _latin1(text))

# ================== UI HEADER ==================
st.set_page_config(page_title="PSPA Tool", layout="centered")
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
st.markdown(f"**Version 1.2 - {date.today().strftime('%d/%m/%Y')}**")
st.markdown("""
Welcome to the **PSPA Tool** (Version 1.2).  
This tool supports a structured evaluation of patient safety projects.  
It enables **identification of areas of improvement**, and **planning, tracking, and review** of improvement actions.
""")

# ================== PROJECT INFO ==================
project_name = st.text_input("Project Name", key="project_name")
project_objectives = st.text_area("🎯 Project Objectives", key="project_objectives")


# ================== PDF EXPORT ==================
if st.button("📄 Generate PDF"):
    pdf = PSPAPDF(project_name or "Project")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Summary
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 10, _latin1("Domain Scores"), ln=True)
    pdf.set_font("Arial", "", 11)
    for d, s in domain_scores.items():
        ranking = get_ranking(s)
        rgb = [int(ranking_colors[ranking].lstrip('#')[i:i+2], 16) for i in (0,2,4)]
        pdf.set_fill_color(*rgb)
        pdf.set_text_color(0,0,0)
        pdf.cell(0, 8, _latin1(f"{d} - {s:.1f}/10 ({ranking.upper()})"), ln=True, fill=True)

    # Lowest questions
    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, _latin1("Lowest Rated Questions"), ln=True)
    pdf.set_font("Arial", "", 11)
    for d, q in lowest_questions.items():
        pdf_add_safe_multicell(pdf, _latin1(f"{d}: {q}"), w=0, h=6, txt_color=(200,0,0), italic=False)

    # Improvement plan
    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, _latin1("Improvement Plan"), ln=True)

    for d in domain_scores.keys():
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(0,0,0)
        pdf.cell(0, 7, _latin1(d), ln=True)
        pdf.set_font("Arial", "I", 10)
        pdf_add_safe_multicell(pdf, f"• Action: {st.session_state.get(f'improve-{d}','')}", txt_color=(0,0,160), italic=True)
        pdf_add_safe_multicell(pdf, f"• Responsible: {st.session_state.get(f'resp-{d}','')}", txt_color=(0,0,160), italic=True)
        pdf_add_safe_multicell(pdf, f"• Review Date: {st.session_state.get(f'date-{d}', date.today())}", txt_color=(0,0,160), italic=True)
        pdf.ln(1)

    # Save PDF (Android friendly)
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name)
        tmp_pdf.seek(0)
        pdf_data = tmp_pdf.read()
    st.download_button("⬇️ Download PDF", pdf_data, file_name=f"{date.today()}_{project_name}_PSPA.pdf", mime="application/pdf")

# ================== EXCEL EXPORT ==================
excel_bytes = _build_excel_report(
    df_summary,
    pd.DataFrame(questions_data),
    project_name or "Project",
    date.today().isoformat()
)
st.download_button("📊 Download Excel", excel_bytes, file_name=f"{date.today()}_{project_name}_PSPA.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
