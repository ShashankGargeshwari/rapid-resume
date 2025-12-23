import streamlit as st


st.set_page_config(page_title="Rapid Resume", page_icon="📝", layout="centered")
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
pointer_groups = {
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

with st.sidebar:
    st.header("Pointer Library")
    st.caption("Select items to add to the resume pointers box.")
    tabs = st.tabs(list(pointer_groups.keys()))
    for tab, (group_name, pointers) in zip(tabs, pointer_groups.items()):
        with tab:
            for idx, pointer in enumerate(pointers):
                key = f"pointer_{group_name}_{idx}"
                st.session_state.setdefault(
                    key, pointer in st.session_state["selected_pointers"]
                )
                st.checkbox(
                    pointer,
                    key=key,
                    on_change=sync_selected_pointer,
                    args=(pointer, key),
                )

selected_pointers = list(st.session_state["selected_pointers"])
current_lines = [
    line.strip()
    for line in st.session_state["resume_pointers_text"].splitlines()
    if line.strip()
]
kept_lines = [
    line
    for line in current_lines
    if line not in all_pointers or line in selected_pointers
]
for pointer in selected_pointers:
    if pointer not in kept_lines:
        kept_lines.append(pointer)
computed_text = "\n".join(kept_lines)

resume_pointers = st.text_area(
    "Resume pointers",
    placeholder="Generated resume pointers will appear here.",
    height=160,
    value=computed_text,
)
st.session_state["resume_pointers_text"] = resume_pointers
if not resume_pointers.strip():
    st.caption("Use this space to draft impact statements aligned to the role.")
