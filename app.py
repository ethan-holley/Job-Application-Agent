import json
import os
from typing import Any, Dict, List

import streamlit as st
from openai import OpenAI


# -----------------------------
# App configuration
# -----------------------------
st.set_page_config(page_title="Job Application Agent", page_icon="💼", layout="wide")
st.title("💼 Job Application Agent")
st.caption("Upload your resume, paste a job description, and generate tailored application materials.")


# -----------------------------
# Helpers
# -----------------------------
def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def read_resume_text(uploaded_file) -> str:
    """Read text from a TXT/MD/PDF resume upload."""
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    if filename.endswith(".txt") or filename.endswith(".md"):
        return file_bytes.decode("utf-8", errors="ignore")

    if filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io

            reader = PdfReader(io.BytesIO(file_bytes))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n".join(pages).strip()
        except Exception as e:
            return f"[PDF parsing failed: {e}]"

    return "Unsupported file type. Please upload a .txt, .md, or .pdf file."


SCHEMA_HINT = {
    "company_name": "",
    "role_title": "",
    "top_requirements": [],
    "preferred_requirements": [],
    "keywords": [],
    "resume_strengths": [],
    "resume_gaps": [],
    "match_score": 0,
    "tailored_resume_bullets": [],
    "cover_letter": "",
}


SYSTEM_PROMPT = """
You are a job application assistant.
Your job is to analyze a resume and a job description, then return a structured JSON object.

Rules:
- Be honest. Do not invent experience the candidate does not have.
- Use only the information explicitly found in the resume and job description.
- Tailor wording to the job posting, but do not fabricate tools, projects, or accomplishments.
- The cover letter should sound natural, concise, and suitable for a recent graduate or early-career candidate.
- The tailored resume bullets should be rewritten suggestions, not fabricated achievements.
- Return valid JSON only.
""".strip()


USER_PROMPT_TEMPLATE = """
Analyze the following resume and job description.
Return a JSON object with exactly these keys:
{schema}

Resume:
{resume}

Job Description:
{job_description}
""".strip()



def call_application_agent(client: OpenAI, resume_text: str, job_description: str) -> Dict[str, Any]:
    prompt = USER_PROMPT_TEMPLATE.format(
        schema=json.dumps(SCHEMA_HINT, indent=2),
        resume=resume_text,
        job_description=job_description,
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw_text = response.output_text

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON block if the model wraps it in markdown
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw_text[start:end + 1])
        raise ValueError("Model did not return valid JSON.")

def improve_cover_letter(client, cover_letter, job_description, resume_text):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an expert career coach. "
                    "Improve the cover letter so it is concise, specific, and impactful. "
                    "Remove generic or filler phrases. "
                    "Incorporate concrete details from the candidate’s experience that directly correlate to the job description. "
                    "Prioritize measurable impact and relevant skills. "
                    "Do not invent experience. Keep it professional and tailored to the company’s mission."
                ),
            },
            {
                "role": "user",
                "content": f"""
                    Job Description:
                    {job_description}

                    Resume:
                    {resume_text}

                    Current Cover Letter:
                    {cover_letter}
                    """
                                },
                            ],
                            temperature=0.3,
                        )
    return response.output_text.strip()


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("Setup")
    st.markdown("1. Install dependencies")
    st.code("pip install streamlit openai pypdf", language="bash")
    st.markdown("2. Set your API key")
    st.code("export OPENAI_API_KEY=your_key_here", language="bash")
    st.markdown("3. Run the app")
    st.code("streamlit run job_application_agent_app.py", language="bash")


# -----------------------------
# Main inputs
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Resume")
    uploaded_resume = st.file_uploader(
        "Upload your resume (.pdf, .txt, .md)",
        type=["pdf", "txt", "md"],
        accept_multiple_files=False,
    )
    resume_text = read_resume_text(uploaded_resume) if uploaded_resume else ""

    if resume_text:
        with st.expander("Preview extracted resume text"):
            st.text_area("Resume text", resume_text, height=250)

with col2:
    st.subheader("Job Description")
    job_description = st.text_area(
        "Paste the job description",
        height=350,
        placeholder="Paste the full job posting here...",
    )


# -----------------------------
# Run analysis
# -----------------------------
run_button = st.button("Generate application materials", type="primary")

if run_button:
    if not uploaded_resume:
        st.error("Please upload your resume.")
    elif not job_description.strip():
        st.error("Please paste a job description.")
    elif resume_text.startswith("Unsupported file type") or resume_text.startswith("[PDF parsing failed"):
        st.error(resume_text)
    else:
        try:
            client = get_client()

            with st.spinner("Analyzing your resume and job description..."):
                result = call_application_agent(client, resume_text, job_description)
                improved_cover_letter = improve_cover_letter(
                    client,
                    result.get("cover_letter", ""),
                    job_description,
                    resume_text
                )
                result["cover_letter"] = improved_cover_letter

            st.success("Done.")

            top_left, top_right = st.columns([1, 2])
            with top_left:
                st.metric("Match score", f"{result.get('match_score', 0)} / 100")
                st.write("**Company:**", result.get("company_name", "Unknown"))
                st.write("**Role:**", result.get("role_title", "Unknown"))

            with top_right:
                st.subheader("Keywords")
                keywords = result.get("keywords", [])
                if keywords:
                    st.write(", ".join(keywords))
                else:
                    st.write("No keywords extracted.")

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Top requirements")
                for item in result.get("top_requirements", []):
                    st.markdown(f"- {item}")

                st.subheader("Your strengths")
                for item in result.get("resume_strengths", []):
                    st.markdown(f"- {item}")

            with c2:
                st.subheader("Preferred requirements")
                for item in result.get("preferred_requirements", []):
                    st.markdown(f"- {item}")

                st.subheader("Gaps to address")
                for item in result.get("resume_gaps", []):
                    st.markdown(f"- {item}")

            st.subheader("Suggested resume bullet rewrites")
            bullets = result.get("tailored_resume_bullets", [])
            if bullets:
                for bullet in bullets:
                    st.markdown(f"- {bullet}")
            else:
                st.write("No bullet suggestions generated.")

            st.subheader("Tailored cover letter")
            st.text_area(
                "Cover letter output",
                value=result.get("cover_letter", ""),
                height=350,
            )

            with st.expander("Raw JSON output"):
                st.json(result)

        except Exception as e:
            st.error(f"Something went wrong: {e}")


# -----------------------------
# Notes for future upgrades
# -----------------------------
st.divider()
st.markdown("### Good next upgrades")
st.markdown(
    """
- Add a second agent that critiques the first draft before showing output.
- Save multiple application versions for different jobs.
- Add company research via web search.
- Export the cover letter to a .txt or .docx file.
- Add a scoring rubric for ATS keyword coverage.
"""
)
