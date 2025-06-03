import streamlit as st
import polars as pl
import ast
import os
from streamlit_shortcuts import button
from dotenv import load_dotenv
from streamlit_scroll_navigation import scroll_navbar
from utils import parse_and_render_text, clean_text
from constants import DATA_VALS, DATA_INFO, SCROLLBAR_STYLES, FILTER_OPTIONS

load_dotenv(override=True)
DATA_DIR = os.getenv("DATA_DIR", "./data")

# df = pl.read_json(os.path.join(DATA_DIR, "evaluations.json"))

st.set_page_config(layout="wide", page_title="CoT Viewer", page_icon="👀")

@st.cache_data
def read_file(file_path: str, file_type: str) -> pl.DataFrame:
    if file_type == "application/json":
        return pl.read_json(file_path)
    elif file_type == "text/csv":
        return pl.read_csv(file_path)

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
        st.session_state["current_index"] = match_index

def fetch_filtered_df():
    filtered_df = st.session_state["df"]
    filter_choices = st.session_state.get("filter_choices", [])
    abandon_choices = st.session_state.get("abandon_choices", [])
    classification_choices = st.session_state.get("classification_choices", [])
    acc_choices = st.session_state.get("acc_choices", [])
    if "Abandoned" in filter_choices:
        filtered_df = filtered_df.filter(pl.col("abandon_prompt") == "Yes")
    if "Has interventions" in filter_choices:
        filtered_df = filtered_df.filter(pl.col("intervention rounds") > 0)
    if len(abandon_choices) > 0:
        filtered_df = filtered_df.filter(pl.col("abandon_prompt_reason").is_in(abandon_choices))
    if len(classification_choices) > 0:
        filtered_df = filtered_df.filter(pl.col("Model performance classification").is_in(classification_choices))
    if len(acc_choices) > 0:
        filtered_df = filtered_df.filter(pl.col("ACC").cast(pl.Float64, strict=False).is_in(acc_choices))
    return filtered_df

def get_filtered_indices():
    """Get the indices from the original dataframe that match the current filters."""
    filtered_df = fetch_filtered_df()
    # Get task IDs from filtered df
    filtered_task_ids = filtered_df.get_column("task id").to_list()
    # Get indices from original df where task ID matches filtered task IDs
    original_indices = st.session_state["df"].with_row_index("index").filter(
        pl.col("task id").is_in(filtered_task_ids)
    ).get_column("index").to_list()
    return original_indices

def previous_evaluation():
    filtered_indices = get_filtered_indices()
    if not filtered_indices:
        return
        
    # Find the current position in filtered indices
    try:
        current_pos = filtered_indices.index(st.session_state["current_index"])
        # Move to previous position in filtered indices
        if current_pos > 0:
            st.session_state["current_index"] = filtered_indices[current_pos - 1]
        else:
            st.session_state["current_index"] = filtered_indices[-1]
    except ValueError:
        # If current index not in filtered set, move to last filtered index
        st.session_state["current_index"] = filtered_indices[-1]
    
    # Update search with task ID from original dataframe
    st.session_state["search"] = str(st.session_state["df"].slice(st.session_state["current_index"], 1).get_column("task id").item())

def next_evaluation():
    filtered_indices = get_filtered_indices()
    if not filtered_indices:
        return
        
    # Find the current position in filtered indices
    try:
        current_pos = filtered_indices.index(st.session_state["current_index"])
        # Move to next position in filtered indices
        if current_pos < len(filtered_indices) - 1:
            st.session_state["current_index"] = filtered_indices[current_pos + 1]
        else:
            st.session_state["current_index"] = filtered_indices[0]
    except ValueError:
        # If current index not in filtered set, move to first filtered index
        st.session_state["current_index"] = filtered_indices[0]
    
    # Update search with task ID from original dataframe
    st.session_state["search"] = str(st.session_state["df"].slice(st.session_state["current_index"], 1).get_column("task id").item())

@st.dialog("Search Results")
def search_for_string():
    search_term = st.session_state.get("search_string", "")
    if not search_term:
        return
    
    df = st.session_state["df"]

    matches = df.filter(pl.col("user prompt").str.contains_any([search_term], ascii_case_insensitive=True) | pl.col("response").str.contains_any([search_term], ascii_case_insensitive=True))
    if matches.shape[0] > 0:
        st.write(f"There are {matches.shape[0]} matches for '{search_term}'")
        for i in range(matches.shape[0]):
            task_id = matches.get_column('task id').item(i)
            prompt_item = matches.get_column('user prompt').item(i)
            response_item = matches.get_column('response').item(i)

            if st.button(f"Task {task_id}"):
                st.session_state["search"] = str(task_id)
                search_evaluation()
                st.rerun()

            if search_term.lower() in prompt_item.lower():
                idx = prompt_item.lower().index(search_term.lower())
                prefix = "**Prompt:** "
                if idx > 50 and len(prompt_item) - idx > 50:
                    st.write(f"{prefix}...{prompt_item[idx-50:idx+50]}...")
                elif idx <= 50:
                    st.write(f"{prefix}{prompt_item[:100]}...")
                else:
                    st.write(f"{prefix}...{prompt_item[-100:]}")
            if search_term.lower() in response_item.lower():
                idx = response_item.lower().index(search_term.lower())
                prefix = "**Response:** "
                if idx > 50 and len(response_item) - idx > 50:
                    st.write(f"{prefix}...{response_item[idx-50:idx+50]}...")
                elif idx <= 50:
                    st.write(f"{prefix}{response_item[:100]}...")
                else:
                    st.write(f"{prefix}...{response_item[-100:]}")
            st.divider()
    else:
        st.write(f"No matches found for '{search_term}'")

# Initialize session state variables with default values
default_state = {
    "button_key_counter": 0,
    "current_index": 0,
    "search_string": "",
    "abandon_options": [],
    "classification_options": [],
    "acc_options": [],
    "filter_options": [],
    "abandon_choices": [],
    "classification_choices": [],
    "acc_choices": [],
    "filter_choices": []
}

for key, default_value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

current_index = st.session_state.get("current_index", 0)

evaluations_file = st.file_uploader("Upload evaluations file", type=["json", "csv"])
if evaluations_file:
    df = read_file(evaluations_file, evaluations_file.type)

    curr_df = df.slice(current_index, 1)

    st.session_state["df"] = df
    st.session_state["curr_df"] = curr_df

    abandon_options = df.get_column("abandon_prompt_reason").unique().to_list()
    classification_options = df.get_column("Model performance classification").unique().to_list()
    acc_options = []
    if "ACC" in df.columns:
        acc_options = df.get_column("ACC").cast(pl.Float64, strict=False).unique().to_list()

    st.session_state["abandon_options"] = abandon_options
    st.session_state["classification_options"] = classification_options
    st.session_state["acc_options"] = acc_options

    with st.sidebar:
        st.text_input("Search by task ID", key="search", on_change=search_evaluation, placeholder="e.g. 60000")

        # Buttons to control current index
        col1, col2 = st.columns(2)
        with col1:
            button("Previous", "ArrowLeft", previous_evaluation, use_container_width=True)
        with col2:
            button("Next", "ArrowRight", next_evaluation, use_container_width=True)
        
        st.subheader("Search filters")
        
        # Show filtered row count
        if st.session_state.get("df") is not None:
            filtered_df = fetch_filtered_df()
            total_rows = len(st.session_state["df"])
            filtered_rows = len(filtered_df)
            st.text(f"Showing {filtered_rows} of {total_rows} rows")
        
        st.text_input("Search in prompt and response", key="search_string", on_change=search_for_string)

        # Use current values from session state as defaults
        st.multiselect(
            "Additional filters",
            FILTER_OPTIONS,
            default=st.session_state.get("filter_choices", []),
            key="filter_choices"
        )

        # Dynamic filters with preserved selections
        st.multiselect(
            "Abandon reason filters",
            st.session_state["abandon_options"],
            default=st.session_state.get("abandon_choices", []),
            key="abandon_choices"
        )

        st.multiselect(
            "Model performance classification",
            st.session_state["classification_options"],
            default=st.session_state.get("classification_choices", []),
            key="classification_choices"
        )

        st.multiselect(
            "ACC level",
            st.session_state["acc_options"],
            default=st.session_state.get("acc_choices", []),
            key="acc_choices"
        )

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
    
    # Only calculate correlations if ACC column exists
    calcs = {}
    if "ACC" in df.columns:
        calcs["correlation"] = df.filter(pl.col("ACC").is_not_null()).select(pl.corr(pl.col("intervention rounds"), pl.col("ACC"), method="pearson")).item()
        calcs["correlation w/o ACC = 0"] = df.filter((pl.col("ACC").cast(pl.Float64, strict=False).is_not_null()) & (pl.col("ACC").cast(pl.Float64, strict=False) > 0)).select(pl.corr(pl.col("intervention rounds"), pl.col("ACC"), method="pearson")).item()
        calcs_df = pl.DataFrame({"stat": list(calcs.keys()), "value": list(calcs.values())})
    else:
        calcs_df = pl.DataFrame({"stat": ["Note"], "value": ["ACC column not present in data"]})

    st.table(stats.unpivot(variable_name="category", value_name="count"))
    st.table(calcs_df)

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
        if name not in curr_df.columns:
            continue
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

# Hide all anchor icons
st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")
