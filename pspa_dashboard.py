
import streamlit as st
import pandas as pd
from datetime import date
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

# ----------- Introduction -----------
st.title("Welcome to the PSPA Dashboard")
st.markdown(
    """
    ### About this Tool
    The **Patient Safety Project Adequacy (PSPA) Dashboard** helps healthcare teams 
    evaluate the readiness and comprehensiveness of their patient safety projects.  
    It allows structured self-assessment across key domains, provides visual feedback, 
    and generates PDF reports to track progress and identify areas for improvement.
    """)

st.markdown("**Version: 22/07/2025**")

# ----------- Project Information -----------
project_name = st.text_input("Project Name")
project_objectives = st.text_area("🎯 Project Objectives")

# ----------- Domains and Questions -----------
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

# ----------- Self-Assessment -----------
domain_scores = {}
lowest_questions = {}

st.header("Self-Assessment by Domain")
for domain, questions in base_domain_questions.items():
    st.subheader(domain)
    scores = []
    for i, q in enumerate(questions, start=1):
        st.markdown(f"**{domain.split('.')[0]}.{i} {q}**")
        score = st.slider(f"Score (0-10)", 0, 10, 5, key=f"{domain}-{i}")
        scores.append(score)
    avg_score = round(np.mean(scores), 2)
    domain_scores[domain] = avg_score
    lowest_questions[domain] = questions[np.argmin(scores)]
    st.markdown(f"**Domain Score:** {avg_score}/10")
    st.caption(f"Lowest scored question: {lowest_questions[domain]}")

# ----------- Summary -----------
st.subheader("Final Summary")
df_summary = pd.DataFrame({
    "Domain": list(domain_scores.keys()),
    "Score": list(domain_scores.values()),
    "Lowest Question": [lowest_questions[d] for d in domain_scores]
})
st.dataframe(df_summary)

# ----------- Radar Chart -----------
labels = list(domain_scores.keys())
scores_list = list(domain_scores.values())
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
scores_list += scores_list[:1]
angles += angles[:1]
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.plot(angles, scores_list, 'o-', linewidth=2)
ax.fill(angles, scores_list, alpha=0.25)
ax.set_yticks(range(0, 11, 2))
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, size=8)
ax.set_title("Patient Safety Project Radar", va='bottom')
st.pyplot(fig)

# ----------- PDF Export -----------
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 14)
pdf.cell(0, 10, "Patient Safety Project Adequacy Report", ln=True, align="C")
pdf.set_font("Arial", '', 12)
pdf.multi_cell(0, 10, f"Project: {project_name}\nObjectives: {project_objectives}\n")
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Summary of Scores by Domain:", ln=True)
for domain in domain_scores:
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"{domain}: {domain_scores[domain]}/10 | Lowest: {lowest_questions[domain]}", ln=True)

pdf_data = pdf.output(dest='S').encode('latin-1')

st.download_button("📄 Download PDF Report", pdf_data,
                   file_name=f"{date.today()}_{project_name.replace(' ', '_')}_PSPA_Report.pdf",
                   mime="application/pdf")
