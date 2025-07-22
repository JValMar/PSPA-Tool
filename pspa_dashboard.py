# pspa_dashboard.py - Lightweight version with welcome message, account creation, and logout confirmation

import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import io, tempfile, os
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

# Store users in memory (for demo purposes)
if "users" not in st.session_state:
    st.session_state["users"] = {"admin": "secure123"}

st.set_page_config(page_title="PSPA Dashboard", layout="centered")

# Logout button with confirmation
if "user" in st.session_state:
    if st.button("Logout"):
        st.session_state.pop("user")
        st.success("You have successfully logged out.")
        st.experimental_rerun()

st.title("🔐 PSPA Dashboard Login")
menu = st.radio("Select an option:", ["Login", "Create Account"])

if menu == "Create Account":
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Register"):
        if new_user and new_pass:
            st.session_state["users"][new_user] = new_pass
            st.success("Account successfully created. You can now log in.")
        else:
            st.error("You must enter a username and password.")

if menu == "Login" and "user" not in st.session_state:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in st.session_state["users"] and st.session_state["users"][username] == password:
            st.session_state["user"] = username
            st.success(f"Welcome, {username}!")
            st.info("This tool helps you assess the adequacy of Patient Safety Projects by scoring across multiple domains. Thank you for your interest in using it!")
            st.experimental_rerun()
        else:
            st.error("Incorrect username or password.")

# Only show dashboard if logged in
if "user" in st.session_state:
    st.header("📊 PATIENT SAFETY PROJECT ADEQUACY DASHBOARD")
    st.markdown("**Version: 22/07/2025**")
    project = st.text_input("Enter project name:")
    objectives = st.text_area("🎯 PROJECT OBJECTIVES", "")

    # (The rest of the evaluation code with questions, scoring, charts, and PDF/Excel generation remains unchanged.)
