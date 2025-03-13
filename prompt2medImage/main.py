from flask import Flask, request, jsonify
import torch
from diffusers import StableDiffusionPipeline
import io
import os
from datetime import datetime
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image

app = Flask(__name__)

# Initialize the model
model_id = "/Users/sparshjain/Prompt2MedImage"
device = "mps"

# Load model only once at startup
print("Loading model...")
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16, local_files_only=True)
pipe = pipe.to(device)
print("Model loaded successfully!")

# Configure Cloudinary
cloudinary.config(
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key = os.environ.get('CLOUDINARY_API_KEY'),
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
)

@app.route('/generate', methods=['POST'])
def generate_image():
    # Get the prompt from the request
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({"error": "No prompt provided"}), 400
    
    prompt = data['prompt']
    
    try:
        # Generate the image using the model
        image = pipe(prompt).images[0]
        
        # Save image to a buffer
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
        
        # Return the Cloudinary image URL and other details
        return jsonify({
            "success": True,
            "image_url": upload_result['secure_url'],
            "public_id": upload_result['public_id'],
            "created_at": upload_result['created_at']
        })
    
    except Exception as e:
        print(f"Error generating or uploading image: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the server
    app.run(host='0.0.0.0', port=5001, debug=False)