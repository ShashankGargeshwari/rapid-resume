import json
import os
import sqlite3
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html
from openai import OpenAI


def split_bulleted_pointers(bulleted_text: str) -> list[str]:
    pointers = []
    for line in bulleted_text.splitlines():
        cleaned = line.lstrip("-*•")
        if cleaned:
            pointers.append(cleaned)
    return pointers



st.set_page_config(page_title="Rapid Resume", page_icon="📝", layout="centered")

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

prompt = "You are a resume helper agent. Your first message will be a welcome message " \
    "that tells the user in a single concise line that you will help me with my resume today," \
    "and append a made up, cute, success code that still looks technical in [] at the end of the message"


response = client.responses.create(
        model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
        input=[{"role": "user", "content": prompt}],
    )

st.markdown(response.output_text)


st.title("Job Description")

job_description = st.text_area(
    label = "Job Description",
    height = 180,
    placeholder= "Paste Job Description Here"
)


st.title("Resume pointers")

resume_pointers = st.text_area(
    label = "Resume Pointers",
    height = 50,
    placeholder= "Paste Resume Pointers Here"
)

pointer_list = split_bulleted_pointers(resume_pointers)

for pointer in pointer_list:
    st.markdown(pointer)

prompt = "This is the job description " + job_description + "extract a bulleted list of keywords that should be used in a successful resume"

if job_description.strip() :
    response = client.responses.create(
            model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
            input=[{"role": "user", "content": prompt}],
        )
    keywords_list = response.output_text

with st.sidebar:
    st.header("KeyWords")
    st.markdown(keywords_list)






  

