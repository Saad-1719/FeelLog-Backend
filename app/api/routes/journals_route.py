from fastapi import HTTPException, Depends, status, APIRouter
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
    SentimentDataResponse,SentimentDataRequest
)
from typing import List
from app.models.auth import UserId
from datetime import datetime
from sqlalchemy import desc
import json
from app.utils.utils import analyze_sentiments, generate_affirmations

# Define FastAPI router
router = APIRouter()


@router.post("/add_journal", response_model=JournalReponse)
def add_journal(
    journal_input: JournalBase,
    db: Session = Depends(get_session),
    user: UserId = Depends(get_current_userId),
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

    new_journal = journals_schema.Journal(
        title=journal_title,
        content=journal_content,
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
                add_affirmation = affirmations_schema.Affirmation(
                    input_summary=input_summary,
                    affirmations=affirmations_json,
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
def fetch_all_journals(
    currentUser: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session),
):
    try:
        all_journals = (
            db.query(journals_schema.Journal)
            .filter(currentUser.id == journals_schema.Journal.user_id)
            .options(joinedload(journals_schema.Journal.affirmations)).order_by(desc(journals_schema.Journal.created_at))
            .all()
        )

        for journal in all_journals:
            for affirmation in journal.affirmations:
                if isinstance(affirmation.affirmations, str):
                    try:
                        affirmation.affirmations = json.loads(affirmation.affirmations)
                    except json.JSONDecodeError:
                        affirmation.affirmations = []

        return all_journals
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
        journal.title = request.title
        journal.content = request.content
        journal.sentiment_label = label
        journal.sentiment_score = round(probability, 2)

        if label.lower() in ["negative", "neg"]:
            affirmations = generate_affirmations(journal_content)
            try:
                affirmations_json = json.dumps(affirmations["affirmations"], indent=2)
                input_summary = affirmations["input_summary"]
                affirmation_entry = (
                    db.query(affirmations_schema.Affirmation)
                    .filter(
                        affirmations_schema.Affirmation.journal_id == request.journal_id
                    )
                    .first()
                )
                if affirmation_entry:
                    affirmation_entry.input_summary = input_summary
                    affirmation_entry.affirmations = affirmations_json
                else:
                    new_affirmation = affirmations_schema.Affirmation(
                        input_summary=input_summary,
                        affirmations=affirmations_json,
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
            db.query(affirmations_schema.Affirmation).filter(
                affirmations_schema.Affirmation.journal_id == request.journal_id
            ).delete()
            db.commit()

        return JournalReponse(
            title=request.title,
            content=journal_content,
            affirmations=json.loads(affirmations_json) if affirmations_json else [],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/get_sentiment_overview", response_model=SentimentDataResponse)
def get_sentiment_overview(
    currentUser: UserId = Depends(get_current_userId),
    db: Session = Depends(get_session)
):
    if not currentUser:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    journal_entries = db.query(journals_schema.Journal).filter(
        journals_schema.Journal.user_id == currentUser.id
    ).order_by(journals_schema.Journal.created_at.asc()).all()

    if not journal_entries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Journal not found")

    response_data = [
        SentimentDataRequest(
            entry_id=entry.id,
            title=entry.title,
            timestamp=entry.created_at,
            sentiment_label=entry.sentiment_label,
            sentiment_score=entry.sentiment_score,
        )
        for entry in journal_entries
    ]

    return SentimentDataResponse(data=response_data)
