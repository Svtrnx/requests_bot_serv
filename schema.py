from pydantic import BaseModel, Field
from typing import List, Optional, Generic, TypeVar
from pydantic.generics import GenericModel
from datetime import datetime


class UserSchema(BaseModel):
    id: int
    username: Optional[str]=None
    key: Optional[str]=None
    hwid: Optional[str]=None
    sub_start: Optional[datetime]=None
    sub_end: Optional[datetime]=None
    adb_address: Optional[str]=None
    role: Optional[str]=None
    freezed: Optional[bool]=None
    thread_count: Optional[int]=None
    application_count: Optional[int]=None
    link_pinned: Optional[bool]=None
    
    class Config:
        orm_mode = True
        

class TaskSchema(BaseModel):
    id: int
    task_status: Optional[str]=None
    task_id: Optional[str]=None
    task_delay: Optional[int]=None
    task_user: Optional[str]=None
    task_datetime: Optional[datetime]=None
    threads_count: Optional[int]=None
    task_work: Optional[int]=None
    
    class Config:
        orm_mode = True
        
        
class Token(BaseModel):
    access_token: str
    token_type: str

    