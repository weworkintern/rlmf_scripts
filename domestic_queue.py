import streamlit as st
from streamlit_shortcuts import button
from streamlit_scroll_navigation import scroll_navbar
import polars as pl
from constants import SCROLLBAR_STYLES
from utils import clean_text

st.set_page_config(layout="wide", page_title="RLMF Domestic Queue", page_icon="👀")

default_state = {
    "current_index": 0,
}

for key, default_value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

current_index = st.session_state.get("current_index", 0)


def next_evaluation():
    st.session_state["current_index"] += 1


def previous_evaluation():
    st.session_state["current_index"] -= 1


@st.cache_data
def read_file(file_path: str) -> pl.DataFrame:
    return pl.read_ndjson(file_path)


def process_step(step_text: str) -> str:
    return clean_text(step_text.replace("\n", "\n\n"), "response")


evaluation_file = st.file_uploader("Upload exported data", type=["jsonl"])

if evaluation_file:
    df = read_file(evaluation_file)

    curr_df = df.slice(current_index, 1)

    answer_data = curr_df["Answer"].item()["data"]

    steps = answer_data["step_info"]

    stats = {
        "question_id": curr_df["link"].item(),
    }

    st.table(stats)

    st.header("Prompt", anchor="Prompt")
    st.write(process_step(answer_data["prompt"]))

    st.header("Reasoning Steps", anchor="Reasoning Steps")

    critique_rounds = 0
    intervene_rounds = 0

    for step in steps:
        if step["final_type"] == "critique":
            st.subheader("", anchor=f"Round {critique_rounds + intervene_rounds + 1}")
            st.error(process_step(step["think"]))
            st.info(
                process_step(
                    step["critique"] if step["critique"] else step["critique_temp"]
                )
            )
            critique_rounds += 1
        elif step["final_type"] == "intervene" or step["origint_think"]:
            st.subheader("", anchor=f"Round {critique_rounds + intervene_rounds + 1}")
            st.error(process_step(step["origint_think"]))
            st.warning(process_step(step["intervene"]))
            intervene_rounds += 1
        elif step["final_answer"]:
            st.header("Final Answer", anchor="Final Answer")
            st.write(process_step(step["final_answer"]))
        else:
            st.write(process_step(step["think"]))

    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            button(
                "Previous", "ArrowLeft", previous_evaluation, use_container_width=True
            )
        with col2:
            button("Next", "ArrowRight", next_evaluation, use_container_width=True)

        st.subheader("Navigation")
        scroll_navbar(
            key="main",
            anchor_ids=["Prompt", "Reasoning Steps", "Final Answer", "Raw Data"],
            override_styles=SCROLLBAR_STYLES,
        )

        st.subheader("Annotations")
        scroll_navbar(
            key="annotation_rounds",
            anchor_ids=list(
                map(
                    lambda x: f"Round {x}",
                    range(1, intervene_rounds + critique_rounds + 1),
                )
            ),
            override_styles=SCROLLBAR_STYLES,
        )

    st.header("Raw Data", anchor="Raw Data")
    st.dataframe(curr_df)
    st.json(curr_df["Answer"].item())
