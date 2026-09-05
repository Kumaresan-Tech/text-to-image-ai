import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Ensure console supports UTF-8 on Windows without crashing on emojis
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load environment variables
load_dotenv()

# API Keys
gemini_key = os.getenv("GEMINI_API_KEY")
hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")

if not hf_token:
    print("❌ Hugging Face token missing. Please set HF_TOKEN in .env")
    sys.exit(1)

# Hugging Face client
from huggingface_hub import InferenceClient
hf_client = InferenceClient(api_key=hf_token)

# Gemini client (optional enhancement)
gemini_client = None
if gemini_key:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"⚠️ Gemini client initialization note: {e}")

# Get user prompt
print("\n" + "=" * 50)
print("  🎨 AI Text-to-Image Generator (FLUX.1 Schnell)")
print("=" * 50)

user_prompt = input("\n📝 Enter your image prompt: ").strip()

if not user_prompt:
    print("❌ Prompt cannot be empty. Please enter a valid prompt.")
    sys.exit(1)

enhanced_prompt = user_prompt

# Gemini prompt enhancement
if gemini_client:
    print("\n🧠 Gemini is enhancing your prompt...")
    instruction = f"""
You are an expert AI image prompt engineer.

Convert the user's simple request into a detailed,
high-quality prompt for an AI image generator.

Include:
- subject details
- environment
- lighting
- composition
- camera perspective
- artistic style
- colors
- visual details

Return ONLY the final image generation prompt without preamble or quotes.

User request:
{user_prompt}
"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=instruction
        )
        if response and response.text:
            enhanced_prompt = response.text.strip()
            print("\n✨ Enhanced Prompt:")
            print(enhanced_prompt)
        else:
            print("⚠️ Enhancement returned empty, using original prompt.")
    except Exception as e:
        print(f"⚠️ Gemini enhancement failed ({e}). Using original prompt.")
else:
    print("\nℹ️ Gemini API key not set; proceeding with raw prompt.")

# Generate image with Hugging Face FLUX.1 Schnell
print("\n🎨 Generating image with FLUX.1 Schnell...")
print("⏳ Please wait (~5-15 seconds)...")

try:
    image = hf_client.text_to_image(
        prompt=enhanced_prompt,
        model="black-forest-labs/FLUX.1-schnell"
    )
except Exception as e:
    print(f"\n❌ Image generation failed: {e}")
    sys.exit(1)

# Create output folder
os.makedirs("outputs", exist_ok=True)

# Save both latest and timestamped image
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
timestamped_path = f"outputs/generated_{timestamp}.png"
latest_path = "outputs/generated_image.png"

image.save(timestamped_path)
image.save(latest_path)

print("\n" + "=" * 50)
print("🎉 IMAGE GENERATED SUCCESSFULLY!")
print("=" * 50)
print(f"🖼️ Latest Image: {latest_path}")
print(f"📁 Archived At: {timestamped_path}")