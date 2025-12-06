"""Unanswered Questions and Business Insights API endpoints (V4 features)."""
from typing import Optional, List
from pydantic import BaseModel
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body
import yaml

from app.db.database import get_db_connection
from app.repositories import business_repo
from app.api.chat import invalidate_agent_cache

router = APIRouter(prefix="/insights", tags=["Insights"])


class UnansweredQuestion(BaseModel):
    """Unanswered question model."""
    id: str
    question_text: str
    category: Optional[str] = None
    occurrence_count: int = 1
    last_asked_at: Optional[str] = None
    suggested_answer: Optional[str] = None
    is_resolved: bool = False
    created_at: str


class UnansweredQuestionsResponse(BaseModel):
    """Response for listing unanswered questions."""
    questions: List[UnansweredQuestion]
    total: int
    categories: dict


@router.get("/{business_id}/unanswered", response_model=UnansweredQuestionsResponse)
async def list_unanswered_questions(
    business_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List unanswered questions for a business, sorted by occurrence count."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM unanswered_questions WHERE business_id = ?"
        params = [business_id]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if resolved is not None:
            query += " AND is_resolved = ?"
            params.append(1 if resolved else 0)
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get categories summary
        cursor.execute("""
            SELECT category, COUNT(*) as count, SUM(occurrence_count) as total_occurrences
            FROM unanswered_questions 
            WHERE business_id = ? AND is_resolved = 0
            GROUP BY category
        """, [business_id])
        categories = {}
        for row in cursor.fetchall():
            cat = row[0] or "uncategorized"
            categories[cat] = {"count": row[1], "occurrences": row[2]}
        
        # Get paginated results
        query += " ORDER BY occurrence_count DESC, last_asked_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        questions = []
        for row in rows:
            questions.append(UnansweredQuestion(
                id=row[0],
                question_text=row[2],
                category=row[3],
                occurrence_count=row[4],
                last_asked_at=row[5],
                suggested_answer=row[6],
                is_resolved=bool(row[7]),
                created_at=row[8]
            ))
        
        return UnansweredQuestionsResponse(
            questions=questions,
            total=total,
            categories=categories
        )


@router.post("/{business_id}/unanswered", response_model=UnansweredQuestion)
async def log_unanswered_question(
    business_id: str,
    question_text: str = Body(..., embed=True),
    category: Optional[str] = Body(None, embed=True)
):
    """Log a new unanswered question or increment existing one."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check for similar question (exact match for now)
        cursor.execute("""
            SELECT id, occurrence_count FROM unanswered_questions
            WHERE business_id = ? AND LOWER(question_text) = LOWER(?) AND is_resolved = 0
        """, [business_id, question_text.strip()])
        
        existing = cursor.fetchone()
        now = datetime.now().isoformat()
        
        if existing:
            # Increment count
            cursor.execute("""
                UPDATE unanswered_questions 
                SET occurrence_count = occurrence_count + 1, last_asked_at = ?
                WHERE id = ?
            """, [now, existing[0]])
            conn.commit()
            
            cursor.execute("SELECT * FROM unanswered_questions WHERE id = ?", [existing[0]])
            row = cursor.fetchone()
        else:
            # Create new
            question_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO unanswered_questions 
                (id, business_id, question_text, category, occurrence_count, last_asked_at, created_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, [question_id, business_id, question_text.strip(), category, now, now])
            conn.commit()
            
            cursor.execute("SELECT * FROM unanswered_questions WHERE id = ?", [question_id])
            row = cursor.fetchone()
        
        return UnansweredQuestion(
            id=row[0],
            question_text=row[2],
            category=row[3],
            occurrence_count=row[4],
            last_asked_at=row[5],
            suggested_answer=row[6],
            is_resolved=bool(row[7]),
            created_at=row[8]
        )


@router.put("/{business_id}/unanswered/{question_id}/resolve")
async def resolve_question(
    business_id: str,
    question_id: str,
    answer: str = Body(..., embed=True),
    add_to_faq: bool = Body(False, embed=True)
):
    """Mark a question as resolved and optionally add to FAQs."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get the question
        cursor.execute("""
            SELECT question_text FROM unanswered_questions 
            WHERE id = ? AND business_id = ?
        """, [question_id, business_id])
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question_text = row[0]
        
        # Mark as resolved
        cursor.execute("""
            UPDATE unanswered_questions 
            SET is_resolved = 1, suggested_answer = ?
            WHERE id = ?
        """, [answer, question_id])
        conn.commit()
    
    # Add to FAQ if requested
    if add_to_faq:
        config = business_repo.get_config(business_id) or {}
        faqs = config.get('faqs', [])
        faqs.append({'question': question_text, 'answer': answer})
        config['faqs'] = faqs
        
        config_yaml = yaml.dump(config, default_flow_style=False)
        business_repo.update_config_yaml(business_id, config_yaml)
        invalidate_agent_cache(business_id)
    
    return {
        "message": "Question resolved",
        "added_to_faq": add_to_faq,
        "question": question_text,
        "answer": answer
    }


@router.delete("/{business_id}/unanswered/{question_id}")
async def delete_unanswered_question(business_id: str, question_id: str):
    """Delete an unanswered question."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM unanswered_questions 
            WHERE id = ? AND business_id = ?
        """, [question_id, business_id])
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Question not found")
        
        conn.commit()
    
    return {"message": "Question deleted"}


@router.put("/{business_id}/unanswered/{question_id}/category")
async def update_question_category(
    business_id: str,
    question_id: str,
    category: str = Body(..., embed=True)
):
    """Update the category of an unanswered question."""
    if not business_repo.exists(business_id):
        raise HTTPException(status_code=404, detail="Business not found")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE unanswered_questions 
            SET category = ?
            WHERE id = ? AND business_id = ?
        """, [category, question_id, business_id])
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Question not found")
        
        conn.commit()
    
    return {"message": "Category updated", "category": category}
