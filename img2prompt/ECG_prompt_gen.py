import pandas as pd
from openai import OpenAI
import time
from tqdm import tqdm
import json
import os

class ECGPromptGenerator:
    def __init__(self, api_key, model="gpt-4"):
        """Initialize the ECG Prompt Generator with OpenAI API key."""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # System and user prompt templates
        self.system_prompt = """You are a physician and a trained cardiologist who is an expert in analysing csv ECG data. 
        The output you provide will be detailed and medically accurate."""
        
        self.user_prompt_template = """Generate an actual, medically accurate description of the data. 
        Three sentences each using medical terminologies. Highlight any disease, illness or problem relevant to the data provided. 
        Do not draw any conclusion regarding why and how the particular disease, illness or problem might have occurred. 
        Just describe the data.

        ECG Data:
        {data}"""

    def create_data_string(self, row):
        """Convert row data to a formatted string using column indices."""
        return ", ".join([f"Column_{i}: {value}" for i, value in enumerate(row)])

    def generate_prompt(self, data_string):
        """Generate description using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self.user_prompt_template.format(data=data_string)}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating prompt: {str(e)}")
            return None

    def process_dataset(self, input_csv_path, output_csv_path, batch_size=50, start_index=None):
        """Process the entire dataset and save results."""
        # Read input CSV without headers
        df = pd.read_csv(input_csv_path, header=None)
        
        print(f"Starting from index: {start_index}")
        
        # Load existing output if it exists
        output_df = pd.DataFrame(columns=['original_index', 'generated_description'])
        if os.path.exists(output_csv_path):
            output_df = pd.read_csv(output_csv_path)
        
        # Process in batches
        total_batches = (len(df) - start_index) // batch_size + 1
        for i in tqdm(range(start_index, len(df), batch_size), total=total_batches):
            batch = df.iloc[i:i+batch_size]
            
            for idx, row in batch.iterrows():
                # Skip if already processed
                if idx in output_df['original_index'].values:
                    continue
                    
                data_string = self.create_data_string(row)
                description = self.generate_prompt(data_string)
                
                if description:
                    new_row = pd.DataFrame({
                        'original_index': [idx],
                        'generated_description': [description]
                    })
                    output_df = pd.concat([output_df, new_row], ignore_index=True)
                    
                    # Save after each successful generation
                    output_df.to_csv(output_csv_path, index=False)
            
            # Rate limiting - sleep for 1 second between batches
            time.sleep(1)
        
        return output_df
        

def main():
    # Configuration
    API_KEY = "API_KEY_HERE"
    INPUT_CSV_PATH = "ecg.csv"
    OUTPUT_CSV_PATH = "generated_descriptions.csv"
    
    # Initialize generator
    generator = ECGPromptGenerator(API_KEY, model="gpt-4o-mini")
    
    # Process dataset
    print("Starting ECG data processing...")
    results = generator.process_dataset(INPUT_CSV_PATH, OUTPUT_CSV_PATH, start_index=1280)
    print(f"Processing complete. Generated {len(results)} descriptions.")
    print(f"Results saved to: {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()