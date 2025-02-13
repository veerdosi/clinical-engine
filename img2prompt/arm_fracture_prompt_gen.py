import os
import base64
from openai import OpenAI
from pathlib import Path
import time
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xray_processing.log'),
        logging.StreamHandler()
    ]
)

class XrayPromptGenerator:
    def __init__(self, api_key: str, input_dir: str, output_dir: str, batch_size: int = 10, start_batch: int = 0):
        self.client = OpenAI(api_key=api_key)
        
        # Convert to absolute paths using current working directory
        current_dir = Path.cwd()
        self.input_dir = current_dir / input_dir
        self.output_dir = current_dir / output_dir
        
        self.batch_size = batch_size
        self.start_batch = start_batch
        self.system_prompt = """You are a physician and orthopaedic doctor who is an expert in analysing x-ray images of human bones. The output you provide will be detailed and medically accurate."""
        self.user_prompt = """Generate an actual, medically accurate description of the image. Three sentences each using medical terminologies. Highlight any disease, deformity, illness or problem relevant to the image provided. Do not draw any conclusion regarding why and how the particular disease, deformity, illness or problem might have occurred. Just describe the image."""
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate input directory exists
        if not self.input_dir.exists():
            raise ValueError(f"Input directory does not exist: {self.input_dir}")

    def get_processed_files(self) -> set:
        """Get list of already processed files."""
        return {Path(f.stem) for f in self.output_dir.glob('*.txt')}

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_image_files(self) -> List[Path]:
        """Get all image files from input directory."""
        valid_extensions = {'.jpg', '.jpeg', '.png'}
        return [f for f in self.input_dir.iterdir() 
                if f.is_file() and f.suffix.lower() in valid_extensions]

    def process_single_image(self, image_path: Path) -> Dict:
        """Process a single image and return the generated description."""
        try:
            base64_image = self.encode_image(str(image_path))
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            return {
                'success': True,
                'image_name': image_path.stem,
                'description': response.choices[0].message.content
            }
        except Exception as e:
            logging.error(f"Error processing {image_path.name}: {str(e)}")
            return {
                'success': False,
                'image_name': image_path.stem,
                'error': str(e)
            }

    def save_description(self, image_name: str, description: str):
        """Save the generated description to a text file."""
        output_path = self.output_dir / f"{image_name}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(description)

    def process_batch(self, image_files: List[Path]):
        """Process a batch of images."""
        processed_files = self.get_processed_files()
        
        for image_path in image_files:
            # Skip if already processed
            if Path(image_path.stem) in processed_files:
                logging.info(f"Skipping already processed file: {image_path.name}")
                continue
                
            result = self.process_single_image(image_path)
            
            if result['success']:
                self.save_description(result['image_name'], result['description'])
                logging.info(f"Successfully processed: {image_path.name}")
            else:
                logging.error(f"Failed to process: {image_path.name}")
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)

    def run(self):
        """Main function to run the prompt generator."""
        image_files = self.get_image_files()
        total_images = len(image_files)
        
        logging.info(f"Found {total_images} images to process")
        
        # Calculate starting index based on start_batch
        start_index = self.start_batch * self.batch_size
        
        # Process images in batches starting from the specified batch
        for i in range(start_index, total_images, self.batch_size):
            current_batch = (i // self.batch_size) + 1
            batch = image_files[i:i + self.batch_size]
            logging.info(f"Processing batch {current_batch}")
            self.process_batch(batch)
            
            # Add delay between batches
            if i + self.batch_size < total_images:
                time.sleep(2)

if __name__ == "__main__":
    # Configuration
    API_KEY = "API_KEY_HERE"
    INPUT_DIR = "images"
    OUTPUT_DIR = "output_prompts"
    BATCH_SIZE = 10

    # Initialize and run the generator
    generator = XrayPromptGenerator(
        api_key=API_KEY,
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
        batch_size=BATCH_SIZE,
        start_batch = 206
    )
    
    generator.run()