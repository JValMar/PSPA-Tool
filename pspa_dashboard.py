import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from fpdf import FPDF
from datetime import date, datetime

st.write('App started')

# Simple user-specific sessions
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None

# Dictionary to store evaluations per user
if "user_data" not in st.session_state:
    st.session_state["user_data"] = {}

# Login form
if not st.session_state["current_user"]:
    st.header("Welcome to the PSPA Dashboard")
    st.info("Enter your credentials to access your evaluations.")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # For demo, only admin/secure123 is valid
        if username == "admin" and password == "secure123":
            st.session_state["current_user"] = username
            if username not in st.session_state["user_data"]:
                st.session_state["user_data"][username] = {}
            st.success(f"Welcome, {username}!")
        else:
            st.error("Incorrect username or password.")
else:
    st.sidebar.write(f"Logged in as: {st.session_state['current_user']}")
    if st.sidebar.button("Logout"):
        st.session_state["current_user"] = None
        st.experimental_rerun()

    st.title("Patient Safety Project Adequacy Dashboard")

    # Dropdown to select existing projects
    user_projects = list(st.session_state["user_data"][st.session_state["current_user"]].keys())
    selected_project = st.selectbox("Select an existing project (or type new):", ["<New Project>"] + user_projects)

    if selected_project != "<New Project>":
        project_data = st.session_state["user_data"][st.session_state["current_user"]][selected_project]
        project = st.text_input("Project Name", selected_project)
        objectives = st.text_area("Project Objectives", project_data["objectives"])
        previous_scores = project_data["scores"]
    else:
        project = st.text_input("Project Name")
        objectives = st.text_area("Project Objectives")
        previous_scores = {}

    domains = ["Leadership", "Staffing", "Baseline", "Design", "Change Mgmt", "Monitoring", "Sustainability"]
    scores = {}
    for d in domains:
        default_value = previous_scores.get(d, 5)
        scores[d] = st.slider(f"Score for {d}", 0, 10, default_value, key=f"{st.session_state['current_user']}_{d}")

    df = pd.DataFrame(list(scores.items()), columns=["Domain", "Score"])
    st.dataframe(df)

    # Save user data for this project
    st.session_state["user_data"][st.session_state["current_user"]][project] = {
        "objectives": objectives,
        "scores": scores,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    labels = list(scores.keys())
    values = list(scores.values())
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    st.pyplot(fig)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Project: {project}", ln=True)
    pdf.set_font("Arial", '', 12)
    for domain, score in scores.items():
        pdf.cell(0, 10, f"{domain}: {score}/10", ln=True)
    pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)

    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    st.download_button("Download PDF", data=pdf_buffer.getvalue(), file_name=f"pspa_report_{st.session_state['current_user']}.pdf", mime="application/pdf")
