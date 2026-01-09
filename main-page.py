import json
import os
import sqlite3
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html
from openai import OpenAI


def get_db_path_and_warning() -> tuple[Path, str]:
    db_url = os.getenv("DATABASE_URL", "").strip()
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)
    default_path = data_dir / "resume_pointers.db"
    

    if not db_url:
        return default_path, ""

    if db_url.startswith("sqlite:///"):
        return Path(db_url.replace("sqlite:///", "", 1)).expanduser(), ""
    if db_url.startswith("sqlite://"):
        return Path(db_url.replace("sqlite://", "", 1)).expanduser(), ""

    return (
        default_path,
        "Non-SQLite DATABASE_URL detected. Falling back to local SQLite.",
    )


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS resume_pointers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            pointer TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.commit()


def seed_defaults(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS count FROM resume_pointers").fetchone()
    if row and row["count"]:
        return
    seed_path = Path(__file__).resolve().parent / "data" / "seed.json"
    seed_data: dict[str, list[str]] = {}
    if seed_path.exists():
        try:
            seed_data = json.loads(seed_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            seed_data = {}
    if not seed_data:
        seed_data = {
            "Product": [
                "Led cross-functional roadmap delivery for a 6-person squad.",
                "Defined product strategy with measurable quarterly OKRs.",
                "Improved activation rate by 18% through A/B testing.",
            ],
            "Design": [
                "Ran 12+ user interviews to validate early product direction.",
                "Shipped a new design system that reduced QA cycles by 30%.",
                "Prototyped and tested 5 flows in Figma before development.",
            ],
            "Data": [
                "Built analytics dashboards to track retention cohorts.",
                "Instrumented key events to improve funnel visibility.",
                "Partnered with data science to launch churn models.",
            ],
        }
    seed_rows = [
        (category, pointer)
        for category, pointers in seed_data.items()
        for pointer in pointers
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO resume_pointers (category, pointer) VALUES (?, ?)",
        seed_rows,
    )
    conn.commit()


def fetch_pointer_groups(conn: sqlite3.Connection) -> dict[str, list[str]]:
    rows = conn.execute(
        "SELECT category, pointer FROM resume_pointers ORDER BY category, id"
    ).fetchall()
    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(row["category"], []).append(row["pointer"])
    return groups


def add_pointer(conn: sqlite3.Connection, category: str, pointer: str) -> bool:
    try:
        conn.execute(
            "INSERT INTO resume_pointers (category, pointer) VALUES (?, ?)",
            (category, pointer),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_pointer(conn: sqlite3.Connection, pointer: str) -> None:
    conn.execute("DELETE FROM resume_pointers WHERE pointer = ?", (pointer,))
    conn.commit()


st.set_page_config(page_title="Rapid Resume", page_icon="📝", layout="centered")

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

prompt = "Hello, wassup"

response = client.responses.create(
        model="gpt-4o-mini",  # or "gpt-5.2" if you prefer :contentReference[oaicite:3]{index=3}
        input=[{"role": "user", "content": st.session_state.prompt}],
    )

st.markdown(response)

st.title("Rapid Resume")
st.caption("A minimal Streamlit starter app.")

st.write("Paste a job description to extract keywords and resume pointers.")

job_description = st.text_area(
    "Job description",
    placeholder="Paste the job description here.",
    height=180,
)

st.subheader("Keywords")
keyword_candidates = [
    "cross-functional collaboration",
    "product strategy",
    "user research",
    "A/B testing",
    "roadmapping",
    "stakeholder management",
    "analytics",
    "Figma",
    "Agile",
]
if job_description.strip():
    st.markdown("\n".join(f"- {keyword}" for keyword in keyword_candidates))
else:
    st.info("Add a job description to see extracted keywords.")

st.subheader("Resume Pointers")
db_path, db_warning = get_db_path_and_warning()
if db_warning:
    st.warning(db_warning)
with get_connection(db_path) as conn:
    ensure_schema(conn)
    seed_defaults(conn)
    pointer_groups = fetch_pointer_groups(conn)

all_pointers = [
    pointer for pointers in pointer_groups.values() for pointer in pointers
]

if "resume_pointers_text" not in st.session_state:
    st.session_state["resume_pointers_text"] = ""
if "selected_pointers" not in st.session_state:
    st.session_state["selected_pointers"] = set()


def sync_selected_pointer(pointer: str, key: str) -> None:
    if st.session_state.get(key):
        st.session_state["selected_pointers"].add(pointer)
    else:
        st.session_state["selected_pointers"].discard(pointer)


def normalize_line(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith(("-", "*")):
        stripped = stripped[1:].lstrip()
    return stripped

with st.sidebar:
    st.header("Pointer Library")
    st.caption("Select items to add to the resume pointers box.")
    if pointer_groups:
        tabs = st.tabs(list(pointer_groups.keys()))
        for tab, (group_name, pointers) in zip(tabs, pointer_groups.items()):
            with tab:
                add_key = f"add_pointer_{group_name}"
                add_input = st.text_input(
                    "Add a new pointer",
                    key=add_key,
                    placeholder="Write a new bullet...",
                )
                if st.button("Add", key=f"add_button_{group_name}"):
                    new_pointer = add_input.strip()
                    if new_pointer:
                        with get_connection(db_path) as conn:
                            ensure_schema(conn)
                            added = add_pointer(conn, group_name, new_pointer)
                        if added:
                            st.session_state["selected_pointers"].add(new_pointer)
                            st.session_state[f"pointer_{group_name}_{new_pointer}"] = True
                            st.success("Pointer added.")
                            st.rerun()
                        else:
                            st.info("That pointer already exists.")
                    else:
                        st.warning("Please enter a pointer first.")

                for idx, pointer in enumerate(pointers):
                    key = f"pointer_{group_name}_{pointer}"
                    st.session_state.setdefault(
                        key, pointer in st.session_state["selected_pointers"]
                    )
                    col_checkbox, col_remove = st.columns([0.9, 0.1])
                    with col_checkbox:
                        st.checkbox(
                            pointer,
                            key=key,
                            on_change=sync_selected_pointer,
                            args=(pointer, key),
                        )
                    with col_remove:
                        if st.button("✕", key=f"remove_{group_name}_{pointer}"):
                            with get_connection(db_path) as conn:
                                remove_pointer(conn, pointer)
                            st.session_state["selected_pointers"].discard(pointer)
                            st.session_state.pop(key, None)
                            current_lines = [
                                normalize_line(line)
                                for line in st.session_state[
                                    "resume_pointers_text"
                                ].splitlines()
                                if line.strip()
                            ]
                            updated_lines = [
                                line for line in current_lines if line != pointer
                            ]
                            st.session_state["resume_pointers_text"] = "\n".join(
                                f"- {line}" for line in updated_lines
                            )
                            st.rerun()
    else:
        st.info("No pointers available yet.")

selected_pointers = list(st.session_state["selected_pointers"])
current_lines_raw = [
    line
    for line in st.session_state["resume_pointers_text"].splitlines()
    if line.strip()
]
current_lines = [normalize_line(line) for line in current_lines_raw]
kept_lines = [
    line
    for line in current_lines
    if line not in all_pointers or line in selected_pointers
]
for pointer in selected_pointers:
    if pointer not in kept_lines:
        kept_lines.append(pointer)
computed_text = "\n".join(line for line in kept_lines)

resume_pointers = st.text_area(
    "Resume pointers",
    placeholder="Generated resume pointers will appear here.",
    height=160,
    value=computed_text,
)
st.session_state["resume_pointers_text"] = resume_pointers
if not resume_pointers.strip():
    st.caption("Use this space to draft impact statements aligned to the role.")
else:
    html(
        f"""
        <div style="display:flex; justify-content:flex-end; margin-top:8px;">
          <button
            style="padding:6px 10px; border-radius:6px; border:1px solid #ccc; background:#f7f7f7; cursor:pointer;"
            onclick="navigator.clipboard.writeText({resume_pointers!r}); this.textContent='Copied!'; setTimeout(() => this.textContent='Copy', 1200);"
          >
            Copy
          </button>
        </div>
        """,
        height=44,
    )
