import streamlit as st
import re
from collections import defaultdict

def format_examples(text, add_flag=False):
    def replacement(match):
        input_text = match.group(1)
        output_text = match.group(2)
        return f"\n\nInput:\n```\n{input_text}\n```\n\nOutput:\n```\n{output_text}\n```\n"
    
    # Replace each example in-place
    return re.sub(r"\\exmp\{(.*?)\}\{(.*?)\}%", replacement, text, flags=re.DOTALL)

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

def convert_latex_to_lists(text):
    # Track nesting level and list types
    level = 0
    list_stack = []  # Stack to track if current level is enumerate or itemize
    
    # Dictionary to track count at each level (for enumerate only)
    counters = defaultdict(int)
    
    # Process the text line by line
    lines = text.split('\n')
    result = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        original_line = lines[i]  # Keep original line with whitespace
        
        # Check for begin enumerate or itemize
        if re.match(r'\\begin\s?\{(enumerate|itemize)\}', line):
            match = re.match(r'\\begin\s?\{(enumerate|itemize)\}', line)
            list_type = match.group(1)
            
            level += 1
            list_stack.append(list_type)
            
            # Initialize counter for this level if it's enumerate
            if list_type == 'enumerate' and level not in counters:
                counters[level] = 0
                
            # Skip this line - don't add to result
            i += 1
            continue
            
        # Check for end enumerate or itemize
        elif re.match(r'\\end\s?\{(enumerate|itemize)\}', line):
            # Reset counter for this level if it was enumerate
            if list_stack and list_stack[-1] == 'enumerate':
                counters[level] = 0
                
            level -= 1
            if list_stack:
                list_stack.pop()
                
            # Skip this line - don't add to result
            i += 1
            continue
            
        # Check for item
        elif re.match(r'\\item', line):
            # Determine current list type
            current_list_type = list_stack[-1] if list_stack else 'enumerate'
            
            # Extract the content after \item
            item_content = line[5:].strip()
            
            # Preserve leading whitespace from the original line
            leading_space = re.match(r'^(\s*)', original_line).group(1)
            
            # Add appropriate indentation based on nesting level
            indent = "    " * (level - 1)
            
            # Check if there are more lines to this item
            j = i + 1
            additional_content = []
            
            while j < len(lines) and not (re.match(r'\s*\\item|\s*\\begin|\s*\\end', lines[j])):
                additional_content.append(lines[j])
                j += 1
            
            # Format based on list type
            if current_list_type == 'enumerate':
                # Increment counter for this level
                counters[level] += 1
                current_count = counters[level]
                result.append(f"{indent}{current_count}. {item_content}")
            else:  # itemize
                # Use bullet points for itemize
                bullet = f"- {level}"
                result.append(f"{indent}{bullet} {item_content}")
            
            # Add any additional content lines with proper indentation
            for content_line in additional_content:
                if content_line.strip():  # If line has content
                    result.append(f"{indent}   {content_line.strip()}")
                else:  # Empty line
                    result.append(content_line)
            
            i = j
            continue
            
        # For empty or other lines, keep them as is
        else:
            result.append(original_line)
            i += 1
    
    return "\n".join(result)

def clean_text(text: str, category: str) -> str:
    # Turns inline and block math into katex-compatible
    text = text.encode("utf-8").decode("unicode_escape")
    
    text = text.replace("\\\\(", "$")
    text = text.replace("\\\\)", "$")
    text = text.replace("\\(", "$")
    text = text.replace("\\)", "$")
    text = text.replace("\\\\[", "$")
    text = text.replace("\\\\]", "$")

    # Fixes some weird custom expressions
    text = text.replace("\\InputFile", "")
    text = text.replace("\\OutputFile", "")
    text = text.replace("\\Note", "")

    text = re.sub(r"(?!`)``cpp", "```cpp", text) # Fixes batch 4, 59955

    text = re.sub(r"\\epigraph\{(.*?)\}\{(.*?)\}", lambda match: f"*(The original problem included an epigraph, that said '{match.group(1)} {match.group(2)}')*", text)
    text = re.sub(r"``(.*?)''", r"`\1`", text)
    
    # Find all examples and display them as tables
    text = format_examples(text, add_flag=category != "response")
    
    # Fixes some custom tags
    text = re.sub(r"\\exmp\{(.*?)\}\{(.*?)\}%", "", text)
    text = re.sub(r"\\begin\{problem\}.*?megabytes\}", "", text)
    text = re.sub(r"\\begin\{center\}.*\\includegraphics.*?\\end\{center\}", "*(A graphic is shown here in the original problem.)*", text)
    text = re.sub(r"\\end\{problem\}", "", text)
    
    # Fixes some leftover styling tags
    text = re.sub(r"\\textit\{(.*?)\}", r"*\1*", text)
    text = re.sub(r"\\textbf\{(.*?)\}", r"**\1**", text)
    text = re.sub(r"\\emph\{(.*?)\}", r"*\1*", text)
    text = re.sub(r"\\it\{(.*?)\}", r"*\1*", text)

    # Fixes href tags
    text = re.sub(r"\\href\{(.*?)\}\{(.*?)\}", r"[\2](\1)", text)
    
    # Fixes \texttt
    text = re.sub(r"[`']*\\t(exttt)?\{(.*?)\}[`']*", r"`\2`", text)

    if category != "response":
        text = re.sub(r"\\n(?!e )(?!eq )", "\n", text)
    else:
        text = re.sub(r"\\n\\n", "\n", text)
        text = re.sub(r"\\n(?!e )(?!eq )(?!\\n)(?!ot )", "  \n", text)
    
    text = re.sub(r"\\t(?!imes)(?!ext)(?!o)(?!au)(?!heta)", r"\t", text)
    text = text.replace("\\begin{example}", "")
    text = text.replace("\\end{example}", "")
    text = convert_latex_to_lists(text)
    return text