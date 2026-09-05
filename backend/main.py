import os
import replicate
from dotenv import load_dotenv

load_dotenv()

prompt = "A futuristic AI laboratory, cinematic lighting, ultra detailed"

print("🎨 Generating image...")

output = replicate.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": prompt
    }
)

print("✅ Image generated!")
print(output)