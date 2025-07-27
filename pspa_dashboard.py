
import streamlit as st
import pandas as pd
import hashlib
from datetime import date, timedelta
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

# ----------- Inicialización -----------
if "users" not in st.session_state:
    st.session_state["users"] = {"admin": hashlib.sha256("secure123".encode()).hexdigest()}
if "evaluations" not in st.session_state:
    st.session_state["evaluations"] = {}
if "username" not in st.session_state:
    st.session_state["username"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ----------- Funciones Auxiliares -----------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    st.session_state["users"][username] = hash_password(password)

def authenticate(username, password):
    return username in st.session_state["users"] and            st.session_state["users"][username] == hash_password(password)

def color_score(val):
    if val >= 8:
        return 'background-color: #a6f1a6'  # green
    elif val >= 6:
        return 'background-color: #fff7a6'  # yellow
    elif val >= 4:
        return 'background-color: #ffd9a6'  # orange
    else:
        return 'background-color: #f1a6a6'  # red

# ----------- Login y Registro -----------
st.image("https://raw.githubusercontent.com/JValMar/PSPA-Tool/main/RAICESP_eng_imresizer.jpg", width=150)

if not st.session_state["logged_in"]:
    st.title("Welcome to the PSPA Dashboard")
    st.write("Assess your patient safety projects and generate reports.")
    auth_mode = st.radio("Choose Action", ["Login", "Register"])

    if auth_mode == "Register":
        new_user = st.text_input("Choose a username")
        new_pass = st.text_input("Choose a password", type="password")
        if st.button("Create Account"):
            if new_user and new_pass:
                if new_user in st.session_state["users"]:
                    st.error("This username already exists.")
                else:
                    register_user(new_user, new_pass)
                    st.success("Account created successfully! You can now login.")
            else:
                st.warning("Please enter both username and password.")

    elif auth_mode == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state["username"] = username
                st.session_state["logged_in"] = True
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
            else:
                st.error("Incorrect username or password.")

# ----------- Dashboard -----------
if st.session_state["logged_in"]:
    username = st.session_state["username"]
    st.header("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
    st.markdown("**Version: 22/07/2025**")

    evaluations = st.session_state["evaluations"].get(username, {})
    project_list = list(evaluations.keys())
    selected_project = st.selectbox("Select a project to load", ["New Project"] + project_list)

    if selected_project != "New Project":
        current_data = evaluations[selected_project]
    else:
        current_data = {}

    project_name = st.text_input("Project Name", value=current_data.get("project_name", ""))
    project_objectives = st.text_area("🎯 Project Objectives", value=current_data.get("objectives", ""))

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

    domain_scores, lowest_questions, improvement_measures, responsible, review_date = {}, {}, {}, {}, {}

    st.header("Self-Assessment by Domain")
    for domain, questions in base_domain_questions.items():
        st.subheader(domain)
        scores = []
        for i, q in enumerate(questions, start=1):
            st.markdown(f"**{domain.split('.')[0]}.{i} {q}**")
            st.text_area(f"Notes for {q}", key=f"notes-{domain}-{i}")
            score = st.slider(f"Score this question (0-10)", 0, 10, 5, key=f"{domain}-{i}")
            scores.append(score)
        avg_score = round(np.mean(scores), 2)
        domain_scores[domain] = avg_score
        lowest_questions[domain] = questions[np.argmin(scores)]
        st.markdown(f"**Domain Score:** {avg_score}/10")
        st.caption(f"Lowest scored question: {lowest_questions[domain]}")
        improvement_measures[domain] = st.text_area(f"Improvement Measures for {domain}", key=f"improve-{domain}")
        responsible[domain] = st.text_input(f"Responsible for {domain}", key=f"resp-{domain}")
        review_date[domain] = st.date_input(f"Review Date for {domain}", value=date.today() + timedelta(days=90), key=f"date-{domain}")

    st.subheader("Final Summary")
    df_summary = pd.DataFrame({
        "Domain": list(domain_scores.keys()),
        "Score": list(domain_scores.values()),
        "Lowest Question": [lowest_questions[d] for d in domain_scores],
        "Responsible": [responsible[d] for d in domain_scores],
        "Review Date": [review_date[d] for d in domain_scores]
    })
    st.dataframe(df_summary.style.applymap(color_score, subset=['Score']))

    # Radar chart
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

    if st.button("💾 Save Project Evaluation"):
        if username not in st.session_state["evaluations"]:
            st.session_state["evaluations"][username] = {}
        st.session_state["evaluations"][username][project_name] = {
            "project_name": project_name,
            "objectives": project_objectives,
            "scores": domain_scores,
            "lowest_questions": lowest_questions,
            "improvements": improvement_measures,
            "responsible": responsible,
            "review_date": {k: str(v) for k, v in review_date.items()}
        }
        st.success("Project evaluation saved successfully!")

    # -------- PDF Export --------
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
        pdf.multi_cell(0, 8, f"{domain}: {domain_scores[domain]}/10 | Lowest: {lowest_questions[domain]}\nResponsible: {responsible[domain]} | Review Date: {review_date[domain]}")
    pdf_data = pdf.output(dest='S').encode('latin-1')
    st.download_button("📄 Download PDF Report", pdf_data, file_name=f"{date.today()}_{project_name.replace(' ', '_')}_PSPA_Report.pdf", mime="application/pdf")

    # -------- Excel Export --------
    excel_buffer = io.BytesIO()
    df_summary.to_excel(excel_buffer, index=False, sheet_name='Summary')
    st.download_button("📊 Download Excel (.xlsx)", excel_buffer.getvalue(), file_name=f"{date.today()}_{project_name.replace(' ', '_')}_PSPA_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    st.info("💬 **Thank you for using this tool. Please help us improve by sharing comments or suggestions at [https://bit.ly/raicesp](https://bit.ly/raicesp)**")
