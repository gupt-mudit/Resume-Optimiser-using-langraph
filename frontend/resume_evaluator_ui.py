import os

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()
url=os.getenv("BACKEND_DOMAIN")
st.set_page_config(layout="wide")
st.title("📄 ATS Resume Evaluator")

# ------------------------------
# Step 1: Upload Resume
# ------------------------------
st.header("Step 1: Upload Resume (.tex)")
resume_file = st.file_uploader("Upload your LaTeX Resume", type=["tex"])
if resume_file:
    if st.button("Upload Resume"):
        with st.spinner("Uploading resume..."):
            res = requests.post("http://"+url+"/upload_resume", files={"file": resume_file})
            if res.ok:
                st.success("✅ Resume uploaded successfully!")
            else:
                st.error("❌ Failed to upload resume.")

# ------------------------------
# Step 2: Provide Job Description
# ------------------------------
st.header("Step 2 (Optional): Provide Job Description")
jd_source = st.radio("Choose JD input method", ["Upload File", "Paste Text", "Provide URL"])

jd_uploaded = False

if jd_source == "Upload File":
    jd_file = st.file_uploader("Upload JD (PDF or TXT)", type=["pdf", "txt"])
    if jd_file and st.button("Upload JD File"):
        with st.spinner("Uploading JD..."):
            res = requests.post("http://"+url+"/upload_jd", files={"file": jd_file})
            if res.ok:
                st.success("✅ JD uploaded successfully!")
                jd_uploaded = True
            else:
                st.error("❌ Failed to upload JD.")

elif jd_source == "Paste Text":
    jd_text = st.text_area("Paste the Job Description here:")
    if jd_text.strip() and st.button("Submit JD Text"):
        with st.spinner("Submitting JD text..."):
            res = requests.post("http://"+url+"/upload_jd", json={"text": jd_text})
            if res.ok:
                st.success("✅ JD text submitted successfully!")
                jd_uploaded = True
            else:
                st.error("❌ Failed to submit JD text.")

elif jd_source == "Provide URL":
    jd_url = st.text_input("Enter JD URL:")
    if jd_url.strip() and st.button("Fetch JD from URL"):
        with st.spinner("Fetching JD from URL..."):
            res = requests.post("http://"+url+"/upload_jd", json={"url": jd_url})
            if res.ok:
                st.success("✅ JD fetched from URL successfully!")
                jd_uploaded = True
            else:
                st.error("❌ Failed to fetch JD from URL.")

# ------------------------------
# Step 3: Chat and ATS Evaluation
# ------------------------------
st.header("Step 3: Chat with AI about Resume Fit")

if "messages" not in st.session_state:
    st.session_state.messages = []

input_text = st.text_input("Ask a question about your resume:")

if input_text:
        with st.spinner("Thinking..."):
            res = requests.post("http://"+url+"/ask", json={"question": input_text})
            if res.ok:
                result = res.json()
                answer = result.get("answer", {})

                ats_score = answer.get("ats_score", "N/A")
                jd_score = answer.get("jd_match_score", "N/A")
                suggestions = answer.get("suggestions", [])
                updated_resume = answer.get("updated_resume", "No updated resume found.")
                ai_reply = answer.get("ai_reply", "AI did not respond.")

                st.session_state.messages.append(("user", input_text))
                st.session_state.messages.append(("assistant", ai_reply))

                # Chat + Evaluation display
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("💬 Chat")
                    for role, msg in st.session_state.messages:
                        st.chat_message(role).write(msg)
                with col2:
                    st.subheader("📊 ATS Evaluation")
                    st.metric("ATS Score", f"{ats_score}/100")
                    st.metric("JD Match Score", f"{jd_score}/100")
                    st.markdown("**Suggestions to Improve Resume:**")
                    for s in suggestions:
                        st.markdown(f"🔹 {s}")
                    st.markdown("---")
                    st.markdown("**📄 Updated Resume (LaTeX)**")
                    st.code(updated_resume, language="latex")
            else:
                st.error("❌ Something went wrong while getting AI response.")
