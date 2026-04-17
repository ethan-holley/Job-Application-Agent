# AI Job Application Agent

An AI-powered job application assistant built with Python, Streamlit, and the OpenAI API. This app analyzes a candidate’s resume and a job description, identifies relevant strengths and gaps, suggests tailored resume bullet rewrites, and generates a customized cover letter.

## Features

- Upload a resume in PDF, TXT, or MD format
- Paste a job description directly into the app
- Extracts key job requirements and keywords
- Compares resume content against the job posting
- Highlights strengths and skill gaps
- Suggests tailored resume bullet rewrites
- Generates a customized cover letter
- Uses a multi-step LLM workflow to refine the cover letter using both the resume and the job description

## Tech Stack

- Python
- Streamlit
- OpenAI API
- PyPDF

## How It Works

The application uses a multi-step workflow:

1. Parse the uploaded resume into text
2. Analyze the resume and job description with an LLM
3. Return structured output including:
   - company name
   - role title
   - top requirements
   - preferred requirements
   - keywords
   - strengths
   - gaps
   - match score
   - tailored resume bullet suggestions
   - initial cover letter
4. Run a second LLM step to improve the cover letter by:
   - removing filler language
   - incorporating concrete resume details
   - aligning more directly with the job description
   - tailoring the tone to the company mission

## Example Use Case

A user uploads their resume and pastes a software engineering job description. The app then:
- estimates how well the resume matches the role
- identifies missing or weaker areas
- suggests stronger resume bullets
- produces a more tailored cover letter than a generic template

## Installation

Install Dependencies: pip3 install streamlit openai pypdf

Clone the repository:

```bash
git clone https://github.com/ethan-holley/Job-Application-Agent.git
cd Job-Application-Agent
pip3 install streamlit openai pypdf
export OPENAI_API_KEY="your_api_key_here"
python3 -m streamlit run app.py
```

## Why this matters
This project demonstrates how agentic AI systems can be applied to real-world workflows. 
Instead of a single prompt, the system uses a multi-step process to analyze, generate, 
and iteratively refine outputs using contextual data from both resumes and job descriptions.
