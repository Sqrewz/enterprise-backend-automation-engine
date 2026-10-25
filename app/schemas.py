from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import TaskStatus

class Token(BaseModel): access_token: str; token_type: str = "bearer"
class UserCreate(BaseModel): email: EmailStr; password: str = Field(min_length=12); role: str = "member"
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; email:EmailStr; role:str; created_at:datetime
class TaskCreate(BaseModel): title:str=Field(min_length=1,max_length=200); description:str|None=None; status:TaskStatus=TaskStatus.todo
class TaskUpdate(BaseModel): title:str|None=Field(default=None,min_length=1,max_length=200); description:str|None=None; status:TaskStatus|None=None
class TaskOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; title:str; description:str|None; status:str; owner_id:int; created_at:datetime
class WorkflowCreate(BaseModel): name:str=Field(min_length=1,max_length=150); definition:dict[str, Any]=Field(default_factory=dict); active:bool=True
class WorkflowOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; name:str; definition:dict[str, Any]; active:bool; created_by:int; created_at:datetime
class Page(BaseModel): items:list[Any]; total:int; page:int; size:int
class ReportRequest(BaseModel): title:str=Field(default="Business Intelligence Report",max_length=200); records:list[dict[str, Any]]; schedule: str | None = None
class AskRequest(BaseModel): question:str=Field(min_length=3,max_length=4000)
class AskResponse(BaseModel): answer:str; sources:list[int]
class WebhookResponse(BaseModel): accepted:bool; duplicate:bool=False
