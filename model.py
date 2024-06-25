from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Form
from pydantic import BaseModel
import asyncio
from datetime import datetime
from typing import List

Base = declarative_base()


class UserTable(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    key = Column(String)
    hwid = Column(String)
    sub_start = Column(DateTime)
    sub_end = Column(DateTime)
    role = Column(String)
    freezed = Column(Boolean)
    thread_count = Column(Integer)
    application_count = Column(Integer)
    link_pinned = Column(String)
    
class TaskTable(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    task_status = Column(String)
    task_id = Column(String)
    task_delay = Column(Integer)
    task_user = Column(String)
    task_datetime = Column(DateTime)
    threads_count = Column(Integer)
    task_work = Column(Integer)
    
class ProxyTable(Base):
    __tablename__ = 'proxy'

    id = Column(Integer, primary_key=True)
    proxy_host = Column(String)
    proxy_port = Column(String)
    proxy_username = Column(String)
    proxy_password = Column(String)
    proxy_user_id = Column(String)
    proxy_datetime = Column(DateTime)
    
    
class AccountTable(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    acc_login = Column(String)
    acc_password = Column(String)
    acc_cookie = Column(String)
    acc_user_id = Column(String)
    acc_datetime = Column(DateTime, default=datetime.now)
    
    
class UserRegRequestForm:
	
    def __init__(
        self,
        username: str = Form(),
        key: str = Form(),
        hwid: str = Form(),
        thread_count: int = Form(),
        application_count: int = Form(),
        link_pinned: str = Form(default=None),
        sub_end_time: int = Form(),
        role: str = Form()
    ):
        self.username = username
        self.key = key
        self.hwid = hwid
        self.thread_count = thread_count
        self.application_count = application_count
        self.link_pinned = link_pinned
        self.sub_end_time = sub_end_time
        self.role = role

class ScheduleTaskRequest(BaseModel):
    delay: int
    bot_work_time: int
    streamer_id: str
    num_tasks: int
    cool_down_tasks: int
    
class ScheduledTask:
    def __init__(self, task_id: str, username: str, num_tasks: int, streamer_id: str, status: str, task_delay: int, creation_time: datetime, end_time: datetime, threads_count_status: int):
        self.task_id = task_id
        self.username = username
        self.num_tasks = num_tasks
        self.streamer_id = streamer_id
        self.status = status
        self.task_delay = task_delay 
        self.creation_time = creation_time 
        self.end_time = end_time 
        self.threads_count_status = threads_count_status 
        self.cancel_flag = asyncio.Event()
        


class OAuth2PasswordRequestFormSignin:
	
    def __init__(
        self,
        username: str = Form(),
        user_key: str = Form(),
        hwid: str = Form(),
    ):
        self.username = username
        self.user_key = user_key
        self.hwid = hwid

class TaskRegRequestForm:
	
    def __init__(
        self,
        task_status: str = Form(),
        task_id: str = Form(),
        task_delay: int = Form(default=None),
        task_user: str = Form(),
        task_datetime: datetime = Form(),
        threads_count: int = Form(default=None),
        task_work: int = Form(default=None)
    ):
        self.task_status = task_status
        self.task_id = task_id
        self.task_delay = task_delay
        self.task_user = task_user
        self.task_datetime = task_datetime
        self.threads_count = threads_count
        self.task_work = task_work
