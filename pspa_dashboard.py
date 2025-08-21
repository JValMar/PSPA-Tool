# pspa_evidence_block.py
# Reusable block to render "How to perform the self‑assessment" and
# "Typical evidence by dimension" in Streamlit.

import streamlit as st

def add_howto_and_evidence_section():
    """Render the How-To (scale 0–10) and the Evidence-by-dimension expander."""
    st.subheader("How to perform the self‑assessment")
    st.markdown(
        """
Use the common **0–10 scale** across **all 7 PSPA dimensions**. Score each question based on evidence available today. 
Document brief **notes** (what you saw, where it lives) and add the **Improvement Action Plan (IAP)** for each domain.

**Common scale (0–10)**

| Level | Descriptor | Minimum expected criteria / evidence |
|:-----:|:-----------|:-------------------------------------|
| **0** | **Nonexistent** | No activity or documents. Nothing planned or assigned. |
| **2** | **Declared intent** | Verbal intent or unapproved drafts. No formally designated owners. No secured resources or timeline. |
| **4** | **Basic defined** | Basic elements documented but incomplete: a named owner, initial document(s), preliminary timeline, no evidence of regular use or data. |
| **6** | **Initial implementation** | Approved documents in use; active roles; first actions underway; baseline or early process data available; limited coverage (<50%) and no systematic improvement cycles yet. |
| **8** | **Operational and consistent** | Extended practice (~50–80% coverage), periodic data with feedback; PDSA-type adjustments; risks managed; evidence of sustained compliance for ≥2–3 months. |
| **10** | **Integrated and outcome-producing** | Practice standardized with >80–90% coverage; demonstrated improvements in outcomes; embedded in SOPs/guidelines and budgets; audit and continuous improvement; independent of the initial project team; learning disseminated. |
        """,
        unsafe_allow_html=False
    )

    with st.expander("Typical evidence by dimension (apply the scale using items like these)"):
        st.markdown(
            """
- **Leadership & Governance**: active sponsor and committee; **RACI** and meeting **minutes**; approved **policy/charter**; **quarterly** review routine.
- **Resources & Capabilities**: budget / funding source; staffing and **competencies**; **training plan**; materials / **protocols at point of care**.
- **Baseline**: indicators with **operational definitions**; target population; initial data (**run chart** / table); **SMART** goals.
- **Design & Implementation**: **theory of change**; SOPs / standards; **timeline with milestones**; documented **coverage / reach**; traceability of changes.
- **Change Management**: **communication plan**; champions; **training sessions**; audits / observations; **feedback loops** to teams.
- **Sustainability**: integration into **SOPs / roles**; **KPIs** on the institutional dashboard; **handover / rotation** plan; **recurrent funding** line.
- **Cross-learning & Partnerships**: **MoUs / agreements**; inter‑facility **learning sessions**; **shared data / lessons learned**; co‑mentoring & dissemination products.
            """,
            unsafe_allow_html=False
        )
