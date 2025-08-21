
import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
import json
import re

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
            ws.write(r1 + 35, 0, "RAICESP - PSPA Tool version 1.2")
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
        # Default widths
        for ci, cname in enumerate(out.columns):
            wsq.set_column(ci, ci, 18)
        # Keep "Notes" wide
        if "Notes" in out.columns:
            _idx_notes = list(out.columns).index("Notes")
            wsq.set_column(_idx_notes, _idx_notes, 40)
        # Auto-fit "Question" based on content length (bounded)
        if "Question" in out.columns:
            _idx_q = list(out.columns).index("Question")
            try:
                _q_max = int(out["Question"].astype(str).map(len).max() or 0)
            except Exception:
                _q_max = 28
            _q_width = max(28, min(80, _q_max + 5))
            wsq.set_column(_idx_q, _idx_q, _q_width)


    buffer.seek(0)
    return buffer.getvalue()

# PDF helper (FPDF) con header/footer
class PSPAPDF(FPDF):
    def __init__(self, project_name):
        super().__init__()
        self.project_name = project_name

    def header(self):
        self.set_font("Arial", "B", 11)
        self.set_text_color(0)
        self.cell(0, 8, _latin1("PATIENT SAFETY PROJECT ADEQUACY DASHBOARD"), ln=True, align="L")
        self.set_font("Arial", "", 9)
        self.set_text_color(80)
        self.cell(0, 8, _latin1(f"Project: {self.project_name}"), ln=True, align="L")
        self.cell(0, 6, _latin1(f"Date: {_dt.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align="L")
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



def _effective_width(pdf):
    return pdf.w - pdf.l_margin - pdf.r_margin

def _lines_for_text(pdf, text, size=11, style=""):
    # Approximate number of lines for given text at current width
    try:
        s = _latin1(text or "")
    except Exception:
        s = str(text or "")
    max_w = _effective_width(pdf)
    pdf.set_font("Arial", style, size)
    total_lines = 0
    for para in s.split("\n"):
        if para == "":
            total_lines += 1
            continue
        words = para.split(" ")
        line_w = 0.0
        lines_here = 1
        for w in words:
            ww = pdf.get_string_width(w + " ")
            if line_w + ww <= max_w:
                line_w += ww
            else:
                lines_here += 1
                line_w = ww
        total_lines += max(1, lines_here)
    return total_lines

def _estimate_domain_block_height(pdf, q_rows):
    # Domain title
    h = 8
    # Questions + optional notes
    for row in q_rows:
        qtxt = f"- {row.get('Question','')} : {row.get('Score','')}/10"
        h += _lines_for_text(pdf, qtxt, size=11, style="") * 6
        notes = row.get("Notes","")
        if notes:
            h += _lines_for_text(pdf, f"Notes: {notes}", size=10, style="I") * 6
        h += 1
    # small bottom margin
    return h + 6


def _pdf_ensure_space(pdf, needed_h=30):
    # If not enough vertical space, start a new page before printing the block
    remaining = pdf.h - pdf.b_margin - pdf.get_y()
    if remaining < needed_h:
        pdf.add_page()

def _estimate_block_height(q_count):
    # approx: domain title (8) + each question line (6) + notes line (6) + small gaps
    return 10 + q_count * 14 + 6


def pdf_add_safe_multicell(pdf, text, w=0, h=6, txt_color=(0,0,0), italic=False):
    pdf.set_text_color(*txt_color)
    style = "" if not italic else "I"
    pdf.set_font("Arial", style, 10 if italic else 11)
    pdf.multi_cell(w, h, _latin1(text))

def _build_pdf_report(project_name, domain_scores, lowest_questions, questions_data):
    # Build PDF and return bytes
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
    _pdf_ensure_space(pdf, 24)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, _latin1("Lowest Rated Questions"), ln=True)
    pdf.set_font("Arial", "", 11)
    for d, q in lowest_questions.items():
        _pdf_ensure_space(pdf, 12)
        pdf_add_safe_multicell(pdf, _latin1(f"{d}: {q}"), w=0, h=6, txt_color=(200,0,0), italic=False)

    # Improvement Action Plan (new page)
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, _latin1("Improvement Action Plan"), ln=True)

    for d in domain_scores.keys():
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(0,0,0)
        pdf.cell(0, 7, _latin1(d), ln=True)
        pdf.set_font("Arial", "I", 10)
        pdf_add_safe_multicell(pdf, _latin1(f"• Action: {st.session_state.get(f'improve-{d}','')}"), txt_color=(0,0,160), italic=True)
        pdf_add_safe_multicell(pdf, _latin1(f"• Responsible: {st.session_state.get(f'resp-{d}','')}"), txt_color=(0,0,160), italic=True)
        pdf_add_safe_multicell(pdf, _latin1(f"• Review Date: {st.session_state.get(f'date-{d}', date.today())}"), txt_color=(0,0,160), italic=True)
        pdf.ln(1)

    # Domain Details (new page)
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, _latin1("Domain Details"), ln=True)
    for d in domain_scores.keys():
        q_rows = [r for r in questions_data if r.get("Domain")==d]
        _pdf_ensure_space(pdf, _estimate_domain_block_height(pdf, q_rows) if ' _estimate_domain_block_height' in globals() else 30)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, _latin1(d), ln=True)
        pdf.set_font("Arial", "", 11)
        for row in q_rows:
            qtxt = f"- {row.get('Question','')} : {row.get('Score','')}/10"
            pdf_add_safe_multicell(pdf, _latin1(qtxt), w=0, h=6, txt_color=(0,0,0), italic=False)
            n = row.get("Notes","")
            if n:
                pdf_add_safe_multicell(pdf, _latin1(f"Notes: {n}"), w=0, h=6, txt_color=(0,0,160), italic=True)
        pdf.ln(1)

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        pdf.output(tmp_pdf.name)
        tmp_pdf.seek(0)
        pdf_data = tmp_pdf.read()
    return pdf_data

def _touch_state():
    st.session_state['_dirty'] = _dt.now().isoformat()

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
st.markdown(f"**Evaluation timestamp:** {_dt.now().strftime('%Y-%m-%d %H:%M')}")


# ================== DOMAINS/QUESTIONS ==================
domains = {
    "1. LEADERSHIP & GOVERNANCE": [
        "Are PS responsibilities clearly assigned?",
        "Is there a PS committee or team that meets regularly?",
        "Are there PS indicators being tracked?",
        "Is PS integrated into strategic planning?"
    ],
    "2. STAFFING, SKILLS & SAFETY CULTURE": [
        "Is there a shortage of critical staff?",
        "Do staff feel safe to report incidents?",
        "Are regular trainings on PS and IPC conducted?",
        "Do staff feel supported to raise concerns?"
    ],
    "3. BASELINE ASSESSMENT": [
        "Has a PS situation analysis been done?",
        "Have PS risks or gaps been identified and prioritized?",
        "Are baseline indicators available?",
        "Were patients or community consulted?"
    ],
    "4. INTERVENTION DESIGN": [
        "Were actions chosen based on evidence or data?",
        "Are responsibilities and timelines defined?",
        "Are patients or staff involved in designing improvements?",
        "Is it clear what change is expected and how to measure it?"
    ],
    "5. CHANGE MANAGEMENT & IMPLEMENTATION": [
        "Is there a team leading the changes?",
        "Are changes being piloted or tested before full rollout?",
        "Are there regular meetings to review progress?",
        "Is coaching or support provided to staff?"
    ],
    "6. MONITORING & MEASUREMENT": [
        "Are indicators or data collected regularly?",
        "Are data used to inform decisions or actions?",
        "Are feedback loops established with frontline staff?",
        "Is there disaggregated data for equity (e.g. gender)?"
    ],
    "7. SUSTAINABILITY & PARTNERSHIPS": [
        "Are changes being integrated into routines or policies?",
        "Is there external support (e.g. MoH, NGOs)?",
        "Is there capacity-building for sustainability?",
        "Are partnerships formalized or evaluated?"
    ]
}

st.header("Self-Assessment")
questions_data = []
domain_scores = {}
lowest_questions = {}

for domain, qs in domains.items():
    
    with col2:
        import hashlib
        uploaded_json = st.file_uploader("Upload previous evaluation (.json)", type="json", key="uploader_json")
        if uploaded_json is not None:
            try:
                content = uploaded_json.read()
                digest = hashlib.md5(content).hexdigest()
                if st.session_state.get("_import_digest") != digest and not st.session_state.get("_import_done"):
                    data = json.loads(content.decode("utf-8"))
                    # Clear previous state
                    for k in list(st.session_state.keys()):
                        if k.startswith(("slider_","note_","improve-","resp-","date-")) or k in ("project_name","project_objectives"):
                            del st.session_state[k]
                    # Load project fields
                    st.session_state["project_name"] = data.get("project_name","")
                    st.session_state["project_objectives"] = data.get("project_objectives","")
                    # Load scores and notes
                    for k, v in data.get("scores", {}).items():
                        try:
                            st.session_state[k] = int(v)
                        except Exception:
                            try:
                                st.session_state[k] = float(v)
                            except Exception:
                                st.session_state[k] = v
                    for k, v in data.get("notes", {}).items():
                        st.session_state[k] = v
                    # Load per-domain fields
                    for d, v in data.get("improvements", {}).items():
                        st.session_state[f"improve-{d}"] = v
                    for d, v in data.get("responsible", {}).items():
                        st.session_state[f"resp-{d}"] = v
                    for d, v in data.get("review_date", {}).items():
                        try:
                            st.session_state[f"date-{d}"] = pd.to_datetime(v, errors='coerce').date() if v else date.today()
                        except Exception:
                            st.session_state[f"date-{d}"] = date.today()
                    # Mark as imported and rerun once
                    st.session_state["_import_digest"] = digest
                    st.session_state["_import_done"] = True
                    st.success("Previous evaluation loaded.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")


# ================== PDF EXPORT ==================
from datetime import datetime as _dt
_ts = _dt.now().strftime('%Y%m%d_%H%M')
_slug = re.sub(r'[^A-Za-z0-9-]+','-', (project_name or 'Project')).strip('-')[:40] or 'Project'
st.download_button('⬇️ Download PDF', _build_pdf_report(project_name, domain_scores, lowest_questions, questions_data),
                 file_name=f'{_ts}_{_slug}_PSPA.pdf', mime='application/pdf')

# ================== EXCEL EXPORT ==================

# ================== CLEAR ALL (below reports) ==================
st.warning("⚠️ This will permanently clear *all* current inputs (scores, notes, Improvement Action Plans, responsibles, dates, project name & objectives). **Are you sure?** We strongly recommend exporting your responses first.", icon="⚠️")
if st.button("🧹 Clear all evaluation now"):
    for k in list(st.session_state.keys()):
        if k.startswith(("slider_","note_","improve-","resp-","date-")) or k in ("_import_done","_import_digest","project_name","project_objectives","_dirty"):
            del st.session_state[k]
    st.success("All evaluation fields cleared.")
    st.rerun()


excel_bytes = _build_excel_report(df_summary, pd.DataFrame(questions_data), project_name or "Project", _dt.now().strftime("%Y-%m-%d %H:%M"))
from datetime import datetime as _dt
_ts = _dt.now().strftime('%Y%m%d_%H%M')
_slug = re.sub(r'[^A-Za-z0-9-]+','-', (project_name or 'Project')).strip('-')[:40] or 'Project'
st.download_button('📊 Download Excel', excel_bytes, file_name=f'{_ts}_{_slug}_PSPA.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
