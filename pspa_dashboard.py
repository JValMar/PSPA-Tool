# Ethiopia Patient Safety Checklist Dashboard (Enhanced PDF Summary & Visuals)

import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import io
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Ethiopia PS Checklist", layout="centered")
st.title("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
st.markdown("**Version: 17/07/2025.** This is a draft proposal, based on the keynote of this workshop and some ideas from PS & QI tools. Please, feel free to suggest any issues to clarify or complete this checklist: jvmartin@us.es")
st.markdown("""
📘 **Checklist Description**

This checklist evaluates the comprehensive considerations required to advance patient safety (PS) at the hospital level, ensuring alignment with international standards while adapting to local realities.

**NOTE:** Regularly review progress with this checklist, adapting as new challenges and opportunities arise, and ensure culturally sensitive, locally driven, and sustainable improvement.
""")

# Sidebar: Project and Date
# Logo upload removed for PDF, but you can display it on the web if needed", type=["jpg", "jpeg", "png"])
st.sidebar.header("Project Information")
project = st.sidebar.text_input("Enter Project Title:", "Adama - Decreasing HAIs").replace('–', '-')
eval_date = st.sidebar.date_input("Date of Evaluation:", date.today())

st.sidebar.markdown("---")
st.sidebar.info("For each domain, respond to multiple evaluation questions (0–10 scale). A summary and recommendations will be generated.")

# Detailed questions per domain
domain_questions = {
    "1. Leadership & Governance": [
        "Is there a designated patient safety focal person?",
        "Does leadership participate in safety rounds or reviews?",
        "Are safety goals part of the hospital's annual plan?",
        "Is patient safety discussed in leadership meetings?"
    ],
    "2. Resources & Capacity": [
        "Are IPC materials adequately available?",
        "Are staff regularly trained on patient safety?",
        "Is there a dedicated IPC budget?",
        "Are clinical areas properly equipped to prevent harm?"
    ],
    "3. Baseline Assessment": [
        "Has a recent risk assessment been conducted?",
        "Is incident reporting in place and functioning?",
        "Do you have baseline data on HAIs or errors?",
        "Is there any safety culture assessment data?"
    ],
    "4. Intervention Design & Implementation": [
        "Are SOPs and safety checklists used consistently?",
        "Are interventions adapted to local realities?",
        "Is patient safety included in job roles and induction?",
        "Are bundles or care pathways in place?"
    ],
    "5. Change Management": [
        "Is SBAR or other communication tools used routinely?",
        "Is feedback from safety audits shared with teams?",
        "Is there accountability for implementing changes?",
        "Do staff participate in improvement planning?"
    ],
    "6. Sustainability & Institutionalization": [
        "Are patient safety activities embedded in budgets?",
        "Are safety champions or trainers identified?",
        "Is training updated regularly and documented?",
        "Are safety practices reviewed periodically?"
    ],
    "7. Cross-Learning, Partnerships": [
        "Does the hospital participate in peer learning?",
        "Are patient or family voices part of safety efforts?",
        "Is knowledge from incidents shared?",
        "Is there collaboration with external partners?"
    ]
}

# Containers for scores and feedback
domain_scores = {}
improvement_notes = {}
lowest_questions = {}
review_dates = {}

st.header("📌 Self-Assessment by Domain")

# Color-coded tag function
def color_tag(score):
    if score >= 8:
        return ':green[Excellent]'
    elif score >= 6:
        return ':orange[Moderate]'
    elif score >= 4:
        return ':orange[Low]'
    else:
        return ':red[Critical]'

for domain, questions in domain_questions.items():
    st.markdown(f"### {domain}")
    question_scores = []
    lowest_q = ("", 11)
    for q in questions:
        score = st.slider(f"{q}", 0, 10, 5, key=f"{domain}-{q}")
        question_scores.append(score)
        if score < lowest_q[1]:
            lowest_q = (q, score)

    avg_score = sum(question_scores) / len(question_scores)
    domain_scores[domain] = round(avg_score, 2)
    # Add colored tag below each domain based on avg score
    if avg_score >= 8:
        st.markdown(':green[🟢 Excellent domain score]')
    elif avg_score >= 6:
        st.markdown(':orange[🟡 Moderate domain score]')
    elif avg_score >= 4:
        st.markdown(':orange[🟠 Low domain score]')
    else:
        st.markdown(':red[🔴 Critical domain score]')
    lowest_questions[domain] = lowest_q[0]
    improvement_notes[domain] = st.text_area(f"Improvement Measures for {domain}", "", key=f"note_{domain}")
    review_dates[domain] = st.date_input(f"Planned Re-evaluation Date for {domain}", date.today() + timedelta(days=90), key=f"reval_{domain}")

# Create DataFrame
score_df = pd.DataFrame({
    "Checklist Dimension": list(domain_scores.keys()),
    "Score": list(domain_scores.values()),
    "Lowest Scored Question": list(lowest_questions.values()),
    "Improvement Measures": list(improvement_notes.values()),
    "Review Date": [d.strftime("%Y-%m-%d") for d in review_dates.values()]
})

average_score = sum(domain_scores.values()) / len(domain_scores)

# Create radar chart
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
labels = list(domain_scores.keys())
scores = list(domain_scores.values())
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
scores += scores[:1]
angles += angles[:1]
ax.plot(angles, scores, color='blue', linewidth=2)
ax.fill(angles, scores, color='skyblue', alpha=0.4)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=8)
for label, angle in zip(ax.get_xticklabels(), angles):
    label.set_horizontalalignment('center')
ax.set_yticks(range(0, 11, 2))
ax.set_ylim(0, 10)
ax.set_title('Patient Safety Project Radar', size=12, pad=20)
plt.tight_layout()
img_buffer = io.BytesIO()
plt.savefig(img_buffer, format='png')
img_buffer.name = "radar.png"
img_buffer.seek(0)
plt.close()

# Export to Excel
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    score_df.to_excel(writer, sheet_name='Checklist Report', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Checklist Report']

    # Apply conditional formatting to Score column
    format_red = workbook.add_format({'bg_color': '#FFC7CE'})
    format_orange = workbook.add_format({'bg_color': '#FFEB9C'})
    format_yellow = workbook.add_format({'bg_color': '#FFFACD'})
    format_green = workbook.add_format({'bg_color': '#C6EFCE'})

    worksheet.conditional_format('B2:B100', {'type': 'cell', 'criteria': '<', 'value': 4, 'format': format_red})
    worksheet.conditional_format('B2:B100', {'type': 'cell', 'criteria': 'between', 'minimum': 4, 'maximum': 5.9, 'format': format_orange})
    worksheet.conditional_format('B2:B100', {'type': 'cell', 'criteria': 'between', 'minimum': 6, 'maximum': 7.9, 'format': format_yellow})
    worksheet.conditional_format('B2:B100', {'type': 'cell', 'criteria': '>=', 'value': 8, 'format': format_green})
    worksheet.conditional_format('D2:D100', {'type': 'cell', 'criteria': 'between', 'minimum': 4, 'maximum': 5.9, 'format': format_orange})
    worksheet.conditional_format('D2:D100', {'type': 'cell', 'criteria': 'between', 'minimum': 6, 'maximum': 7.9, 'format': format_yellow})
    worksheet.conditional_format('D2:D100', {'type': 'cell', 'criteria': '>=', 'value': 8, 'format': format_green})

    # Add radar chart image to Excel
    worksheet.set_column('A:A', 30)
    worksheet.set_column('B:B', 40)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 10, workbook.add_format({'align': 'center'}))
    worksheet.set_column('E:E', 60)
    worksheet.set_column('F:F', 50)
    worksheet.set_column('G:G', 20)
    # Auto-adjust column widths
    for col_num, value in enumerate(score_df.columns.values):
        column_len = max(
            score_df[value].astype(str).map(len).max(),
            len(value)
        ) + 2
        worksheet.set_column(col_num, col_num, column_len)

    worksheet.insert_image(f'{chr(65 + len(score_df.columns))}2', 'radar.png', {'image_data': img_buffer})

st.download_button(
    label="📥 Download Report (.xlsx)",
    data=excel_buffer.getvalue(),
    file_name=f'{project.replace(" ", "_")}_PatientSafetyChecklist.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)



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

# Summary of Scores with color cues
pdf.set_font('Arial', '', 10)
pdf.cell(0, 8, "Summary of Scores by Dimension:", ln=1)
for _, row in score_df.iterrows():
    score = row['Score']
    if score >= 8:
        color = (0, 128, 0)  # Green
    elif score >= 6:
        color = (255, 165, 0)  # Orange
    elif score >= 4:
        color = (255, 140, 0)  # Darker orange/yellow
    else:
        color = (255, 0, 0)  # Red
    pdf.set_text_color(*color)
    pdf.cell(0, 6, f"{row['Checklist Dimension']:<40} {score}/10", ln=1)

pdf.set_text_color(0, 0, 0)
pdf.ln(5)

import tempfile

with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
    tmp_img.write(img_buffer.getbuffer())
    tmp_img_path = tmp_img.name

pdf.image(tmp_img_path, x=40, y=None, w=130)
pdf.ln(10)

# Section Details
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

pdf_buffer = io.BytesIO()
pdf_bytes = pdf.output(dest='S').encode('latin1')
pdf_buffer = io.BytesIO(pdf_bytes)

st.download_button(
    label="📄 Download Report (.pdf)",
    data=pdf_buffer.getvalue(),
    file_name=f'{project.replace(" ", "_")}_PatientSafetyChecklist.pdf',
    mime='application/pdf'
)

import os
os.remove(tmp_img_path)
st.success("✅ Evaluation complete. Reports ready for download.")
