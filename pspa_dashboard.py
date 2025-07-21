# Steps to Deploy on Streamlit Cloud

1. **Create a GitHub Repository:**
   - Sign in to [GitHub](https://github.com/) and create a new repository (e.g., `pspa-dashboard`).
   - Clone the repository locally using `git clone <repo-url>`.
   - Copy your `pspa_dashboard.py` and any supporting files (like `config.json`) into the repository folder.

2. **Add Requirements File:**
   - Create a file named `requirements.txt` in the repository root with the following content:
     ```
     streamlit
     pandas
     matplotlib
     fpdf
     numpy
     ```

3. **Push to GitHub:**
   Use the following commands:
   ```bash
   git add .
   git commit -m "Initial commit with pspa_dashboard"
   git push origin main
   ```

4. **Deploy on Streamlit Cloud:**
   - Go to [Streamlit Cloud](https://share.streamlit.io/).
   - Log in with your GitHub account.
   - Click **New app** and select your repository and branch (e.g., `main`).
   - Choose `pspa_dashboard.py` as the main file.
   - Deploy the app.

5. **Access and Share:**
   - Once deployed, Streamlit will provide a shareable URL (e.g., `https://<your-app>.streamlit.app`).
   - Share this link with others. They will use the login credentials set in the app.

6. **Future Updates:**
   - Edit your local code and push changes with `git commit` and `git push`. Streamlit Cloud will automatically redeploy the app.

---

Would you like me to create a **ready-to-use `requirements.txt`** and a **sample `README.md`** for this project?
