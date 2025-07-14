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
    return step_text.replace("\n", "\n\n")


def retrieve_stats(df: pl.DataFrame) -> pl.DataFrame:
    stats = pl.DataFrame(
        {
            "total": len(df),
            "abandoned": df.filter(
                pl.col("Answer").struct.field("data").struct.field("fake_abandon")
                == "Yes"
            ).shape[0],
            "zero_interventions": df.filter(
                pl.col("Answer").struct.field("data").struct.field("cot_qualify")
                == "Perfect"
            ).shape[0],
        }
    )
    stats = stats.with_columns(
        (pl.col("total") - pl.col("abandoned") - pl.col("zero_interventions")).alias(
            "effective"
        )
    )
    return stats


evaluation_file = st.file_uploader("Upload exported data", type=["jsonl"])

if evaluation_file:
    df = read_file(evaluation_file)

    curr_df = df.slice(current_index, 1)

    answer_data = curr_df["Answer"].item()["data"]

    steps = answer_data["step_info"]

    st.header("Data Info", anchor="Data Info")
    st.subheader("All Cases")
    stats = retrieve_stats(df)
    st.table(stats.unpivot(variable_name="category", value_name="value"))

    st.subheader("Current Case")
    stats = pl.DataFrame(
        {
            "question_id": curr_df["link"].item(),
            "cot_quality": answer_data["cot_qualify"],
            "abandoned": answer_data["fake_abandon"] == "Yes",
            "model_performance": answer_data["model_performance"][0],
            "submission_id": answer_data["submission_id"],
            "item_id": curr_df["ItemID"],
            "task_id": curr_df["TaskID"],
            "operator": curr_df["Operator"],
        }
    ).unpivot(variable_name="category", value_name="value")

    st.table(stats)

    st.header("Prompt", anchor="Prompt")
    st.write(clean_text(answer_data["prompt"], "prompt"))

    st.header("Reasoning Steps", anchor="Reasoning Steps")

    critique_rounds = 0
    intervene_rounds = 0
    annotation_rounds = []

    for step in steps:
        if step["final_type"] == "critique":
            critique_rounds += 1
            annotation_rounds.append(
                {"annotation_type": "Critique", "round_number": critique_rounds}
            )
            st.subheader("", anchor=f"Critique {critique_rounds}")
            st.error(process_step(step["think"]))
            st.info(
                process_step(
                    step["critique"] if step["critique"] else step["critique_temp"]
                )
            )
        elif step["final_type"] == "intervene" or step["origint_think"]:
            intervene_rounds += 1
            annotation_rounds.append(
                {"annotation_type": "Intervene", "round_number": intervene_rounds}
            )
            st.subheader("", anchor=f"Intervene {intervene_rounds}")
            st.error(process_step(step["origint_think"]))
            st.warning(process_step(step["intervene"]))
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

        if len(annotation_rounds) > 0:
            st.subheader("Annotations")
            scroll_navbar(
                key="annotation_rounds",
                anchor_ids=list(
                    map(
                        lambda x: f"{x['annotation_type']} {x['round_number']}",
                        annotation_rounds,
                    )
                ),
                override_styles=SCROLLBAR_STYLES,
            )

    st.header("Ground Truth", anchor="Ground Truth")
    st.write("```cpp\n" + answer_data["gt_answer"] + "\n```")

    st.header("Raw Data", anchor="Raw Data")
    st.dataframe(curr_df)
    st.json(curr_df["Answer"].item())
