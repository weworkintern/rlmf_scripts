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
# df = pl.read_json(os.path.join(DATA_DIR, "evaluations.json"))

st.set_page_config(layout="wide", page_title="CoT Viewer", page_icon="👀")

@st.cache_data
def read_file(file_path: str, file_type: str) -> pl.DataFrame:
    if file_type == "application/json":
        return pl.read_json(file_path)
    elif file_type == "text/csv":
        return pl.read_csv(file_path)

def display_example(input_text: str, output_text: str) -> None:
    """Display an example input/output pair in a Streamlit table."""
    st.table({
        "Input": [input_text],
        "Output": [output_text]
    })

def clean_text(text: str) -> str:
    text = text.replace("\\\\(", "$")
    text = text.replace("\\\\)", "$")
    text = text.replace("\\\\[", "$\n")
    text = text.replace("\\\\]", "$\n")
    text = text.replace("\\InputFile", "")
    text = text.replace("\\OutputFile", "")
    text = text.replace("\\Note", "")
    
    # Find all examples and display them as tables
    examples = re.findall(r"\\exmp\{(.*?)\}\{(.*?)\}%", text)
    if examples:
        st.write("### Examples")
    for input_text, output_text in examples:
        display_example(
            input_text.replace('\\n', '\n'),
            output_text.replace('\\n', '\n')
        )
    
    # Remove the example markers from the text
    text = re.sub(r"\\exmp\{(.*?)\}\{(.*?)\}%", "", text)
    text = re.sub(r"\\begin\{problem\}.*?megabytes\}", "", text)
    text = re.sub(r"\\begin\{center\}.*\\includegraphics.*?\\end\{center\}", "*(A graphic is shown here in the original problem.)*", text)
    text = re.sub(r"\\end\{problem\}", "", text)

    text = text.replace("\\n", "\n")
    text = re.sub(r"\\t(!imes)", r"\t\1", text)
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
            st.markdown(remaining_text[:start_pos], unsafe_allow_html=True)
        
        # Find the end of this token section
        token_start = start_pos + len(f"<{current_token}>")
        end_tag = f"</{current_token}>"
        end_pos = remaining_text.find(end_tag, token_start)
        
        if end_pos == -1:  # No closing tag found
            # Display the token name and rest of text
            tokens[current_token](f"**{current_token.upper()} {token_count[current_token]}:** {remaining_text[token_start:]}")
            token_count[current_token] += 1
            remaining_text = ""
        else:
            # Display the content with the appropriate component
            token_content = remaining_text[token_start:end_pos]
            tokens[current_token](f"**{current_token.upper()} {token_count[current_token]}:** {token_content}")
            token_count[current_token] += 1
            # Update remaining text
            remaining_text = remaining_text[end_pos + len(end_tag):]
    
    # Display any remaining text
    if remaining_text:
        st.markdown(remaining_text, unsafe_allow_html=True)

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

    with st.sidebar:
        st.subheader("Navigation")
        scroll_navbar(
            anchor_ids=[
                "Data Info",
                "Remarks",
                *DATA_VALS.values()
            ],
            override_styles={
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
        )

    # Buttons to control current index
    col1, col2 = st.columns(2)
    with col1:
        button("Previous", "ArrowLeft", previous_evaluation, use_container_width=True)
    with col2:
        button("Next", "ArrowRight", next_evaluation, use_container_width=True)

    search = st.text_input("Search by task ID", key="search", on_change=search_evaluation)

    curr_df = df.slice(current_index, 1)

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
        val = clean_text(val)
        if name != "final_answer":
            val = val.replace("\n", "\n\n")
        if name == "ground_truth_answer":
            if not val.startswith("```"):
                val = "```cpp\n" + val + "\n```"
        if name == "response":
            parse_and_render_text(val)
        else:
            st.markdown(val, unsafe_allow_html=True)
        st.divider()

    st.dataframe(curr_df)
else:
    st.info("Upload an evaluation file to view")