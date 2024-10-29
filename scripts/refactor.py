import os
from pathlib import Path
import re
from datasets import Dataset
import pandas as pd

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def create_conversation_from_text(text, source_file):
    content = clean_text(text)
    
    if not content:
        return None
        
    conversation = {
        'conversations': [
            {
                'role': 'system',
                'content': 'You are a helpful AI assistant that provides accurate and informative responses.'
            },
            {
                'role': 'user',
                'content': f'What can you tell me about the following content: {content[:100]}...'
            },
            {
                'role': 'assistant',
                'content': content
            }
        ],
        'source': source_file,
        'score': 1.0,
        'text': f"system\n\n"
                f"Cutting Knowledge Date: December 2023\nToday Date: 26 July 2024\n\n"
                f"system\n\n"
                f"{content}\n"
                f"assistant\n\n"
                f"{content}"
    }
    
    return conversation

def create_dataset():
    data_dir = Path('data/scraped_data')
    conversations_data = []
    
    for file_path in data_dir.glob('*.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            conversation = create_conversation_from_text(content, file_path.stem)
            if conversation:
                conversations_data.append(conversation)
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Convert to pandas DataFrame first
    df = pd.DataFrame(conversations_data)
    
    # Convert to HuggingFace Dataset
    dataset = Dataset.from_pandas(df)
    
    # Save the dataset
    dataset.save_to_disk('data/processed_dataset')
    
    print(f"Dataset created with {len(dataset)} entries")
    return dataset

if __name__ == "__main__":
    dataset = create_dataset()