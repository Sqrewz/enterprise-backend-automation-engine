from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models import Document

async def answer_question(session: AsyncSession, question: str) -> tuple[str, list[int]]:
    words=[w for w in question.lower().split() if len(w)>2]
    docs=(await session.scalars(select(Document).order_by(Document.created_at.desc()).limit(50))).all()
    ranked=sorted(docs, key=lambda d: sum(w in d.content.lower() for w in words), reverse=True)[:4]
    context="\n\n".join(f"[Document {d.id}: {d.filename}]\n{d.content[:5000]}" for d in ranked if d.content)
    if not context: return "The knowledge base contains no usable matching documents.", []
    settings=get_settings()
    if not settings.gemini_api_key:
        return f"Gemini is not configured. Relevant context:\n{context[:1500]}", [d.id for d in ranked]
    from google import genai
    client=genai.Client(api_key=settings.gemini_api_key)
    prompt=f"Answer only using this enterprise knowledge base. Cite document IDs.\n\n{context}\n\nQuestion: {question}"
    response=client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text or "No answer generated.", [d.id for d in ranked]
