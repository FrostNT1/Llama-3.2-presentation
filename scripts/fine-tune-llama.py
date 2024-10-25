from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import Dataset
import os
import torch
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.expanduser('~/.env'))
hf_token = os.getenv('HF_TOKEN')

# Load the LLaMA 3.2 model and tokenizer
model_name = "meta-llama/Llama-3.2-3B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=hf_token)

# Prepare the text dataset for training
def load_scraped_data():
    texts = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'scraped_data')
    for file_name in tqdm(os.listdir(data_dir), desc="Loading data"):
        with open(os.path.join(data_dir, file_name), "r", encoding='utf-8') as file:
            texts.append(file.read())
    return texts

print("Loading scraped data...")
scraped_texts = load_scraped_data()

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=512)

print("Tokenizing dataset...")
dataset = Dataset.from_dict({"text": scraped_texts})
tokenized_dataset = dataset.map(tokenize_function, batched=True, desc="Tokenizing")

# Define the training arguments
training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    num_train_epochs=3,
    weight_decay=0.01,
    save_steps=1000,
    fp16=True,
    gradient_accumulation_steps=4,
    logging_dir='./logs',
    logging_steps=100,
)

# Custom callback to display progress
class ProgressCallback(Trainer.Callback):
    def __init__(self):
        self.start_time = time.time()

    def on_train_begin(self, args, state, control, **kwargs):
        print("Training started...")

    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step % 100 == 0:
            elapsed_time = time.time() - self.start_time
            progress = state.global_step / state.max_steps
            estimated_total_time = elapsed_time / progress if progress > 0 else 0
            remaining_time = estimated_total_time - elapsed_time

            print(f"Progress: {progress:.2%} | "
                  f"Step: {state.global_step}/{state.max_steps} | "
                  f"Elapsed: {elapsed_time/60:.2f}m | "
                  f"Remaining: {remaining_time/60:.2f}m")

    def on_train_end(self, args, state, control, **kwargs):
        print("Training completed!")

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=lambda data: {'input_ids': torch.stack([f['input_ids'] for f in data]),
                                'attention_mask': torch.stack([f['attention_mask'] for f in data]),
                                'labels': torch.stack([f['input_ids'] for f in data])},
    callbacks=[ProgressCallback()]
)

# Start fine-tuning
print("Starting fine-tuning...")
trainer.train()

# Save the fine-tuned model
print("Saving fine-tuned model...")
save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'fine_tuned_llama3.2')
model.save_pretrained(save_dir)
tokenizer.save_pretrained(save_dir)

print("Fine-tuning process completed!")
