# Ethiopia Patient Safety Checklist Dashboard (Final PDF Fix for Mobile & Desktop)

import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os

st.set_page_config(page_title="Ethiopia PS Checklist", layout="centered")
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")

st.markdown("**Version: 17/07/2025.** This is a draft proposal, based on the keynote of this workshop and some ideas from PS & QI tools. Please, feel free to suggest any issues to clarify or complete this checklist: jvmartin@us.es")
st.markdown("""
📘 **Checklist Description**

This checklist evaluates the comprehensive considerations required to advance patient safety (PS) at the hospital level, ensuring alignment with international standards while adapting to local realities.

**NOTE:** Regularly review progress with this checklist, adapting as new challenges and opportunities arise, and ensure culturally sensitive, locally driven, and sustainable improvement.
""")

# Sidebar: Project and Date
st.sidebar.header("Project Information")
project = st.sidebar.text_input("Enter Project Title:")
if not project:
    st.warning("⚠️ Please enter a project title in the sidebar to personalize your reports.")
project = project.replace('–', '-')
eval_date = st.sidebar.date_input("Date of Evaluation:", date.today())

st.sidebar.markdown("---")
st.sidebar.info("For each domain, respond to multiple evaluation questions (0–10 scale). A summary and recommendations will be generated.")

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

# Input Collection
domain_scores = {}
review_dates = {}
notes = {}

st.header("📌 Self-Assessment by Domain")

for domain, questions in domain_questions.items():
    st.markdown(f"### {domain}")
    scores = []
    for q in questions:
        score = st.slider(q, 0, 10, 5, key=f"{domain}-{q}")
        scores.append(score)
    avg_score = round(np.mean(scores), 2)
    domain_scores[domain] = avg_score

    # Color-coded feedback
    if avg_score >= 8:
        st.markdown(':green[Excellent domain score]')
    elif avg_score >= 6:
        st.markdown(':orange[Moderate domain score]')
    elif avg_score >= 4:
        st.markdown(':orange[Low domain score]')
    else:
        st.markdown(':red[Critical domain score]')

    lowest_index = scores.index(min(scores))
    lowest_q = questions[lowest_index]
    st.caption(f"Lowest scored question: {lowest_q}")
    notes[domain] = st.text_area(f"✏️ Improvement Measures for {domain}", "")
    review_dates[domain] = st.date_input(f"📅 Review Date for {domain}", date.today() + timedelta(days=90))

score_df = pd.DataFrame({
    "Checklist Dimension": list(domain_scores.keys()),
    "Score": list(domain_scores.values()),
    "Lowest Scored Question": [
        domain_questions[dim][0] if dim not in notes else notes[dim] for dim in domain_scores.keys()
    ],
    "Improvement Measures": [notes[dim] for dim in domain_scores.keys()],
    "Review Date": [review_dates[dim] for dim in domain_scores.keys()]
})

# Radar Chart Generation
labels = list(domain_scores.keys())
scores = list(domain_scores.values())
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
scores += scores[:1]
angles += angles[:1]

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, scores, 'o-', linewidth=2)
ax.fill(angles, scores, alpha=0.25)
ax.set_yticks(range(0, 11, 2))
ax.set_yticklabels(map(str, range(0, 11, 2)))
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, size=8)
ax.set_title("Patient Safety Project Radar", va='bottom')

img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png')
img_buffer.seek(0)

# Export Excel Logic
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    score_df.to_excel(writer, index=False, sheet_name='Scores')
    workbook = writer.book
    worksheet = writer.sheets['Scores']

    # Auto-fit columns
    for col_num, value in enumerate(score_df.columns.values):
        column_len = max(
            score_df[value].astype(str).map(len).max(),
            len(value)
        ) + 2
        worksheet.set_column(col_num, col_num, column_len)

    # Insert radar chart
    worksheet.insert_image('H2', 'radar.png', {'image_data': img_buffer})

("Summary of Domain Scores")
for domain, score in domain_scores.items():
    if score >= 8:
        st.markdown(f"**{domain}:** :green[{score}/10 - Excellent]")
    elif score >= 6:
        st.markdown(f"**{domain}:** :orange[{score}/10 - Moderate]")
    elif score >= 4:
        st.markdown(f"**{domain}:** :orange[{score}/10 - Low]")
    else:
        st.markdown(f"**{domain}:** :red[{score}/10 - Critical]")
    lowest_question = 'No question answered' if not domain_questions.get(domain) else domain_questions[domain][0]
    st.caption(f"Lowest scored question: {notes[domain] if notes[domain] else lowest_question}")

# Bar chart of domain scores with color coding
colors = []
for score in domain_scores.values():
    if score >= 8:
        colors.append('green')
    elif score >= 6:
        colors.append('orange')
    elif score >= 4:
        colors.append('darkorange')
    else:
        colors.append('red')

bar_fig, bar_ax = plt.subplots(figsize=(8, 4))
bars = bar_ax.bar(domain_scores.keys(), domain_scores.values(), color=colors)

# Add value labels on top of bars
for bar, val in zip(bars, domain_scores.values()):
    bar_ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f'{val}', ha='center', va='bottom', fontsize=8)
bar_ax.set_ylim(0, 10)
bar_ax.set_ylabel('Score')
bar_ax.set_title('Domain Scores Overview')
plt.xticks(rotation=45, ha='right')
st.pyplot(bar_fig)

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

st.markdown("💬 **Thank you for using this tool.** Please help us improve it by sharing your comments and suggestions: [https://bit.ly/raicesp](https://bit.ly/raicesp)")
