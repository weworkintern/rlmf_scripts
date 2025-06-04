DATA_VALS = {
    "user prompt": "User Prompt",
    "response": "Response",
    "system prompt": "System Prompt",
    "initial_response": "Initial Response",
    "intervene_system_prompt": "Intervene System Prompt",
    "intervene prompt": "Intervene User Prompt",
    "final_answer": "Final Answer",
    "ground_truth_answer": "Ground Truth Answer",
}

DATA_INFO = [
    "task id",
    "question_id",
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

FILTER_OPTIONS = [
    "None",
    "Abandoned",
    "Has interventions",
    "Not abandoned",
    "No interventions",
    "Has ground truth solutions"
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