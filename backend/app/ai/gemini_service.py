import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

CATEGORIES = [
    "Food waste",
    "Agricultural waste",
    "Fruit and vegetable waste",
    "Coffee waste",
    "Maize/cereal waste",
    "Dairy waste",
    "Brewery waste",
    "Animal-related organic waste",
    "Other organic waste",
    "Unknown / requires review",
]

PROMPT = f"""
You are classifying a photo of organic waste for a B2B waste marketplace.

Choose exactly one category from this list: {", ".join(CATEGORIES)}

Respond ONLY with valid JSON, no extra text, in this exact format:
{{
  "waste_type": "<one category from the list>",
  "confidence": "<High, Medium, or Low - your own qualitative judgment, not a percentage>",
  "description": "<1-2 sentence description of what is visible>",
  "possible_uses": ["<use1>", "<use2>"]
}}

If the image is unclear or not organic waste, use "Unknown / requires review" as the waste_type,
set confidence to "Low", and explain why in the description.
"""


def classify_image(image_bytes: bytes, mime_type: str) -> dict:
    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(
        [
            {"mime_type": mime_type, "data": image_bytes},
            PROMPT,
        ]
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)