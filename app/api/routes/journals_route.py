from fastapi import HTTPException, Depends, status, APIRouter
from sqlalchemy.orm import Session
from app.models.auth import UserPublic
from app.services.db import get_session
from app.dependencies.helpers import get_current_userId
from app.schemas import journals_schema, affirmations_schema
from app.models.journals import JournalBase, JournalReponse
from transformers import pipeline
from app.core.config import GEMINI_API_KEY
from datetime import datetime
import warnings
import google.generativeai as genai
import json
import re
from functools import lru_cache

warnings.filterwarnings("ignore", message="Some weights of the model checkpoint")

# Configure Gemini client
client = genai.configure(api_key=GEMINI_API_KEY)
genai_model = genai.GenerativeModel("gemini-2.0-flash")

# Define FastAPI router
router = APIRouter()

# # Lazy-load sentiment pipeline
# @lru_cache(maxsize=1)
# def get_sentiment_pipeline():
#     return pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")



@router.post("/add_journal", response_model=JournalReponse)
def add_journal(
    journal_input: JournalBase,
    db: Session = Depends(get_session),
    user: UserPublic = Depends(get_current_userId),
):
    journal_title = journal_input.title
    journal_content = journal_input.content

    user_id = user.id
    created_at = datetime.now()

    # Use the pipeline for sentiment analysis
    # sentiment = get_sentiment_pipeline()(journal_content)[0]
    prompt_to_analyze_journal_sentiment=f"""You are a compassionate and emotionally intelligent sentiment analyst. Your role is to read a person's short journal entry or reflection and determine the underlying emotional tone. Your analysis should reflect nuance and empathy, capturing the complexity of human emotions.

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
            "{journal_content}"

            Respond only in the following JSON format:

            {{
            "label": "positive/negative/neutral",
            "probability": XX.XX
            }}"""
    
    response_sentiment = genai_model.generate_content(contents=prompt_to_analyze_journal_sentiment)
    raw_sentiment_text = re.sub(r"```json|```", "", response_sentiment.text).strip()

    try:
        sentiment_json = json.loads(raw_sentiment_text)
        label = sentiment_json["label"]
        probability = float(sentiment_json["probability"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid sentiment analysis format from Gemini."
        )

    new_journal = journals_schema.Journal(
        title=journal_title,
        content=journal_content,
        user_id=user_id,
        sentiment_label=label,
        sentiment_score=round(probability, 2),
        created_at=created_at,
    )
    
    

    try:
        db.add(new_journal)
        db.commit()
        db.refresh(new_journal)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error in writing data to db",
        )

    prompt = f"""You are a compassionate and emotionally intelligent affirmation coach. Your job is to read a person's short input text, extract their emotional and situational context, and then generate 5 personalized, uplifting affirmations that directly support their mental and emotional well-being.

        Your affirmations should:
        - Acknowledge and validate the person’s feelings (e.g., stress, sadness, exhaustion, relief).
        - Focus on resilience, self-worth, and encouragement based on the scenario.
        - Be supportive, empowering, and gently optimistic.
        - Avoid toxic positivity; reflect a realistic but hopeful tone.
        - Be concise (1–2 sentences per affirmation), direct, and emotionally attuned.

        Only return the 5 affirmations in a numbered list, without repeating the input text or adding extra explanations.

        Example Input:
        "I had a rough day at university today. The lectures were really difficult to understand and we were given a lot of assignments. I am really depressed and overwhelmed. However, hanging out with my friends made me happy."

        Example Output:
        1. It's okay to feel overwhelmed—I'm doing my best, and that's enough right now.  
        2. Even tough days pass, and I have the strength to keep moving forward.  
        3. I am not alone—connection with friends brings me comfort and light.  
        4. I learn and grow, even when things feel confusing or hard.  
        5. I give myself permission to rest and recharge without guilt.

        Now, generate 5 affirmations based on this input:
        "{journal_content}"
        
        Respond ONLY in the following JSON format without explanations:

        ```json
        {{
            "input_summary": "User is feeling overwhelmed and sad due to difficult university lectures and heavy assignments but finds relief in spending time with friends.",
            "affirmations": [
                "It's okay to feel overwhelmed—I'm doing my best, and that's enough right now.",
                "Even tough days pass, and I have the strength to keep moving forward.",
                "I am not alone—connection with friends brings me comfort and light.",
                "I learn and grow, even when things feel confusing or hard.",
                "I give myself permission to rest and recharge without guilt."
            ]
        }}"""

    json_response = None

    if label.lower() == "negative":
        response = genai_model.generate_content(contents=prompt)

        raw_text = response.text
        cleaned_text = re.sub(r"```json|```", "", raw_text).strip()
        try:
            json_response = json.loads(cleaned_text)
            affirmations_json = json.dumps(json_response["affirmations"], indent=2)
            input_summary = json_response["input_summary"]
            try:
                add_affirmation = affirmations_schema.Affirmation(
                    input_summary=input_summary,
                    affirmations=affirmations_json,
                    journal_id=new_journal.id,
                )
                db.add(add_affirmation)
                db.commit()
                db.refresh(add_affirmation)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error in writing data to db",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The response from the external service was not in a valid format. Please try again later.",
            )

    return JournalReponse(
        title=journal_title,
        content=journal_content,
        sentiment_label=label,
        sentiment_probability=round(probability, 2),
        output=json_response,  # May be None if not negative
    )
