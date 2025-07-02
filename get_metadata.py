import json
import os
import glob
from dotenv import load_dotenv
import pandas as pd

COLUMN_MAPPING = {
    'task id': 'task_id',
    'trainer id': 'trainer_id',
    'model name': 'model_name',
    'question_id': 'question_id',
    # 'system prompt': 'system_prompt',
    # 'user prompt': 'user_prompt',
    'level': 'level',
    'ACC': 'acc',
    # 'intervene_system_prompt': 'intervene_system_prompt',
    # 'intervene prompt': 'intervene_prompt',
    # 'ground_truth_answer': 'ground_truth_answer',
    'temperature': 'temperature',
    'total_tokens': 'total_tokens',
    'total_latency (ms)': 'total_latency_ms',
    # 'initial_reasoning': 'initial_reasoning',
    # 'response': 'response',
    # 'initial_response': 'initial_response',
    # 'final_answer': 'final_answer',
    'abandon_prompt': 'abandon_prompt',
    'abandon_prompt_reason': 'abandon_prompt_reason',
    'intervention rounds': 'intervention_rounds',
    'CoT quality': 'cot_quality',
    'remarks': 'remarks',
    'Model performance classification': 'model_performance_classification',
    'codeforces_submission_id':'codeforces_submission_id',
    'programming_language': 'programming_language',
}

def process_json_files(data_dir):
    all_processed_items = []
    all_column_names = set(COLUMN_MAPPING.values()) # Start with mapped names

    # Recursively find all .json and .jsonl files
    json_files = glob.glob(os.path.join(data_dir, '**', '*.json'), recursive=True)
    jsonl_files = glob.glob(os.path.join(data_dir, '**', '*.jsonl'), recursive=True)
    all_input_files = json_files + jsonl_files

    for file_path in all_input_files:
        print(f"Processing file: {file_path}")
        # Extract batch_id from filename
        basename = os.path.basename(file_path)
        batch_id = os.path.splitext(basename)[0]
        
        items = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    for line in f:
                        try:
                            items.append(json.loads(line))
                        except json.JSONDecodeError as e_line:
                            print(f"Skipping line in {file_path} due to JSON decode error: {e_line}")
                elif file_path.endswith('.json'):
                    try:
                        content = json.load(f)
                        if isinstance(content, list):
                            items = content
                        elif isinstance(content, dict): # Handle case where a .json file might contain a single object
                            items = [content]
                        else:
                            print(f"Skipping file {file_path}: content is not a list or dict of JSON objects.")
                    except json.JSONDecodeError as e_file:
                        print(f"Skipping file {file_path} due to JSON decode error: {e_file}")
                        # As a fallback for .json, try to read as JSONL if initial parse fails
                        # This might happen if a .json file is actually in JSONL format
                        f.seek(0) # Reset file pointer to the beginning
                        try:
                            print(f"Attempting to read {file_path} as JSONL...")
                            current_items = []
                            for line in f:
                                try:
                                    current_items.append(json.loads(line))
                                except json.JSONDecodeError as e_line_fallback:
                                    print(f"Skipping line in {file_path} (fallback JSONL) due to JSON decode error: {e_line_fallback}")
                            items = current_items
                        except Exception as e_fallback:
                            print(f"Failed to read {file_path} as JSONL fallback: {e_fallback}")

        except Exception as e:
            print(f"Could not read or process file {file_path}: {e}")
            continue

        for item in items:
            if not isinstance(item, dict):
                print(f"Skipping non-dictionary item in {file_path}: {item}")
                continue
            
            processed_item = {}
            # Apply column mapping and collect all original column names
            for original_key, value in item.items():
                if original_key in COLUMN_MAPPING:
                    new_key = COLUMN_MAPPING.get(original_key, original_key) # Use original key if not in mapping
                    if 'id' in new_key:  # Convert any form of ID to string
                        value = str(value)
                    processed_item[new_key] = value
                    all_column_names.add(new_key) # Add the key used (either mapped or original)
            
            # Add batch_id
            processed_item['batch_id'] = batch_id
            all_column_names.add('batch_id')
            
            all_processed_items.append(processed_item)

    # No filter
    filtered_items = all_processed_items

    # Ensure all filtered items have all collected columns
    final_output_items = []
    for item in filtered_items:
        standardized_item = {}
        for col_name in all_column_names:
            standardized_item[col_name] = item.get(col_name) # Defaults to None if key is missing
        final_output_items.append(standardized_item)
        
    return final_output_items


def main():
    load_dotenv(override=True)
    DATA_DIR = os.getenv('DATA_DIR', './data')

    # Ensure the DATA_DIR exists
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Error: Data directory '{DATA_DIR}' not found.")
    else:
        SUB_DIR = input("Please enter the sub-directory for the delivery JSON files (e.g., ALL): ")
        FILE_DIR = DATA_DIR + "/" + SUB_DIR
        output_data = process_json_files(FILE_DIR)

    if output_data:
        print(f"\nFound {len(output_data)} items.")
        print("Details of the first item (if any):")
        print(json.dumps(output_data[0], indent=4))

        # Convert output_data to DataFrame
        df = pd.DataFrame(output_data)
        

        # Reorder the DataFrame columns
        final_ordered_columns = list(COLUMN_MAPPING.values()) + ['batch_id']
        df = df[final_ordered_columns]

        # Save the output_data to 'metadata.csv'
        output_file_path = os.path.join(DATA_DIR, 'metadata.csv')
        try:
            df.to_csv(output_file_path, index=False, encoding='utf-8')
            print(f"\nOutput successfully written to {output_file_path}")
        except IOError as e:
            print(f"\nError writing output to {output_file_path}: {e}")
    else:
        print("No items found.")

if __name__ == '__main__':
    main()
