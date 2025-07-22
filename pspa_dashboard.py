import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from fpdf import FPDF
from datetime import date, timedelta, datetime

# Debug startup
st.write('App started')

# Simplified login for testing
def login_section():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == "admin" and password == "secure123":
            st.session_state["logged_in"] = True
            st.success("Login successful.")
        else:
            st.error("Incorrect username or password.")

if "logged_in" not in st.session_state:
    login_section()

if st.session_state.get("logged_in"):
    st.title("Patient Safety Project Adequacy Dashboard")
    project = st.text_input("Project Name")
    objectives = st.text_area("Project Objectives")

    # Example domain scores
    domains = ["Leadership", "Staffing", "Baseline", "Design", "Change Mgmt", "Monitoring", "Sustainability"]
    scores = {d: st.slider(f"Score for {d}", 0, 10, 5) for d in domains}
    df = pd.DataFrame(list(scores.items()), columns=["Domain", "Score"])
    st.dataframe(df)

    # Generate radar chart
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

    # PDF generation using buffer
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
    pdf_data = pdf_buffer.getvalue()

    st.download_button("Download PDF", data=pdf_data, file_name="pspa_report.pdf", mime="application/pdf")
