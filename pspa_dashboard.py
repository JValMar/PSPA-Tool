
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
    # Determine lowest questions (handle ties)
    min_score = min(scores)
    lowest_qs = [f"{domain.split('.')[0]}.{j+1} {questions[j]}" for j, s in enumerate(scores) if s == min_score]
    lowest_questions[domain] = ", ".join(lowest_qs)
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
    st.markdown(f"<p style='color:red;'><b>Lowest scored questions:</b> {lowest_questions[domain]}</p>", unsafe_allow_html=True)

    improvement_measures[domain] = st.text_area(f"Improvement Measures for {domain}", key=f"improve-{domain}")
    responsible[domain] = st.text_input(f"Responsible for {domain}", key=f"resp-{domain}")
    review_date[domain] = st.date_input(f"Review Date for {domain}", value=date.today() + timedelta(days=90), key=f"date-{domain}")

# --- Final Summary ---
st.subheader("Final Summary")
df_summary = pd.DataFrame({
    "Domain": list(domain_scores.keys()),
    "Score": [round(s, 1) for s in domain_scores.values()],
    "Lowest Question": [lowest_questions[d] for d in domain_scores],
    "Lowest Questions": [lowest_questions[d] for d in domain_scores],
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

# --- Radar Chart ---
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

img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png')
img_buffer.seek(0)
st.pyplot(fig)

# --- PDF Export ---
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", 'B', 14)
pdf.cell(0, 10, "Patient Safety Project Adequacy Report", ln=True, align="C")
pdf.set_font("Arial", '', 12)
pdf.multi_cell(0, 10, f"Project: {project_name}\nObjectives: {project_objectives}\nDate: {date.today()}\n")
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Summary of Scores by Domain:", ln=True)
for domain in domain_scores:
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 8, f"{domain}: {domain_scores[domain]:.1f}/10\nLowest: {lowest_questions[domain]}\nImprovement Action: {improvement_measures[domain]}\nResponsible: {responsible[domain]} | Review Date: {review_date[domain]}")
tmp_img = "radar_chart.png"
with open(tmp_img, "wb") as f:
    f.write(img_buffer.getvalue())
pdf.image(tmp_img, x=40, w=130)
pdf.set_y(-20)
pdf.set_font("Arial", 'I', 8)
pdf.multi_cell(0, 8, "Thank you for using this tool. Suggestions: https://bit.ly/raicesp")
pdf_data = pdf.output(dest='S').encode('latin-1')
st.download_button("📄 Download PDF Report", pdf_data, file_name=f"{date.today()}_{project_name.replace(' ', '_')}_PSPA_Report.pdf", mime="application/pdf")

# --- Excel Export ---
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    df_summary.to_excel(writer, index=False, sheet_name='Summary')
    worksheet = writer.sheets['Summary']
    worksheet.insert_image('H2', 'radar_chart.png', {'image_data': img_buffer})
st.download_button("📊 Download Excel (.xlsx)", excel_buffer.getvalue(), file_name=f"{date.today()}_{project_name.replace(' ', '_')}_PSPA_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
