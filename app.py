

from flask import Flask, request
from flask_cors import CORS
import requests
import base64
import io
from PIL import Image
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
from tempfile import NamedTemporaryFile

app = Flask(__name__)
CORS(app)

def merge_images(images):
    # Determine the total width and height of the merged image
    total_width = max(image.width for image in images)
    total_height = sum(image.height for image in images)

    # Create a new image with the total size
    merged_image = Image.new('RGB', (total_width, total_height))

    # Paste each image below the previous one
    y_offset = 0
    for image in images:
        merged_image.paste(image, (0, y_offset))
        y_offset += image.height

    return merged_image

def encode_image(image):
    # Convert image to RGB mode if not already
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def convert_pdf_to_base64(pdf_file_storage):
    # Convert all pages of the PDF to images and merge them
    with NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
        pdf_file_storage.save(temp_pdf)
        temp_pdf_path = temp_pdf.name

    pages = convert_from_path(temp_pdf_path)
    merged_image = merge_images(pages)
    return encode_image(merged_image)

@app.route("/process-file/", methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return {"error": "No file part"}
    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}

    file_extension = file.filename.split('.')[-1].lower()
    base64_image = ''
    if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
        base64_image = encode_image(Image.open(file))
    elif file_extension == 'pdf':
        try:
            base64_image = convert_pdf_to_base64(file)
        except Exception as e:
            return {"error": str(e)}
    else:
        return {"error": "Unsupported file format"}

    user_prompt = request.form.get('prompt')
    api_key = "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"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",

          "messages": [
             {
                 "role": "user",
                 "content": [
                     {
                         "type": "text",
                         "text": user_prompt
                     },
                     {
                         "type": "image_url",
                         "image_url": {
                             "url": f"data:image/jpeg;base64,{base64_image}"
                         }
                     }
                 ]
             }
         ],
         "max_tokens": 4000
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            return "No relevant data found in response."
    except requests.RequestException as e:
        return {"error": str(e)}

if __name__ == '__main__':
    app.run(debug=True)
