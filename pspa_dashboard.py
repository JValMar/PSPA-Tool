
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

# --- Header ---
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
st.markdown("**Version: 22/07/2025**")

st.markdown(
    """
    Welcome to the **Patient Safety Project Adequacy (PSPA) Dashboard**.

    This tool helps healthcare teams evaluate patient safety projects, 
    identify improvement areas, and generate detailed PDF and Excel reports.
    """
)

# --- Project Information ---
project_name = st.text_input("Project Name")
project_objectives = st.text_area("🎯 Project Objectives")

# --- Domains and Questions ---
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

domain_scores = {}
lowest_questions = {}
improvement_measures = {}
responsible = {}
review_date = {}
questions_data = []

st.header("Self-Assessment by Domain")
for domain, questions in base_domain_questions.items():
    st.markdown(f"<h3 style='color:#1a73e8;'>{domain}</h3>", unsafe_allow_html=True)
    scores = []
    for i, q in enumerate(questions, start=1):
        question_num = f"{domain.split('.')[0]}.{i}"
        st.markdown(f"**{question_num} {q}**")
        note = st.text_area(f"Notes for {q}", key=f"notes-{domain}-{i}")
        score = st.slider(f"Score this question (0-10)", 0, 10, 5, key=f"{domain}-{i}")
        scores.append(score)
        questions_data.append({
            "Domain": domain,
            "Question": f"{question_num} {q}",
            "Notes": note,
            "Score": score
        })
    avg_score = round(np.mean(scores), 1)
    domain_scores[domain] = avg_score
    lowest_questions[domain] = questions[np.argmin(scores)]
    st.markdown(f"**Domain Score:** {avg_score:.1f}/10")
    if avg_score < 2:
        grade = 'Very Low'; color = 'red'
    elif avg_score < 4:
        grade = 'Low'; color = 'orange'
    elif avg_score < 6:
        grade = 'Average'; color = 'yellow'
    elif avg_score < 8:
        grade = 'High'; color = 'lightgreen'
    else:
        grade = 'Excellent'; color = 'green'
    st.markdown(f"<p style='color:{color}; font-weight:bold;'>Domain Score Rank: {grade}</p>", unsafe_allow_html=True)
    st.caption(f"Lowest scored question: {lowest_questions[domain]}")
    improvement_measures[domain] = st.text_area(f"Improvement Measures for {domain}", key=f"improve-{domain}")
    responsible[domain] = st.text_input(f"Responsible for {domain}", key=f"resp-{domain}")
    review_date[domain] = st.date_input(f"Review Date for {domain}", value=date.today() + timedelta(days=90), key=f"date-{domain}")

# --- Final Summary ---
st.subheader("Final Summary")
df_summary = pd.DataFrame({
    "Domain": list(domain_scores.keys()),
    "Score": [round(s, 1) for s in domain_scores.values()],
    "Lowest Question": [lowest_questions[d] for d in domain_scores],
    "Improvement Action": [improvement_measures[d] for d in domain_scores],
    "Responsible": [responsible[d] for d in domain_scores],
    "Review Date": [review_date[d] for d in domain_scores]
})

def color_score(val):
    if val >= 8: return 'background-color: #34c759; color: black;'
    elif val >= 6: return 'background-color: #ffeb3b; color: black;'
    elif val >= 4: return 'background-color: #ff9800; color: black;'
    else: return 'background-color: #f44336; color: white;'

st.dataframe(df_summary.style.applymap(color_score, subset=['Score']))
