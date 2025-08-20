
import streamlit as st

st.set_page_config(layout="centered")
st.title("📊 Preview: PSPA Dashboard Visual Mockup")

st.markdown("### Example of Domain Score Blocks", unsafe_allow_html=True)

ranking_blocks = {
    "VERY LOW": "#ff4d4d",
    "LOW": "#ff944d",
    "AVERAGE": "#ffeb3b",
    "HIGH": "#81c784",
    "VERY HIGH": "#42a5f5"
}

for rank, color in ranking_blocks.items():
    st.markdown(
        f"<div style='background-color:{color}; color:#1a1a1a; padding:8px; border-radius:6px;'>"
        f"<b>Domain Score:</b> 6.5/10 - <b>{rank}</b></div>",
        unsafe_allow_html=True
    )

st.markdown("---")
st.markdown("### Example of Lowest Question Highlight", unsafe_allow_html=True)

lowest_questions = [
    ("3.1", "Is there a team leading the changes?"),
    ("4.2", "Are responsibilities and timelines defined?")
]

for num, text in lowest_questions:
    st.markdown(
        f"<p><b>Lowest Question:</b> <span style='color:#0040ff; font-weight:bold;'>{num}</span> "
        f"<span style='color:#cc0000;'>{text}</span></p>",
        unsafe_allow_html=True
    )

st.info("This is a visual preview to check styles, contrast and layout for mobile and desktop views.")
