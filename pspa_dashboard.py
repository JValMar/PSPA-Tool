# File: pspa_dashboard.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import io, json, tempfile, os
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Ethiopia PS Checklist", layout="centered")
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")

# Project Objectives
project = st.sidebar.text_input("Enter Project Title:")
objectives = st.text_area("🎯 Project Objectives", "")
if not project:
    st.warning("⚠️ Please enter a project title in the sidebar to personalize your reports.")

# Description
st.markdown("""
**Version: 17/07/2025.** This is a draft proposal based on the keynote of this workshop and ideas from PS & QI tools. 
[https://bit.ly/raicesp](https://bit.ly/raicesp)

📘 **Checklist Description**
This checklist evaluates considerations required to advance patient safety (PS) at hospital level, ensuring alignment with international standards while adapting to local realities.
""")

# Domain Questions
domain_questions = {
    "1. Leadership & Governance": [
        "Are PS responsibilities clearly assigned?",
        "Is there a PS committee or team that meets regularly?",
        "Are there PS indicators being tracked?",
        "Is PS integrated into strategic planning?"
    ],
    "2. Staffing, Skills & Safety Culture": [
        "Is there a shortage of critical staff?",
        "Do staff feel safe to report incidents?",
        "Are regular trainings on PS and IPC conducted?",
        "Do staff feel supported to raise concerns?"
    ],
    "3. Baseline Assessment": [
        "Has a PS situation analysis been done?",
        "Have PS risks or gaps been identified and prioritized?",
        "Are baseline indicators available?",
        "Were patients or community consulted?"
    ],
    "4. Intervention Design": [
        "Were actions chosen based on evidence or data?",
        "Are responsibilities and timelines defined?",
        "Are patients or staff involved in designing improvements?",
        "Is it clear what change is expected and how to measure it?"
    ],
    "5. Change Management & Implementation": [
        "Is there a team leading the changes?",
        "Are changes being piloted or tested before full rollout?",
        "Are there regular meetings to review progress?",
        "Is coaching or support provided to staff?"
    ],
    "6. Monitoring & Measurement": [
        "Are indicators or data collected regularly?",
        "Are data used to inform decisions or actions?",
        "Are feedback loops established with frontline staff?",
        "Is there disaggregated data for equity (e.g. gender)?"
    ],
    "7. Sustainability & Partnerships": [
        "Are changes being integrated into routines or policies?",
        "Is there external support (e.g. MoH, NGOs)?",
        "Is there capacity-building for sustainability?",
        "Are partnerships formalized or evaluated?"
    ]
}

# Helper function
def next_monday_after_3_months():
    base = date.today() + timedelta(days=90)
    return base + timedelta(days=(7 - base.weekday()) % 7)

# Data collections
domain_scores, notes, responsible, review_dates, lowest_questions = {}, {}, {}, {}, {}

st.header("📌 Self-Assessment by Domain")

for domain, questions in domain_questions.items():
    st.subheader(domain)
    scores = []
    for q in questions:
        st.text_area(f"📝 Notes for: {q}", key=f"notes-{domain}-{q}")
        score = st.slider(q, 0, 10, 5, key=f"{domain}-{q}")
        scores.append(score)
    avg_score = round(np.mean(scores), 2)
    domain_scores[domain] = avg_score
    lowest_q = questions[np.argmin(scores)]
    lowest_questions[domain] = lowest_q
    st.caption(f"Lowest scored question: {lowest_q}")
    notes[domain] = st.text_area(f"✏️ Improvement Measures for {domain}", "")
    responsible[domain] = st.text_input(f"👤 Responsible for {domain}", "")
    review_dates[domain] = next_monday_after_3_months()

# General observations
general_observations = st.text_area("📌 General Observations", "")

# DataFrame
score_df = pd.DataFrame({
    "Checklist Dimension": list(domain_scores.keys()),
    "Score": list(domain_scores.values()),
    "Lowest Scored Question": [lowest_questions[d] for d in domain_scores.keys()],
    "Improvement Measures": [notes[d] for d in domain_scores.keys()],
    "Responsible": [responsible[d] for d in domain_scores.keys()],
    "Review Date": [review_dates[d] for d in domain_scores.keys()]
})

# Radar Chart
labels = list(domain_scores.keys())
scores = list(domain_scores.values())
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
scores += scores[:1]
angles += angles[:1]
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, scores, 'o-', linewidth=2)
ax.fill(angles, scores, alpha=0.25)
ax.set_yticks(range(0, 11, 2))
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, size=8)
ax.set_title("Patient Safety Project Radar", va='bottom')
img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png')
img_buffer.seek(0)

# Summary with bar chart
st.subheader("Summary of Lowest Rated Questions")
for d, q in lowest_questions.items():
    st.markdown(f"**{d}:** {q} (Score: {domain_scores[d]})")

bar_fig, bar_ax = plt.subplots(figsize=(8, 4))
colors = ['green' if s >= 8 else 'orange' if s >= 4 else 'red' for s in domain_scores.values()]
bar_ax.bar(domain_scores.keys(), domain_scores.values(), color=colors)
bar_ax.set_ylim(0, 10)
bar_ax.set_ylabel('Score')
bar_ax.set_title('Domain Scores Overview')
plt.xticks(rotation=45, ha='right')
for i, v in enumerate(domain_scores.values()):
    bar_ax.text(i, v + 0.2, str(v), ha='center')
st.pyplot(bar_fig)

# PDF Report
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "PATIENT SAFETY PROJECT ADEQUACY DASHBOARD", 0, 1, 'C')
        self.set_font('Arial', '', 11)
        self.cell(0, 10, f"Project: {project}", 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Page {self.page_no()} of {{nb}}", 0, 0, 'C')
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 8, title, 0, 1, 'L')
    def chapter_body(self, body):
        self.set_font('Arial', '', 9)
        self.multi_cell(0, 6, body)
        self.ln()

pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, "Objectives:", ln=1)
pdf.set_font('Arial', '', 9)
pdf.multi_cell(0, 6, objectives)
pdf.ln(5)

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, "Summary of Scores by Dimension:", ln=1)
for _, row in score_df.iterrows():
    pdf.cell(0, 6, f"{row['Checklist Dimension']:<30} {row['Score']}/10", ln=1)

pdf.ln(5)
for _, row in score_df.iterrows():
    body = (f"Score: {row['Score']}\nLowest Scored Question: {row['Lowest Scored Question']}\n"
            f"Improvement Measures: {row['Improvement Measures']}\nResponsible: {row['Responsible']}\n"
            f"Review Date: {row['Review Date']}")
    pdf.chapter_title(row['Checklist Dimension'])
    pdf.chapter_body(body)

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, "General Observations:", ln=1)
pdf.set_font('Arial', '', 9)
pdf.multi_cell(0, 6, general_observations)

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
    pdf.output(tmp_pdf.name)
    tmp_pdf_path = tmp_pdf.name
with open(tmp_pdf_path, "rb") as f:
    pdf_data = f.read()
os.unlink(tmp_pdf_path)

# Excel Export
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    score_df.to_excel(writer, index=False, sheet_name='Scores')
    worksheet = writer.sheets['Scores']
    for col_num, value in enumerate(score_df.columns.values):
        col_len = max(score_df[value].astype(str).map(len).max(), len(value)) + 2
        worksheet.set_column(col_num, col_num, col_len)
    worksheet.insert_image('H2', 'radar.png', {'image_data': img_buffer})

# Download buttons
st.download_button(
    label="📊 Download Excel (.xlsx)",
    data=excel_buffer.getvalue(),
    file_name=f'{eval_date.strftime("%Y-%m-%d")}_PSPA_report_{project.replace(" ", "_")}.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

st.download_button(
    label="📄 Download Report (.pdf)",
    data=pdf_data,
    file_name=f'{eval_date.strftime("%Y-%m-%d")}_PSPA_report_{project.replace(" ", "_")}.pdf',
    mime='application/pdf'
)

st.success("✅ Evaluation complete. Reports ready for download.")

st.markdown("💬 **Thank you for using this tool.** Suggestions: [https://bit.ly/raicesp](https://bit.ly/raicesp)")
