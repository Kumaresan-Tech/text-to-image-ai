import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

hf_token = os.getenv("HF_TOKEN")

if not hf_token:
    raise ValueError("❌ HF_TOKEN is missing from .env")

client = InferenceClient(
    api_key=hf_token
)

prompt = """
A futuristic AI robot standing in a cyberpunk city,
neon lights, cinematic lighting, highly detailed
"""

print("🎨 Generating image...")

image = client.text_to_image(
    prompt=prompt,
    model="black-forest-labs/FLUX.1-schnell"
)

image.save("test_image.png")

print("✅ Image generated!")
print("📁 test_image.png")