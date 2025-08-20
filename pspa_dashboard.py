
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
            wsq.set_column(ci, ci, 30 if cname in ("Question", "Notes") else 18)

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
project_name = st.text_input("Project Name")
project_objectives = st.text_area("🎯 Project Objectives")

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
    st.markdown("---")
    st.markdown(f"<h3 style='background-color:#003366; color:white; padding:8px; border-radius:6px;'>{domain}</h3>", unsafe_allow_html=True)
    scores = []
    min_score_local = 10
    for i, q in enumerate(qs, start=1):
        q_num = f"{domain.split('.')[0]}.{i}"
        st.markdown(f"<p><span style='color:#1a75ff; font-weight:bold;'>{q_num}</span> {q}</p>", unsafe_allow_html=True)
        note_key = f"note_{q_num}"
        score_key = f"slider_{q_num}"
        note_val = st.session_state.get(note_key, "")
        score_val = st.session_state.get(score_key, 5)
        notes = st.text_area("Notes", value=note_val, key=note_key)
        score = st.slider("Score (0-10)", 0, 10, value=score_val, key=score_key)
        scores.append(score)
        min_score_local = min(min_score_local, score)
        questions_data.append({"Domain": domain, "Question": f"{q_num} {q}", "Score": score, "Notes": notes})
    avg_score = round(float(np.mean(scores)), 1) if len(scores) else 0.0
    domain_scores[domain] = avg_score
    ranking = get_ranking(avg_score)
    min_questions = [f"{domain.split('.')[0]}.{i+1} {qs[i]}" for i, s in enumerate(scores) if s == min_score_local]
    lowest_questions[domain] = ", ".join(min_questions)

    # Improvement widgets per domain (keys to allow import)
    improve_key = f"improve-{domain}"
    resp_key    = f"resp-{domain}"
    date_key    = f"date-{domain}"
    st.session_state.setdefault(improve_key, "")
    st.session_state.setdefault(resp_key, "")
    st.session_state.setdefault(date_key, date.today())
    st.text_area(f"Improvement Action for {domain}", key=improve_key)
    st.text_input(f"Responsible for {domain}", key=resp_key)
    st.date_input(f"Review Date", value=st.session_state.get(date_key, date.today()), key=date_key)

# ================== SUMMARY TABLE ==================
st.subheader("Summary")
df_summary = pd.DataFrame({
    "Domain": list(domain_scores.keys()),
    "Score": [round(s, 1) for s in domain_scores.values()],
    "Lowest Questions": [lowest_questions[d] for d in domain_scores],
    "Improvement Action": [st.session_state.get(f"improve-{d}", "") for d in domain_scores],
    "Responsible": [st.session_state.get(f"resp-{d}", "") for d in domain_scores],
    "Review Date": [st.session_state.get(f"date-{d}", date.today()) for d in domain_scores]
})

def color_code(value):
    return f"background-color:{ranking_colors[get_ranking(value)]}; color:black"

def highlight_low_questions(val):
    return "color:#cc0000; font-weight:bold;" if isinstance(val, str) and val else ""

styled_summary = df_summary.style.applymap(color_code, subset=["Score"]).applymap(highlight_low_questions, subset=["Lowest Questions"])
st.dataframe(styled_summary, use_container_width=True)

# ================== RADAR (WEB) ==================
labels = list(domain_scores.keys())
if labels:
    values = list(domain_scores.values())
    values_c = values + [values[0]]
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist() + [0]
    fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
    ax.plot(angles, values_c, 'o-', linewidth=2)
    ax.fill(angles, values_c, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=8)
    ax.set_yticks(range(0, 11, 2))
    ax.set_title("Radar Chart", va='bottom')
    st.pyplot(fig)

# ================== IMPORT / EXPORT (JSON) ==================
with st.expander("📥 Import or Export Evaluation"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Export Evaluation"):
            eval_data = {
                "scores": {k: v for k, v in st.session_state.items() if k.startswith("slider_")},
                "notes":  {k: v for k, v in st.session_state.items() if k.startswith("note_")},
                "improvements": {d: st.session_state.get(f"improve-{d}", "") for d in domains.keys()},
                "responsible":  {d: st.session_state.get(f"resp-{d}", "") for d in domains.keys()},
                "review_date":  {d: str(st.session_state.get(f"date-{d}", date.today())) for d in domains.keys()}
            }
            json_data = json.dumps(eval_data, indent=2)
            st.download_button("Download JSON", json_data, file_name="evaluation_data.json", mime="application/json")
    with col2:
        uploaded_json = st.file_uploader("Upload previous evaluation (.json)", type="json", key="uploader_json")
        if uploaded_json is not None and not st.session_state.get("_import_done"):
            try:
                data = json.load(uploaded_json)
                # 1) CLEAR previous state
                for k in list(st.session_state.keys()):
                    if k.startswith("slider_") or k.startswith("note_") or k.startswith("improve-") or k.startswith("resp-") or k.startswith("date-"):
                        del st.session_state[k]
                # 2) LOAD state from JSON
                for k, v in data.get("scores", {}).items():
                    try:
                        st.session_state[k] = int(v)
                    except Exception:
                        st.session_state[k] = v
                for k, v in data.get("notes", {}).items():
                    st.session_state[k] = v
                for d, v in data.get("improvements", {}).items():
                    st.session_state[f"improve-{d}"] = v
                for d, v in data.get("responsible", {}).items():
                    st.session_state[f"resp-{d}"] = v
                for d, v in data.get("review_date", {}).items():
                    st.session_state[f"date-{d}"] = pd.to_datetime(v, errors='coerce').date() if v else date.today()
                st.session_state["_import_done"] = True
                st.success("Previous evaluation loaded.")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading file: {e}")

    st.markdown("---")
    if st.button("🧹 Clear all evaluation"):
        for k in list(st.session_state.keys()):
            if k.startswith("slider_") or k.startswith("note_") or k.startswith("improve-") or k.startswith("resp-") or k.startswith("date-") or k == "_import_done":
                del st.session_state[k]
        st.success("All evaluation fields cleared.")
        st.rerun()

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
