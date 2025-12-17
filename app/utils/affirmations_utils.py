import json
from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY
import re

client = genai.Client(api_key=GEMINI_API_KEY)
# genai_model = genai.GenerativeModel("gemini-2.0-flash")


def analyze_sentiments(content: str) -> dict:
    prompt_to_analyze_journal_sentiment = f"""You are a compassionate and emotionally intelligent sentiment analyst. Your role is to read a person's short journal entry or reflection and determine the underlying emotional tone. Your analysis should reflect nuance and empathy, capturing the complexity of human emotions.

                Your output should:
                - Identify whether the sentiment is positive, negative, or neutral.
                - Account for mixed emotions and determine the dominant sentiment.
                - Include a probability score (0.00–100.00) representing your confidence in the classification, based on the clarity and consistency of the sentiment.
                - Be returned in a valid JSON format only with no explanations or extra text.
                  Example Input:
                "I’m grateful for my family, but lately I’ve been feeling disconnected and tired all the time."

                Example Output:
                {{
                "label": "negative",
                "probability": 78.25
                }}

                Instructions:
                Now analyze the following input:
                "{content}"

                Respond only in the following JSON format:

                {{
                "label": "positive/negative/neutral",
                "probability": XX.XX
                }}"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_to_analyze_journal_sentiment,
        config=types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=10,
    ),
    )
    
    cleaned = re.sub(r"```json|```", "", response.text).strip()
    return json.loads(cleaned)


def generate_affirmations(content: str) -> dict:
    prompt = f"""You are a compassionate and emotionally intelligent affirmation coach. Your job is to read a person's short input text, extract their emotional and situational context, and then generate 5 personalized, uplifting affirmations that directly support their mental and emotional well-being.

           Your affirmations must:
            - Acknowledge and validate the person’s emotions (e.g., sadness, self-doubt, loneliness).
            - Be supportive, emotionally attuned, and empowering—**but not overly heavy or wordy**.
            - Be **short and digestible**: *no more than 10–13 words per affirmation*.
            - Avoid "toxic positivity"—stay grounded, warm, and realistic.
            - Use natural, affirming language someone could easily repeat anytime.


           Only return the 5 affirmations in a numbered list, without repeating the input text or adding extra explanations.

           Example Input:
           "I had a rough day at university today. The lectures were really difficult to understand and we were given a lot of assignments. I am really depressed and overwhelmed. However, hanging out with my friends made me happy."

           Example Output:
           1. It's okay to feel overwhelmed—I'm doing my best.  
           2. I have the strength to keep moving forward.  
           3. I am not alone—connection with friends brings me comfort and light.  
           4. I learn and grow, even when things feel confusing or hard.  
           5. I give myself permission to rest and recharge without guilt.

           Now, generate 5 affirmations based on this input:
           "{content}"

           Respond ONLY in the following JSON format without explanations:

           ```json
            {{
                "input_summary": "User is feeling overwhelmed and sad due to difficult university lectures and heavy assignments but finds relief in spending time with friends.",
                "affirmations": [
                    "It's okay to feel overwhelmed—I'm doing my best.",
                    "I have the strength to keep going.",
                    "Connection with friends brings me light and support.",
                    "I learn and grow, even when it's tough.",
                    "I deserve rest and kindness toward myself."
                ]
            }}
"""
    response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=10,
    ))
    cleaned = re.sub(r"```json|```", "", response.text).strip()
    return json.loads(cleaned)
