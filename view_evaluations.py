import streamlit as st
import polars as pl
import os
import json
from streamlit_shortcuts import button
from dotenv import load_dotenv

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
    "abandon_prompt_reason": "Abandon Prompt Reason",
}

DATA_INFO = [
    "task id",
    "model name",
    "abandon_prompt",
    "temperature",
    "intervention rounds",
    "CoT quality",
    "Model performance classification",
    "codeforces_submission_id",
    "programming_language",
    "total_tokens",
]

print(os.path.join(DATA_DIR, "evaluations.json"))
df = pl.read_json(os.path.join(DATA_DIR, "evaluations.json"))


if "button_key_counter" not in st.session_state:
    st.session_state["button_key_counter"] = 0

if "current_index" not in st.session_state:
    st.session_state["current_index"] = 0

def previous_evaluation():
    st.session_state["current_index"] -= 1

def next_evaluation():
    st.session_state["current_index"] += 1

def clean_text(text: str) -> str:
    text = text.replace("\\n", "\n")
    text = text.replace("\\\\", "$")
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

def parse_tokens(text: str) -> None:
    """Parse text with XML-style tokens and display with appropriate Streamlit styling."""
    # Process the text until no more tokens are found
    remaining_text = text
    token_counts = {
        "abandon": 0,
        "reason": 0,
        "intervene": 0,
    }
    while True:
        # Find the next token
        next_token_start = float('inf')
        found_token = None
        
        for token in ["abandon", "reason", "intervene"]:
            start = remaining_text.find(f"<{token}>")
            if start != -1 and start < next_token_start:
                next_token_start = start
                found_token = token
        
        if found_token is None:
            # No more tokens found, display remaining text as markdown
            if remaining_text.strip():
                st.markdown(remaining_text.strip())
            break
            
        # Display text before the token
        if next_token_start > 0:
            st.markdown(remaining_text[:next_token_start].strip())
            
        # Find the end of the token content
        token_end = remaining_text.find(f"</{found_token}>", next_token_start)
        if token_end == -1:
            # If no closing tag, treat rest as normal text
            st.markdown(remaining_text[next_token_start:].strip())
            break
            
        # Extract the content between tags
        content_start = next_token_start + len(found_token) + 2  # +2 for "<>"
        content = remaining_text[content_start:token_end].strip()
        
        # Apply appropriate styling based on token type
        if found_token == "abandon":
            token_counts["abandon"] += 1
            st.error(f"**{found_token} {token_counts['abandon']}:**\n{content}")
        elif found_token == "reason":
            token_counts["reason"] += 1
            st.info(f"**{found_token} {token_counts['reason']}:**\n{content}")
        elif found_token == "intervene":
            token_counts["intervene"] += 1
            st.warning(f"**{found_token} {token_counts['intervene']}:**\n{content}")
            
        # Update remaining text
        remaining_text = remaining_text[token_end + len(found_token) + 3:]  # +3 for "</>"

current_index = st.session_state.get("current_index", 0)

# Buttons to control current index
col1, col2 = st.columns(2)
with col1:
    button("Previous", "ArrowLeft", previous_evaluation, use_container_width=True)
with col2:
    button("Next", "ArrowRight", next_evaluation, use_container_width=True)

search = st.text_input("Search by task ID", key="search", on_change=search_evaluation)

curr_df = df.slice(current_index, 1)

# Data info
st.header("Data Info")
data_info = {key: curr_df.get_column(key).item() for key in DATA_INFO}
st.table(data_info)

# Remarks
st.header("Remarks")
remarks = curr_df.get_column("remarks").item()
remarks = remarks.replace("'", '"')
st.table((json.loads(remarks)["remarks"]))

st.divider()

for (name, title) in DATA_VALS.items():
    val = curr_df.get_column(name).item()
    if not val:
        st.header(title)
        st.write("No value")
        continue
    st.header(title)
    val = clean_text(val)
    val = parse_tokens(val)
    st.divider()

st.divider()
st.dataframe(curr_df)