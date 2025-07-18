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
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")

st.markdown("**Version: 17/07/2025.** This is a draft proposal, based on the keynote of this workshop and some ideas from PS & QI tools. Please, feel free to suggest any issues to clarify or complete this checklist: jvmartin@us.es")
st.markdown("""
📘 **Checklist Description**

This checklist evaluates the comprehensive considerations required to advance patient safety (PS) at the hospital level, ensuring alignment with international standards while adapting to local realities.

**NOTE:** Regularly review progress with this checklist, adapting as new challenges and opportunities arise, and ensure culturally sensitive, locally driven, and sustainable improvement.
""")

# Sidebar: Project and Date
st.sidebar.header("Project Information")
project = st.sidebar.text_input("Enter Project Title:", "Adama - Decreasing HAIs").replace('–', '-')
eval_date = st.sidebar.date_input("Date of Evaluation:", date.today())

st.sidebar.markdown("---")
st.sidebar.info("For each domain, respond to multiple evaluation questions (0–10 scale). A summary and recommendations will be generated.")

# Domain Questions
...  # [Keep your domain_questions definition unchanged]

# Input Collection
...  # [Keep your domain_scores, review_dates, notes logic unchanged]

# Radar Chart Generation
...  # [Keep matplotlib chart generation logic unchanged]

# Export Excel Logic
...  # [Keep Excel export logic unchanged]

# PDF Generation
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "PATIENT SAFETY PROJECT ADEQUACY DASHBOARD", 0, 1, 'C')
        self.set_font('Arial', '', 11)
        self.cell(0, 10, f"Project: {project}", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-40)
        self.set_font('Arial', 'I', 8)
        self.set_y(-15)
        self.cell(0, 6, f"Thank you for use this tool. Please share any suggestion: jvmartin@us.es | Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Page {self.page_no()} of {{nb}}", 0, 0, 'C')

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

pdf.set_font('Arial', '', 10)
pdf.cell(0, 8, "Summary of Scores by Dimension:", ln=1)
for _, row in score_df.iterrows():
    score = row['Score']
    if score >= 8:
        color = (0, 128, 0)
    elif score >= 6:
        color = (255, 165, 0)
    elif score >= 4:
        color = (255, 140, 0)
    else:
        color = (255, 0, 0)
    pdf.set_text_color(*color)
    pdf.cell(0, 6, f"{row['Checklist Dimension']:<40} {score}/10", ln=1)

pdf.set_text_color(0, 0, 0)
pdf.ln(5)

with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
    tmp_img.write(img_buffer.getbuffer())
    tmp_img_path = tmp_img.name

pdf.image(tmp_img_path, x=40, y=None, w=130)
pdf.ln(10)

for _, row in score_df.iterrows():
    pdf.chapter_title(row['Checklist Dimension'])
    if row['Score'] < 6:
        pdf.set_font('Arial', 'B', 9)
    else:
        pdf.set_font('Arial', '', 9)
    body = f"""Score: {row['Score']}
Lowest Scored Question: {row['Lowest Scored Question']}
Improvement Measures: {row['Improvement Measures']}
Review Date: {row['Review Date']}"""
    pdf.chapter_body(body)

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
    tmp_pdf_path = tmp_pdf.name
pdf.output(tmp_pdf_path)

with open(tmp_pdf_path, "rb") as f:
    pdf_binary = f.read()

st.download_button(
    label="📄 Download Report (.pdf)",
    data=pdf_binary,
    file_name=f'{project.replace(" ", "_")}_PatientSafetyChecklist.pdf',
    mime='application/pdf'
)

os.remove(tmp_pdf_path)
os.remove(tmp_img_path)
st.success("✅ Evaluation complete. Reports ready for download.")
