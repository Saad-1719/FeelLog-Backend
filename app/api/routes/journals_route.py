from fastapi import HTTPException, Depends, status, APIRouter, Request
from sqlalchemy.orm import Session, joinedload
from app.services.db import get_session
from app.dependencies.auth import get_current_userId
from app.schemas import journals_schema, affirmations_schema
from app.models.journals import (
    JournalBase,
    JournalReponse,
    AllJournalsAndAffirmations,
    JournalDeleteRequest,
    JournalUpdateRequest,
    SentimentDataResponse,
    SentimentDataRequest,
)
from typing import List
from app.models.auth import UserId
from datetime import datetime
from sqlalchemy import desc
import json
from app.utils.affirmations_utils import analyze_sentiments, generate_affirmations
from app.utils.encryption_utils import encrypt_data, decrypt_data
from slowapi import Limiter
from slowapi.util import get_remote_address


def custom_key_func(request: Request):
    # Skip rate limiting for OPTIONS requests
    if request.method == "OPTIONS":
        return None
    # Regular rate limiting for all other methods
    return get_remote_address(request)


limiter = Limiter(key_func=custom_key_func)

# Define FastAPI router
router = APIRouter()


@router.post("/add_journal", response_model=JournalReponse)
@limiter.limit("8/minute")
def add_journal(
    journal_input: JournalBase,
    db: Session = Depends(get_session),
    user: UserId = Depends(get_current_userId),
    request: Request = None,
):
    journal_title = journal_input.title
    journal_content = journal_input.content
    affirmations_json = None

    if not journal_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Journal content cannot be empty",
        )

    try:
        sentiment_json = analyze_sentiments(journal_content)
        if (
            not isinstance(sentiment_json, dict)
            or "label" not in sentiment_json
            or "probability" not in sentiment_json
        ):
            raise ValueError("Invalid sentiment analysis response")
        label = sentiment_json["label"]
        probability = float(sentiment_json["probability"])
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid sentiment analysis format from Gemini.",
        )
    encrypted_title = encrypt_data(journal_title)
    encrypted_content = encrypt_data(journal_content)
    new_journal = journals_schema.Journal(
        title=encrypted_title,
        content=encrypted_content,
        user_id=user.id,
        sentiment_label=label,
        sentiment_score=round(probability, 2),
        created_at=datetime.now(),
    )

    try:
        db.add(new_journal)
        db.commit()
        db.refresh(new_journal)
        if label.lower() in ["negative", "neg"]:
            affirmations = generate_affirmations(journal_content)
            try:
                affirmations_json = json.dumps(affirmations["affirmations"], indent=2)
                input_summary = affirmations["input_summary"]
                encrypted_input_summary = encrypt_data(input_summary)
                encrypted_affirmations = encrypt_data(affirmations_json)
                add_affirmation = affirmations_schema.Affirmation(
                    input_summary=encrypted_input_summary,
                    affirmations=encrypted_affirmations,
                    journal_id=new_journal.id,
                )
                db.add(add_affirmation)
                db.commit()
                db.refresh(add_affirmation)
            except (json.JSONDecodeError, KeyError):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid affirmation response format from Gemini.",
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error in writing data to db: {str(e)}",
        )

    return JournalReponse(
        title=journal_title,
        content=journal_content,
        affirmations=json.loads(affirmations_json) if affirmations_json else [],
    )


@router.get("/get_all_journals", response_model=List[AllJournalsAndAffirmations])
@limiter.limit("20/minute")
def fetch_all_journals(
    currentUser: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session),
    request: Request = None,
):
    try:
        all_journals = (
            db.query(journals_schema.Journal)
            .filter(currentUser.id == journals_schema.Journal.user_id)
            .options(joinedload(journals_schema.Journal.affirmations))
            .order_by(desc(journals_schema.Journal.created_at))
            .all()
        )

        decrypted_journals = []

        for journal in all_journals:

            journal.title = decrypt_data(journal.title)
            journal.content = decrypt_data(journal.content)

            for affirmation in journal.affirmations:

                if affirmation.input_summary:
                    affirmation.input_summary = decrypt_data(affirmation.input_summary)

                if affirmation.affirmations:
                    decrypted_affirmations = decrypt_data(affirmation.affirmations)
                    try:
                        affirmation.affirmations = json.loads(decrypted_affirmations)
                    except json.JSONDecodeError:
                        affirmation.affirmations = []

            decrypted_journals.append(journal)

        return decrypted_journals
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/delete_journal")
def delete_journal(
    request: JournalDeleteRequest,
    currentUser: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session),
):
    try:
        result = (
            db.query(journals_schema.Journal)
            .filter(
                journals_schema.Journal.id == request.journal_id,
                journals_schema.Journal.user_id == currentUser.id,
            )
            .delete()
        )
        db.commit()
        return {"message": "Journal deleted successfully", "deleted": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/update_journal", response_model=JournalReponse)
def update_journal(
    request: JournalUpdateRequest,
    currentUser: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session),
):
    try:
        journal_title = request.title
        journal_content = request.content

        if not journal_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Journal content cannot be empty",
            )

        sentiment = analyze_sentiments(journal_content)
        try:
            if (
                not isinstance(sentiment, dict)
                or "label" not in sentiment
                or "probability" not in sentiment
            ):
                raise ValueError("Invalid sentiment analysis response")
            label = sentiment["label"]
            probability = float(sentiment["probability"])
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid sentiment analysis format from Gemini.",
            )

        affirmations_json = None

        journal = (
            db.query(journals_schema.Journal)
            .filter(
                journals_schema.Journal.id == request.journal_id,
                journals_schema.Journal.user_id == currentUser.id,
            )
            .first()
        )
        if not journal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal not found or not owned by user",
            )

        # Encrypt updated data
        journal.title = encrypt_data(journal_title)
        journal.content = encrypt_data(journal_content)
        journal.sentiment_label = label
        journal.sentiment_score = round(probability, 2)

        if label.lower() in ["negative", "neg"]:
            affirmations = generate_affirmations(journal_content)
            try:
                affirmations_json = json.dumps(affirmations["affirmations"], indent=2)
                input_summary = affirmations["input_summary"]

                # Encrypt affirmation data
                encrypted_input_summary = encrypt_data(input_summary)
                encrypted_affirmations = encrypt_data(affirmations_json)

                affirmation_entry = (
                    db.query(affirmations_schema.Affirmation)
                    .filter(
                        affirmations_schema.Affirmation.journal_id == request.journal_id
                    )
                    .first()
                )
                if affirmation_entry:
                    affirmation_entry.input_summary = encrypted_input_summary
                    affirmation_entry.affirmations = encrypted_affirmations
                else:
                    new_affirmation = affirmations_schema.Affirmation(
                        input_summary=encrypted_input_summary,
                        affirmations=encrypted_affirmations,
                        journal_id=request.journal_id,
                    )
                    db.add(new_affirmation)
                db.commit()
            except (json.JSONDecodeError, KeyError):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid affirmation response format from Gemini.",
                )
        else:
            # Delete affirmations if sentiment is not negative
            db.query(affirmations_schema.Affirmation).filter(
                affirmations_schema.Affirmation.journal_id == request.journal_id
            ).delete()
            db.commit()

        return JournalReponse(
            title=journal_title,
            content=journal_content,
            affirmations=json.loads(affirmations_json) if affirmations_json else [],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/get_sentiment_overview", response_model=SentimentDataResponse)
@limiter.limit("8/minute")
def get_sentiment_overview(
    currentUser: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session),
    request: Request = None,
):
    try:

        if not currentUser:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        journal_entries = (
            db.query(journals_schema.Journal)
            .filter(journals_schema.Journal.user_id == currentUser.id)
            .order_by(journals_schema.Journal.created_at.asc())
            .all()
        )

        if not journal_entries:
            return SentimentDataResponse(data=[])

        response_data = [
            SentimentDataRequest(
                entry_id=entry.id,
                title=decrypt_data(entry.title),  # Decrypt title
                timestamp=entry.created_at,
                sentiment_label=entry.sentiment_label,
                sentiment_score=entry.sentiment_score,
            )
            for entry in journal_entries
        ]

        return SentimentDataResponse(data=response_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error in processing request",
        )
