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
objectives = st.text_area("🎯 Project Objectives", "")
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

st.header("📌 Self-Assessment by Domain")

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

# Add numbered questions to Excel sheet
all_questions = []
for domain, questions in domain_questions.items():
    for q in questions:
        all_questions.append({"Domain": domain, "Question": q})
questions_df = pd.DataFrame(all_questions)

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
    st.markdown(f"**{d}:** **{q}** (Score: {domain_scores[d]})")

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

# PDF Report with background for lowest questions
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
    def chapter_body(self, body, highlight=False):
        if highlight:
            self.set_fill_color(230, 230, 230)
            self.multi_cell(0, 6, body, fill=True)
        else:
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
pdf.cell(0, 8, "Lowest Rated Questions Summary:", ln=1)
pdf.set_font('Arial', '', 9)
for d, q in lowest_questions.items():
    pdf.chapter_body(f"{d}: {q} (Score: {domain_scores[d]})", highlight=True)

# Include numbered questions in PDF
pdf.ln(5)
for domain, questions in domain_questions.items():
    pdf.chapter_title(domain)
    for q in questions:
        pdf.chapter_body(q)

# Excel Export with highlight for lowest questions
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    score_df.to_excel(writer, index=False, sheet_name='Scores')
    questions_df.to_excel(writer, index=False, sheet_name='Questions')
    worksheet = writer.sheets['Scores']
    highlight_format = writer.book.add_format({'bg_color': '#D9D9D9'})
    for idx, q in enumerate(score_df['Lowest Scored Question'], start=2):
        worksheet.write(f'C{idx}', q, highlight_format)

# Download buttons
st.download_button(
    label="📊 Download Excel (.xlsx)",
    data=excel_buffer.getvalue(),
    file_name=f"{date.today()}_PSPA_report_{project.replace(' ', '_')}.xlsx",
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

st.success("✅ Evaluation complete. Reports ready for download.")
