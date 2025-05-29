import streamlit as st
import polars as pl
import os
import json
from streamlit_shortcuts import button
from dotenv import load_dotenv
from streamlit_scroll_navigation import scroll_navbar
from utils import parse_and_render_text, clean_text
import ast

load_dotenv(override=True)
DATA_DIR = os.getenv("DATA_DIR", "./data")

DATA_VALS = {
    "user prompt": "User Prompt",
    "response": "Response",
    "system prompt": "System Prompt",
    "intervene_system_prompt": "Intervene System Prompt",
    "intervene prompt": "Intervene User Prompt",
    "final_answer": "Final Answer",
    "ground_truth_answer": "Ground Truth Answer",
}

DATA_INFO = [
    "task id",
    "trainer id",
    "model name",
    "abandon_prompt",
    "abandon_prompt_reason",
    "temperature",
    "intervention rounds",
    "CoT quality",
    "Model performance classification",
    "codeforces_submission_id",
    "programming_language",
    "total_tokens",
    "ACC",
    "level",
]

SCROLLBAR_STYLES = {
    "navbarButtonBase": {
        "backgroundColor": "#f4f3ed",
        "color": "#222",
        "borderColor": "#d3d2ca"
    },
    "navbarButtonActive": {
        "backgroundColor": "#bb5a38",
        "color": "#fff",
        "borderColor": "#bb5a38"
    },
    "navbarButtonHover": {
        "backgroundColor": "#ecebe3",
        "secondaryBackgroundColor": "#ecebe3",
        "color": "#222",
        "linkColor": "#222",
        "borderColor": "#bb5a38"
    },
    "navigationBarBase": {
        "backgroundColor": "#f4f3ed",
        "color": "#222",
        "borderColor": "#d3d2ca"
    }
}
# df = pl.read_json(os.path.join(DATA_DIR, "evaluations.json"))

st.set_page_config(layout="wide", page_title="CoT Viewer", page_icon="👀")

@st.cache_data
def read_file(file_path: str, file_type: str) -> pl.DataFrame:
    if file_type == "application/json":
        return pl.read_json(file_path)
    elif file_type == "text/csv":
        return pl.read_csv(file_path)

if "button_key_counter" not in st.session_state:
    st.session_state["button_key_counter"] = 0

if "current_index" not in st.session_state:
    st.session_state["current_index"] = 0

def search_evaluation():
    """Search for a task ID and update the current index."""
    search_term = st.session_state.get("search", "")
    if not search_term:
        return
        
    # Convert task IDs to strings for searching
    task_ids = df.get_column("task id").cast(pl.Utf8)
    # Find the index of the first matching task ID
    matches = task_ids.str.contains(search_term)
    if matches.any():
        match_index = matches.arg_true().item(0)  # Get the first match index
        print(f"Match index: {match_index}")
        st.session_state["current_index"] = match_index

def previous_evaluation():
    if st.session_state["current_index"] > 0:
        st.session_state["current_index"] -= 1
    else:
        st.session_state["current_index"] = len(df) - 1
    st.session_state["search"] = str(df.slice(st.session_state["current_index"], 1).get_column("task id").item())

def next_evaluation():
    if st.session_state["current_index"] < len(df) - 1:
        st.session_state["current_index"] += 1
    else:
        st.session_state["current_index"] = 0
    st.session_state["search"] = str(df.slice(st.session_state["current_index"], 1).get_column("task id").item())

current_index = st.session_state.get("current_index", 0)

evaluations_file = st.file_uploader("Upload evaluations file", type=["json", "csv"])
if evaluations_file:
    df = read_file(evaluations_file, evaluations_file.type)

    curr_df = df.slice(current_index, 1)

    with st.sidebar:
        # Buttons to control current index
        col1, col2 = st.columns(2)
        with col1:
            button("Previous", "ArrowLeft", previous_evaluation, use_container_width=True)
        with col2:
            button("Next", "ArrowRight", next_evaluation, use_container_width=True)
        search = st.text_input("Search by task ID", key="search", on_change=search_evaluation)
        st.subheader("Navigation")
        scroll_navbar(
            key="main",
            anchor_ids=[
                "Data Info",
                "Remarks",
                *DATA_VALS.values(),
                "Raw Data"
            ],
            override_styles=SCROLLBAR_STYLES
        )
        if curr_df.get_column("intervention rounds").item() > 0:
            st.subheader("Intervention Rounds")
            scroll_navbar(
                key="intervention_rounds",
                anchor_ids=list(map(lambda x: f"Round {x}", range(1, curr_df["intervention rounds"].item() + 1))),
                override_styles=SCROLLBAR_STYLES
            )
    
    st.header("Instructions")
    st.info("Use the navigation bar to quickly jump to the prompts, responses and interventions.  \nYou can search by task ID, and use the arrow keys to switch between cases.")

    # Data info
    st.header("Data Info", anchor="Data Info")
    st.subheader("All Cases")
    stats = pl.DataFrame({
        "total": len(df),
        "abandoned": df.filter(pl.col("abandon_prompt") == "Yes").shape[0],
        "zero_interventions": df.filter(pl.col("intervention rounds") == 0).shape[0],
        "effective": len(df) - df.filter(pl.col("abandon_prompt_reason").is_not_null()).shape[0] - df.filter(pl.col("intervention rounds") == 0).shape[0],
        "abandoned_and_no_interventions": df.filter((pl.col("abandon_prompt") == "Yes") & (pl.col("intervention rounds") == 0)).shape[0],
    })
    
    if stats["abandoned_and_no_interventions"].item() > 0:
        st.error(f"Sanity check failed: There are {stats['abandoned_and_no_interventions'].item()} cases where the case was abandoned and no interventions were made.")
    
    calcs = pl.DataFrame({
        "correlation": df.filter(pl.col("ACC").is_not_null()).select(pl.corr(pl.col("intervention rounds"), pl.col("ACC"), method="pearson")).item(),
        "correlation w/o ACC = 0": df.filter((pl.col("ACC").cast(pl.Float64, strict=False).is_not_null()) & (pl.col("ACC").cast(pl.Float64, strict=False) > 0)).select(pl.corr(pl.col("intervention rounds"), pl.col("ACC"), method="pearson")).item(),
    })

    st.table(stats.unpivot(variable_name="category", value_name="count"))
    st.table(calcs.unpivot(variable_name="stat", value_name="value"))

    st.subheader("Current Case")
    data_info = {}
    for key in DATA_INFO:
        if key in curr_df.columns:
            data_info[key] = curr_df.get_column(key).item()
    st.table(data_info)

    # Remarks
    st.header("Remarks", anchor="Remarks")
    remarks = curr_df.get_column("remarks").item()
    remarks_dict = ast.literal_eval(remarks)
    st.table(remarks_dict["remarks"])

    for (name, title) in DATA_VALS.items():
        val = curr_df.get_column(name).item()
        st.header(title, anchor=title)
        if not val:
            st.write("No value")
            continue
        val = clean_text(val, name)
        if name != "final_answer" and name != "ground_truth_answer":
            val = val.replace("\n", "\n\n")
        if name == "ground_truth_answer":
            if not val.startswith("```"):
                val = "```cpp\n" + val + "\n```"
        if name == "response":
            parse_and_render_text(val)
        else:
            st.write(val, unsafe_allow_html=True)
        st.divider()

    st.header("Raw Data", anchor="Raw Data")
    st.dataframe(curr_df.unpivot(), height=800)
else:
    st.info("Upload an evaluation file to view")

st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")
