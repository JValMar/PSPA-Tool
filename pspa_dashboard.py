
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

# === HEADER ===
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
st.markdown("**Version 1.1 - 27/07/2025**")
st.markdown(
    "Welcome to the **PSPA Tool**. This tool helps you evaluate patient safety projects, "
    "identify areas of improvement, and plan and track improvement actions with subsequent project reviews. "
    "You can generate professional PDF and Excel reports with visual analytics."
)

# === PROJECT INFO ===
project_name = st.text_input("Project Name")
project_objectives = st.text_area("🎯 Project Objectives")

# === QUESTIONS & DOMAINS ===
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

domain_scores, lowest_questions, improvements, responsible, review_date = {}, {}, {}, {}, {}
questions_data = []

def get_ranking(score):
    if score < 2: return "Very Low"
    elif score < 4: return "Low"
    elif score < 6: return "Average"
    elif score < 8: return "High"
    else: return "Very High"

ranking_colors = {
    "Very Low": "#ff9999",
    "Low": "#ffd699",
    "Average": "#ffff99",
    "High": "#ccffcc",
    "Very High": "#cce0ff"
}

# === SELF-ASSESSMENT ===
st.header("Self-Assessment")
for domain, qs in domains.items():
    scores = []
    min_score_local = 10
    st.markdown("---", unsafe_allow_html=True)
    st.markdown(f"<h3 style='background-color:#003366; color:white; padding:8px; border-radius:6px; margin-top:12px;'>{domain}</h3>", unsafe_allow_html=True)
    for i, q in enumerate(qs, start=1):
        q_num = f"{domain.split('.')[0]}.{i}"
        color_q_num = '#1a75ff'
        st.markdown(f"<p><span style='color:{color_q_num}; font-weight:bold;'>{q_num}</span> {q}</p>", unsafe_allow_html=True)
        notes = st.text_area(f"Notes for {q}", key=f"notes-{domain}-{i}")
        score = st.slider(f"Score (0-10)", 0, 10, 5, key=f"{domain}-{i}")
        # Color numeración y texto si es la más baja
        color_q_num = "#1a75ff"
        color_q_text = "black"
        scores.append(score)
        min_score_local = min(min_score_local, score)
        questions_data.append({"Domain": domain, "Question": f"{q_num} {q}", "Score": score, "Notes": notes})
        color_q_num = '#1a75ff'
        st.markdown(f"<p><span style='color:{color_q_num}; font-weight:bold;'>{q_num}</span> {q}</p>", unsafe_allow_html=True)
    avg_score = round(np.mean(scores), 1)
    domain_scores[domain] = avg_score
    ranking = get_ranking(avg_score)
    min_questions = [f"{domain.split('.')[0]}.{i+1} {qs[i]}" for i, s in enumerate(scores) if s == min_score_local]
    lowest_questions[domain] = ", ".join(min_questions)
    st.markdown(f"<div style='background-color:{ranking_colors[ranking]}; padding:4px; border-radius:4px;'>"
                f"<b>Domain Score:</b> {avg_score:.1f}/10 - {ranking}</div>", unsafe_allow_html=True)
    st.markdown(f"<p><span style='color:#1a75ff; font-weight:bold;'>Lowest Question(s):</span> "
                f"<span style='color:#800000;'>{lowest_questions[domain]}</span></p>", unsafe_allow_html=True)
    improvements[domain] = st.text_area(f"Improvement Action for {domain}", key=f"improve-{domain}")
    responsible[domain] = st.text_input(f"Responsible for {domain}", key=f"resp-{domain}")
    review_date[domain] = st.date_input(f"Review Date", value=date.today() + timedelta(days=90), key=f"date-{domain}")

# === SUMMARY ===
st.subheader("Summary")
df_summary = pd.DataFrame({
    "Domain": list(domain_scores.keys()),
    "Score": [round(s, 1) for s in domain_scores.values()],
    "Lowest Questions": [lowest_questions[d] for d in domain_scores],
    "Improvement Action": [improvements[d] for d in domain_scores],
    "Responsible": [responsible[d] for d in domain_scores],
    "Review Date": [review_date[d] for d in domain_scores]
})

def color_code(value):
    return f"background-color:{ranking_colors[get_ranking(value)]}; color:black"

def highlight_low_questions(val):
    # Color azul para número, rojo oscuro para texto
    if val and isinstance(val, str):
        parts = val.split(" ", 1)
        if len(parts) > 1:
            return "font-weight:bold; color:#800000"
        return "color:#1a75ff; font-weight:bold"
    return ""

styled_summary = df_summary.style.applymap(color_code, subset=["Score"]).applymap(highlight_low_questions, subset=["Lowest Questions"])
st.dataframe(styled_summary)

# === RADAR CHART ===
labels = list(domain_scores.keys())
scores_list = list(domain_scores.values()) + [list(domain_scores.values())[0]]
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist() + [0]
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, scores_list, 'o-', linewidth=2)
ax.fill(angles, scores_list, alpha=0.25)
ax.set_yticks(range(0, 11, 2))
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, size=8)
ax.set_title("Radar Chart", va='bottom')
img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png')
img_buffer.seek(0)
st.pyplot(fig)

# === PDF EXPORT ===
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 14)
pdf.cell(0, 10, "Patient Safety Project Adequacy Report", ln=True, align="C")
pdf.set_font("Arial", '', 12)
pdf.multi_cell(0, 10, f"Project: {project_name}\nObjectives: {project_objectives}\nDate: {date.today()}\n")
with open("radar_chart.png", "wb") as f: f.write(img_buffer.getvalue())
pdf.image("radar_chart.png", x=40, w=130)
pdf.ln(85)
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Summary of Domains", ln=True)
pdf.set_font("Arial", '', 11)
for domain in domain_scores:
    pdf.multi_cell(0, 8,
        f"{domain}: {domain_scores[domain]:.1f}/10 - {get_ranking(domain_scores[domain])}\n"
        f"Lowest Question(s): {lowest_questions[domain]}\n"
        f"Improvement Action: {improvements[domain]}\n"
        f"Responsible: {responsible[domain]} | Review Date: {review_date[domain]}\n"
    )
pdf.add_page()
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Detailed Questions and Notes", ln=True)
pdf.set_font("Arial", '', 10)
for row in questions_data:
    min_local = min([q['Score'] for q in questions_data if q['Domain'] == row['Domain']])
    pdf.set_text_color(255, 0, 0) if row['Score'] == min_local else pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, f"{row['Question']} | Score: {row['Score']:.1f}\nNotes: {row['Notes']}\n")
pdf.set_y(-20)
pdf.set_font("Arial", 'I', 8)
pdf.set_text_color(0, 0, 0)
pdf.multi_cell(0, 8, f"Downloaded on {datetime.now().strftime('%Y-%m-%d %H:%M')}\nSuggestions: https://bit.ly/raicesp")
pdf_data = pdf.output(dest='S').encode('latin-1')
st.download_button("📄 Download PDF", pdf_data, file_name=f"{date.today()}_{project_name}_PSPA.pdf", mime="application/pdf")

# === EXCEL EXPORT ===
excel_buffer = io.BytesIO()
df_questions = pd.DataFrame(questions_data)
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df_summary.to_excel(writer, index=False, sheet_name='Summary')
    df_questions.to_excel(writer, index=False, sheet_name='Questions')
    ws = writer.sheets['Summary']
    for i, col in enumerate(df_summary.columns):
        col_width = max(df_summary[col].astype(str).map(len).max(), len(col)) + 2
        ws.set_column(i, i, col_width)
    ws.insert_image('H2', 'radar_chart.png', {'image_data': img_buffer})
st.download_button("📊 Download Excel", excel_buffer.getvalue(), file_name=f"{date.today()}_{project_name}_PSPA.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === FOOTER ===
st.markdown("---")
st.info("💬 **Thank you for using PSPA Tool. Share suggestions at [https://bit.ly/raicesp](https://bit.ly/raicesp)**")
