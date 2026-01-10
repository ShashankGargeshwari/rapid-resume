import json
import os
import sqlite3
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html
from openai import OpenAI



st.set_page_config(page_title="Rapid Resume", page_icon="📝", layout="centered")

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

prompt = "Hello, wassup"
st.session_state.prompt = prompt

response = client.responses.create(
        model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
        input=[{"role": "user", "content": st.session_state.prompt}],
    )

st.markdown(response.output_text)