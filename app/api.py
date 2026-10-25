import hashlib, hmac, json
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.security import create_access_token, decode_token, hash_password, require_roles, verify_password
from app.db import get_session
from app.models import Document, Role, Task, User, WebhookEvent, Workflow
from app.schemas import AskRequest, AskResponse, Page, ReportRequest, TaskCreate, TaskOut, TaskUpdate, Token, UserCreate, UserOut, WebhookResponse, WorkflowCreate, WorkflowOut
from app.services.documents import save_and_extract
from app.services.rag import answer_question
from app.workers.tasks import generate_report, publish_outbound_event

router=APIRouter(prefix="/api/v1")
DB=Annotated[AsyncSession, Depends(get_session)]; Current=Annotated[dict[str,str], Depends(decode_token)]

@router.post("/auth/register", response_model=UserOut, status_code=201)
async def register(data:UserCreate, db:DB):
    if data.role not in {r.value for r in Role}: raise HTTPException(422,"Invalid role")
    if await db.scalar(select(User).where(User.email==data.email)): raise HTTPException(409,"Email already registered")
    user=User(email=str(data.email), password_hash=hash_password(data.password), role=data.role); db.add(user); await db.commit(); await db.refresh(user); return user
@router.post("/auth/login", response_model=Token)
async def login(form:Annotated[OAuth2PasswordRequestForm,Depends()],db:DB):
    user=await db.scalar(select(User).where(User.email==form.username))
    if not user or not verify_password(form.password,user.password_hash): raise HTTPException(status.HTTP_401_UNAUTHORIZED,"Incorrect email or password")
    return Token(access_token=create_access_token(str(user.id),user.role))

@router.post("/tasks",response_model=TaskOut,status_code=201)
async def create_task(data:TaskCreate,db:DB,user:Current):
    task=Task(**data.model_dump(),owner_id=int(user["sub"])); db.add(task); await db.commit(); await db.refresh(task); return task
@router.get("/tasks",response_model=Page)
async def list_tasks(db:DB,user:Current,page:int=Query(1,ge=1),size:int=Query(20,ge=1,le=100),status_filter:str|None=Query(None,alias="status")):
    query=select(Task); count=select(func.count()).select_from(Task)
    if user["role"]==Role.member.value: query=query.where(Task.owner_id==int(user["sub"])); count=count.where(Task.owner_id==int(user["sub"]))
    if status_filter: query=query.where(Task.status==status_filter); count=count.where(Task.status==status_filter)
    items=(await db.scalars(query.order_by(Task.id.desc()).offset((page-1)*size).limit(size))).all(); return Page(items=[TaskOut.model_validate(x) for x in items],total=await db.scalar(count) or 0,page=page,size=size)
@router.patch("/tasks/{task_id}",response_model=TaskOut)
async def update_task(task_id:int,data:TaskUpdate,db:DB,user:Current):
    task=await db.get(Task,task_id)
    if not task: raise HTTPException(404,"Task not found")
    if user["role"]==Role.member.value and task.owner_id!=int(user["sub"]): raise HTTPException(403,"Not task owner")
    for key,value in data.model_dump(exclude_unset=True).items(): setattr(task,key,value.value if hasattr(value,"value") else value)
    await db.commit(); await db.refresh(task); return task

@router.post("/workflows", response_model=WorkflowOut, status_code=201)
async def create_workflow(data:WorkflowCreate, db:DB, user:Annotated[dict,Depends(require_roles(Role.admin.value,Role.manager.value))]):
    if await db.scalar(select(Workflow).where(Workflow.name==data.name)): raise HTTPException(409,"Workflow name already exists")
    workflow=Workflow(**data.model_dump(),created_by=int(user["sub"])); db.add(workflow); await db.commit(); await db.refresh(workflow); return workflow
@router.get("/workflows", response_model=list[WorkflowOut])
async def list_workflows(db:DB,_user:Current):
    return (await db.scalars(select(Workflow).order_by(Workflow.name))).all()

@router.post("/documents",status_code=201)
async def upload_document(file:Annotated[UploadFile,File(...)],db:DB,user:Current):
    path,content,meta=await save_and_extract(file); doc=Document(filename=file.filename or "upload",content_type=file.content_type or "",storage_path=str(path),content=content,metadata_json=meta,uploaded_by=int(user["sub"])); db.add(doc); await db.commit(); await db.refresh(doc); return {"id":doc.id,"filename":doc.filename,"metadata":meta}
@router.post("/knowledge/ask",response_model=AskResponse)
async def ask(data:AskRequest,db:DB,_user:Current):
    answer,sources=await answer_question(db,data.question); return AskResponse(answer=answer,sources=sources)
@router.post("/reports",status_code=202)
async def create_report(data:ReportRequest,_user:Annotated[dict,Depends(require_roles(Role.admin.value,Role.manager.value))]):
    job=generate_report.delay(data.records,data.title); return {"job_id":job.id,"status":"queued"}
@router.post("/webhooks/{event_type}",response_model=WebhookResponse,status_code=202)
async def ingest_webhook(event_type:str,request:Request,background:BackgroundTasks,db:DB):
    raw=await request.body(); signature=request.headers.get("X-Signature",""); expected=hmac.new(get_settings().webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,expected): raise HTTPException(401,"Invalid webhook signature")
    key=request.headers.get("Idempotency-Key")
    if not key: raise HTTPException(400,"Idempotency-Key required")
    if await db.scalar(select(WebhookEvent).where(WebhookEvent.idempotency_key==key)): return WebhookResponse(accepted=True,duplicate=True)
    try: payload=json.loads(raw)
    except json.JSONDecodeError as exc: raise HTTPException(400,"Invalid JSON") from exc
    db.add(WebhookEvent(idempotency_key=key,event_type=event_type,payload=payload)); await db.commit()
    background.add_task(publish_outbound_event.delay,event_type,payload)
    return WebhookResponse(accepted=True)
