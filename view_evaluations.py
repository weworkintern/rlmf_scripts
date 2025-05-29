import streamlit as st
import polars as pl
import os
import json
from streamlit_shortcuts import button
from dotenv import load_dotenv
from streamlit_scroll_navigation import scroll_navbar
import re

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

def format_examples(text):
    def replacement(match):
        input_text = match.group(1)
        output_text = match.group(2)
        return f"\n---\n\n```\n{input_text}\n```\n\n```\n{output_text}\n```"
    
    # Replace each example in-place
    return re.sub(r"\\exmp\{(.*?)\}\{(.*?)\}%", replacement, text, flags=re.DOTALL)

def clean_text(text: str, category: str) -> str:
    text = text.replace("\\\\(", "$")
    text = text.replace("\\\\)", "$")
    text = text.replace("\\\\[", "$")
    text = text.replace("\\\\]", "$")
    text = text.replace("\\InputFile", "")
    text = text.replace("\\OutputFile", "")
    text = text.replace("\\Note", "")
    
    # Find all examples and display them as tables
    text = format_examples(text)
    
    # Remove the example markers from the text
    text = re.sub(r"\\exmp\{(.*?)\}\{(.*?)\}%", "", text)
    text = re.sub(r"\\begin\{problem\}.*?megabytes\}", "", text)
    text = re.sub(r"\\begin\{center\}.*\\includegraphics.*?\\end\{center\}", "*(A graphic is shown here in the original problem.)*", text)
    text = re.sub(r"\\end\{problem\}", "", text)
    text = re.sub(r"\\textit\{(.*?)\}", r"*\1*", text)
    text = re.sub(r"\\textbf\{(.*?)\}", r"**\1**", text)

    if category != "response":
        text = re.sub(r"\\n(?!e )", "\n", text)
    else:
        text = re.sub(r"\\n\\n", "\n", text)
        text = re.sub(r"\\n(?!e )(?!\\n)", "  \n", text)
    text = re.sub(r"\\t(?!imes)", r"\t", text)
    text = text.replace("\\begin{example}", "")
    text = text.replace("\\end{example}", "")
    return text

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

def parse_and_render_text(text: str) -> None:
    """Split text by token tags and render each chunk with appropriate Streamlit component."""
    tokens = {
        "abandon": st.error,
        "reason": st.info,
        "intervene": st.warning
    }
    token_count = {token: 1 for token in tokens}
    
    # Process the text to find and display chunks
    remaining_text = text
    while any(f"<{token}>" in remaining_text for token in tokens):
        # Find the first occurrence of any token
        token_positions = {token: remaining_text.find(f"<{token}>") for token in tokens}
        token_positions = {token: pos for token, pos in token_positions.items() if pos != -1}
        
        if not token_positions:
            break
            
        # Find which token comes first
        current_token = min(token_positions, key=token_positions.get)
        start_pos = token_positions[current_token]
        
        # Display text before the token
        if start_pos > 0:
            st.write(remaining_text[:start_pos], unsafe_allow_html=True)
        
        # Find the end of this token section
        token_start = start_pos + len(f"<{current_token}>")
        end_tag = f"</{current_token}>"
        end_pos = remaining_text.find(end_tag, token_start)
        
        if end_pos == -1:  # No closing tag found
            # Display the token name and rest of text
            st.subheader("", anchor=f"Round {token_count[current_token]}")
            tokens[current_token](f"**{current_token.upper()} {token_count[current_token]}:** {remaining_text[token_start:]}")
            token_count[current_token] += 1
            remaining_text = ""
        else:
            # Display the content with the appropriate component
            st.subheader("", anchor=f"Round {token_count[current_token]}")
            token_content = remaining_text[token_start:end_pos]
            tokens[current_token](f"**{current_token.upper()} {token_count[current_token]}:** {token_content}")
            token_count[current_token] += 1
            # Update remaining text
            remaining_text = remaining_text[end_pos + len(end_tag):]
    
    # Display any remaining text
    if remaining_text:
        st.write(remaining_text, unsafe_allow_html=True)

if "button_key_counter" not in st.session_state:
    st.session_state["button_key_counter"] = 0

if "current_index" not in st.session_state:
    st.session_state["current_index"] = 0

def previous_evaluation():
    st.session_state["current_index"] -= 1

def next_evaluation():
    st.session_state["current_index"] += 1

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
    data_info = {}
    for key in DATA_INFO:
        if key in curr_df.columns:
            data_info[key] = curr_df.get_column(key).item()
    st.table(data_info)

    # Remarks
    st.header("Remarks", anchor="Remarks")
    remarks = curr_df.get_column("remarks").item()
    remarks = remarks.replace("'", '"')
    st.table((json.loads(remarks)["remarks"]))

    st.divider()

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
