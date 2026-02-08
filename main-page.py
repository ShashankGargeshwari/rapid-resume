"""Streamlit app for tailoring resume pointers to a job description."""

import json
import os
import sqlite3
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html
from openai import OpenAI

import logging

# Setup Logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

logger.info("App started now")


# Initialize the OpenAI client with Streamlit secrets.
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def split_bulleted_pointers(bulleted_text: str) -> list[str]:
    """Convert a bulleted string into a list of plain text lines."""
    pointers = []
    for line in bulleted_text.splitlines():
        cleaned = line.lstrip("-*•")
        if cleaned:
            pointers.append(cleaned)
    return pointers


class ResumePointer:
    """Represents a resume bullet and its relevance score."""
    plain_text = ""
    match_score = 0
    match_keywords = []

    def __init__(self, raw_text):
        """Initialize with the raw bullet text."""
        self.plain_text = raw_text

    def render(self):
        """Render the pointer and a color-coded relevance badge."""
        st.markdown(self.plain_text)
        if(self.match_score <= 5):
            st.badge(f"Relevance : {self.match_score}", color="red")
        else:
            if(self.match_score <=7):
                st.badge(f"Relevance : {self.match_score}", color="orange")
            else:
                st.badge(f"Relevance : {self.match_score}", color="green")

        st.markdown("**Keywords**")
        st.text(self.match_keywords)
                
        st.write("---")
    
    def match(self , keywords_list):
        """Score relevance of this pointer against a list of keywords."""
        prompt = """Score how well this resume pointer (out of 10) is relevant to the list of keywords provided. Provide ONLY the number,
        with no trailing or leading text. Show all the keywords in a single line seprarated by commans, no bullets"""
        all_keywords = ""
        for keyword in keywords_list:
            all_keywords += keyword + " , "

        response = client.responses.create(
        model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
        input=[{"role": "user", "content": f"{prompt} Keywords : {all_keywords} Resume Pointer : {self.plain_text}"}],
        )

        self.match_score = int(response.output_text)

        # list out keywords for which this resume pointer is a good match. 
        prompt = """List out the at most top 6 keywords this resume pointer is a good match for. If you cannot find 3 good matches,
        Show only the keywords that are a match. If they are fewer or no matches, then show only the appropriate number of  keywords.
        Don't have any leading ortrailing text"""
        self.match_keywords = client.responses.create(
        model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
        input=[{"role": "user", "content": f"{prompt} Keywords : {all_keywords} Resume Pointer : {self.plain_text}"}],
        ).output_text

class Keyword:
    """Simple keyword wrapper for rendering in the sidebar."""
    plain_text = ""
    importance = 0
    index = 0
    frequency = 0

    def __init__(self, raw_text, imp, ind):
        """Initialize the keyword with display metadata."""
        self.plain_text = raw_text
        self.importance = raw_text
        self.index = ind

    def render(self):
        """Render the keyword with its index in the sidebar."""
        st.markdown(f"{self.index}. {self.plain_text} [ {self.frequency}]")

    def update_frequency(self, resume_pointers: list[ResumePointer]):
        """Update the frequency of this keyword matching resume poitners"""
        for resume_pointer in resume_pointers:
            logger.info(f" keyword :   + {self.plain_text} + resume pointer match  : {resume_pointer.match_keywords}") 
            if(self.plain_text in resume_pointer.match_keywords):
                self.frequency = self.frequency+1
                logger.info("!!! match !!!")

st.set_page_config(page_title="Rapid Resume", page_icon="📝", layout="centered")

# Set OpenAI API key from Streamlit secrets.
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set a default model.
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

# Initial greeting for the user.
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

resume_pointers_text = st.text_area(
    label = "Resume Pointers",
    height = 'content',
    placeholder= "Paste Resume Pointers Here"
)

pointer_list = split_bulleted_pointers(resume_pointers_text)

resume_pointers = []

for pointer in pointer_list:
    r = ResumePointer(pointer)
    resume_pointers.append(r)

prompt = f"""This is the job description {job_description} extract a bulleted list of keywords that should be used in a successful resume.
    Avoid any leading or trailing sentences. Just have the bulleted list. Sort it in descending order of importance"""

keywords_list = ""

if job_description.strip() :
    response = client.responses.create(
            model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
            input=[{"role": "user", "content": prompt}],
        )
    keywords_list = split_bulleted_pointers(response.output_text)




for r in resume_pointers:
    r.match(keywords_list)
    r.render()
    

with st.sidebar:
    st.header("KeyWords")
    i = 1
    for keyword in keywords_list:

        k = Keyword(keyword, 0, i)
        k.update_frequency(resume_pointers)
        k.render()
        i = i+1

 
        

  
