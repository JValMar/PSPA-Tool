# File: pspa_dashboard.py

import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import io, tempfile, os
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Ethiopia PS Checklist", layout="centered")
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")

# Project Objectives
project = st.sidebar.text_input("Enter Project Title:")
objectives = st.text_area("🎯 PROJECT OBJECTIVES", "")
if not project:
    project = "Unnamed Project"
    st.warning("⚠️ Please enter a project title in the sidebar to personalize your reports.")

# Description
st.markdown("""
**Version: 17/07/2025.** Draft proposal based on the keynote of this workshop and ideas from PS & QI tools. 
[https://bit.ly/raicesp](https://bit.ly/raicesp)

📘 **Checklist Description**
Evaluates considerations required to advance patient safety (PS) at hospital level.
""")

# Domain Questions
base_domain_questions = {
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

# Number questions
domain_questions = {}
for domain, questions in base_domain_questions.items():
    prefix = domain.split(".")[0]
    numbered_questions = [f"{prefix}.{i+1} {q}" for i, q in enumerate(questions)]
    domain_questions[domain] = numbered_questions

# Helper function
def next_monday_after_3_months():
    base = date.today() + timedelta(days=90)
    return base + timedelta(days=(7 - base.weekday()) % 7)

# Data collections
domain_scores, notes, responsible, review_dates, lowest_questions = {}, {}, {}, {}, {}

st.header("📌 SELF-ASSESSMENT BY DOMAIN")

for domain, questions in domain_questions.items():
    st.subheader(domain)
    scores = []
    for q in questions:
        st.text_area(q, key=f"notes-{domain}-{q}")
        st.markdown("Score the situation regarding this question from 0 (minimum) to 10 (maximum):")
        score = st.slider("", 0, 10, 5, key=f"{domain}-{q}")
        scores.append(score)
    avg_score = round(np.mean(scores), 2)
    domain_scores[domain] = avg_score
    lowest_q = questions[np.argmin(scores)]
    lowest_questions[domain] = lowest_q
    st.caption(f"Lowest scored question: {lowest_q}")
    notes[domain] = st.text_area(f"✏️ Improvement Measures for {domain}", "")
    responsible[domain] = st.text_input(f"👤 Responsible for {domain}", "")
    review_dates[domain] = next_monday_after_3_months()
    st.text(f"Review date: {review_dates[domain]}")

# General observations
general_observations = st.text_area("📌 GENERAL OBSERVATIONS", "")

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

# Summary
st.subheader("FINAL SUMMARY (ALL 7 DOMAINS)")
st.dataframe(score_df)

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

# PDF Report with all details
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "PATIENT SAFETY PROJECT ADEQUACY DASHBOARD", 0, 1, 'C')
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
    pdf.cell(0, 6, f"{row['Checklist Dimension']:<35} {row['Score']}/10 | Review: {row['Review Date']}", ln=1)

pdf.ln(5)
for _, row in score_df.iterrows():
    pdf.chapter_title(row['Checklist Dimension'])
    body = (f"Score: {row['Score']}\nLowest Scored Question: {row['Lowest Scored Question']}\n"
            f"Improvement Measures: {row['Improvement Measures']}\nResponsible: {row['Responsible']}\n"
            f"Review Date: {row['Review Date']}")
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

# Excel Export with radar chart
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    score_df.to_excel(writer, index=False, sheet_name='Scores')
    worksheet = writer.sheets['Scores']
    for col_num, value in enumerate(score_df.columns.values):
        worksheet.set_column(col_num, col_num, 25)
    worksheet.insert_image('H2', 'radar.png', {'image_data': img_buffer})

# Download buttons
st.download_button(
    label="📊 Download Excel (.xlsx)",
    data=excel_buffer.getvalue(),
    file_name=f"{date.today()}_PSPA_report_{project.replace(' ', '_')}.xlsx",
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

st.download_button(
    label="📄 Download Report (.pdf)",
    data=pdf_data,
    file_name=f"{date.today()}_PSPA_report_{project.replace(' ', '_')}.pdf",
    mime='application/pdf'
)

st.success("✅ Evaluation complete. Reports ready for download.")
