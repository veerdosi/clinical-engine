import torch
from diffusers import StableDiffusionPipeline
import io
import os
import argparse
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate medical images from text prompts")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt for image generation")
    parser.add_argument("--output", type=str, help="Local path to save the generated image")
    parser.add_argument("--upload", action="store_true", help="Upload the image to Cloudinary")
    args = parser.parse_args()

    # Initialize the model
    model_id = "/Users/sparshjain/Documents/GitHub/clinical-engine/Prompt2MedImage"
    device = "mps"

    # Load model
    print("Loading model...")
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16, local_files_only=True)
    pipe = pipe.to(device)
    print("Model loaded successfully!")

    try:
        # Generate the image using the model
        prompt = args.prompt
        print(f"Generating image for prompt: {prompt}")
        image = pipe(prompt).images[0]
        
        # Save image locally if output path is provided
        if args.output:
            os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
            image.save(args.output)
            print(f"Image saved to {args.output}")
        
        # Upload to Cloudinary if requested
        if args.upload:
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
                api_key=os.environ.get('CLOUDINARY_API_KEY'),
                api_secret=os.environ.get('CLOUDINARY_API_SECRET')
            )
            
            # Save image to a buffer for uploading
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                img_buffer,
                folder="stable-diffusion-images",
                public_id=filename,
                resource_type="image"
            )
            
            print(f"Image uploaded to Cloudinary: {upload_result['secure_url']}")
            
            # Return the URL as stdout for the calling script to capture
            print(f"CLOUDINARY_URL:{upload_result['secure_url']}")
        
        return 0  # Success
    
    except Exception as e:
        print(f"Error generating or uploading image: {str(e)}")
        return 1  # Error

if __name__ == '__main__':
    exit(main())