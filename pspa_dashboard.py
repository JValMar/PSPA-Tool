
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
st.markdown("**Version: 22/07/2025**")
st.markdown("Welcome to the **PSPA Tool**, designed to evaluate patient safety projects and generate PDF/Excel reports.")

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

st.header("Self-Assessment")
for domain, qs in domains.items():
    st.subheader(domain)
    scores = []
    for i, q in enumerate(qs, start=1):
        q_num = f"{domain.split('.')[0]}.{i}"
        st.markdown(f"**{q_num} {q}**")
        notes = st.text_area(f"Notes for {q}", key=f"notes-{domain}-{i}")
        score = st.slider("Score (0-10)", 0, 10, 5, key=f"{domain}-{i}")
        scores.append(score)
        questions_data.append({"Domain": domain, "Question": f"{q_num} {q}", "Score": score, "Notes": notes})
    avg_score = round(np.mean(scores), 1)
    domain_scores[domain] = avg_score
    min_score = min(scores)
    lowest_qs = [f"{domain.split('.')[0]}.{i+1} {qs[i]}" for i, s in enumerate(scores) if s == min_score]
    lowest_questions[domain] = ", ".join(lowest_qs)
    st.markdown(f"**Domain Score:** {avg_score:.1f}/10")
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
st.dataframe(df_summary)

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
    pdf.multi_cell(0, 8, f"{domain}: {domain_scores[domain]:.1f}/10\nLowest: {lowest_questions[domain]}\nImprovement: {improvements[domain]}\nResponsible: {responsible[domain]} | Review Date: {review_date[domain]}\n")
pdf.set_y(-20)
pdf.set_font("Arial", 'I', 8)
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
