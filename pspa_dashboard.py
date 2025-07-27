
# PSPA Dashboard (fixed)
# Includes: login persistence, color scale, and fixed PDF export.

import streamlit as st
import pandas as pd
import hashlib
from datetime import date
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

if "users" not in st.session_state:
    st.session_state["users"] = {"admin": hashlib.sha256("secure123".encode()).hexdigest()}
if "evaluations" not in st.session_state:
    st.session_state["evaluations"] = {}
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    return username in st.session_state["users"] and            st.session_state["users"][username] == hash_password(password)

def color_score(val):
    if val >= 8:
        return "background-color: #90EE90"
    elif val >= 6:
        return "background-color: #FFFF99"
    elif val >= 4:
        return "background-color: #FFD580"
    else:
        return "background-color: #FF7F7F"

st.title("Welcome to the PSPA Dashboard")
st.write("Assess your patient safety projects easily and generate reports.")

if not st.session_state["logged_in"]:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state["username"] = username
            st.session_state["logged_in"] = True
            st.success(f"Welcome, {username}!")
        else:
            st.error("Incorrect username or password.")

if st.session_state["logged_in"]:
    username = st.session_state["username"]
    st.header("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
    st.markdown("**Version: 22/07/2025**")

    project_name = st.text_input("Project Name")
    project_objectives = st.text_area("🎯 Project Objectives")

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
        ]
        # Add other domains as needed
    }

    domain_scores = {}
    lowest_questions = {}
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

    df_summary = pd.DataFrame({
        "Domain": list(domain_scores.keys()),
        "Score": list(domain_scores.values()),
        "Lowest Question": [lowest_questions[d] for d in domain_scores]
    })
    st.dataframe(df_summary.style.applymap(color_score, subset=["Score"]))

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
