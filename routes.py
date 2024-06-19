from fastapi import Depends, APIRouter, BackgroundTasks, HTTPException, Body, Response, Request, status, WebSocket, WebSocketDisconnect
from starlette.responses import RedirectResponse
import asyncio
from sqlalchemy.orm import Session
from invoke_requests import main, make_request
import json
from typing import Dict, List, Deque
from collections import deque
from requests import create_user, create_task_func
from connection import get_db
from datetime import datetime, timedelta
import model
import random
from schema import Token
import string
import userController
import websockets
from authSecurity import create_access_token, get_current_user
from dotenv import load_dotenv
from config import ACCESS_TOKEN_EXPIRE_MINUTES
import logging

load_dotenv()

userRouter = APIRouter()


scheduled_tasks = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_buffers: Dict[str, Deque[str]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

        
        if task_id in self.message_buffers:
            while self.message_buffers[task_id]:
                message = self.message_buffers[task_id].popleft()
                await websocket.send_text(message)

    def disconnect(self, task_id: str):
        self.active_connections.pop(task_id, None)

    async def send_personal_message(self, message: str, task_id: str):
        websocket = self.active_connections.get(task_id)
        if websocket:
            await websocket.send_text(message)
        else:
            
            if task_id not in self.message_buffers:
                self.message_buffers[task_id] = deque()
            self.message_buffers[task_id].append(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@userRouter.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", task_id)
            await manager.broadcast(f"Client #{task_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(task_id)
        await manager.broadcast(f"Client #{task_id} left the chat")

@userRouter.post("/send-message/{task_id}")
async def send_message(task_id: str, message: str):
    await manager.send_personal_message(message, task_id)
    return {"message": "Message sent"}

@userRouter.post("/connect-websocket/")
async def connect_websocket(task_id: str):
    uri = f"ws://localhost:8000/ws/{task_id}"
    async def websocket_client():
        async with websockets.connect(uri) as websocket:
            await websocket.send("Hello Server!")
            response = await websocket.recv()
            print(f"Received message from server: {response}")
    asyncio.create_task(websocket_client())
    return {"message": "WebSocket client started"}



def generate_random_id(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length))

async def read_proxies_from_file(filename):
    proxies = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                proxies.append(line.strip())
    except FileNotFoundError:
        print(f"File {filename} dont found.")
    return proxies


#############################################################################
async def perform_custom_task(task_id, delay, bot_work_time, scheduled_task, model_id, num_tasks, cool_down_tasks):
    try:
        print(scheduled_task.username)
        user = scheduled_task.username
        # await asyncio.sleep(3)
        # await send_message(task_id=task_id, message='123')
        await asyncio.sleep(delay)
        await connect_websocket(task_id=user)
        
        # await increment_threads_count_status(task_id, 3)
        info = await get_task_status(task_id=task_id)
        print(info)
        if info['status'] == 'scheduled':
            current_time = datetime.now()
            bot_work_time_minutes = current_time + timedelta(minutes=bot_work_time)

            # websocket = await websockets.connect(f'ws://localhost:8000/ws/{task_id}')
            await update_task_status(task_id, 'active')
            try:
                with open('reserv.json', 'r') as file:
                    data = json.load(file)
            except FileNotFoundError:
                print("File not found")
                data = []

            if isinstance(data, list):
                print('Total accounts: ', len(data))

            credentials_data = await main()

            if not credentials_data:
                return

            cool_down = cool_down_tasks
            num_tasks_ = num_tasks

            proxies = await read_proxies_from_file('proxy.txt')
            if not proxies:
                print("Failed to load the proxy from the file.")
                return
            current_iteration = 0
            tasks = []
            for i in range(num_tasks_):
                proxy = proxies[i % len(proxies)]
                task = asyncio.create_task(make_request(credentials_data[i], proxy, bot_work_time_minutes, scheduled_task, model_id))
                tasks.append(task)
                current_iteration += 1
                await send_message(task_id=user, message=f'{task_id}:{current_iteration}')
                await update_task_thread_count(task_id=task_id, new_thread_count=current_iteration)
                await asyncio.sleep(cool_down)
                if scheduled_task.cancel_flag.is_set() or datetime.now() >= bot_work_time_minutes:
                    print(f"Task {task_id} has been canceled")
                    break

            for task in tasks:
                await task 
        print(f"Execution of task {task_id} completed")
        info_cancel = await cancel_task(task_id)
        print(info_cancel)
    except Exception as e:
        print(f"Task error {task_id}: {e}")


@userRouter.get("/index")
def get_index(request: Request):
    return {"request": request.url}


@userRouter.get("/tasks")
async def get_active_tasks(current_user: model.UserTable = Depends(get_current_user)):
    active_tasks = []
    for task_id, scheduled_task in scheduled_tasks.items():
        if not scheduled_task.cancel_flag.is_set() and scheduled_task.username == current_user.username:
            active_tasks.append({
                "task_id": task_id,
                "threads_count": scheduled_task.num_tasks,
                "username": scheduled_task.username,
                "streamer_id": scheduled_task.streamer_id,
                "task_delay": scheduled_task.task_delay,
                "creation_time": scheduled_task.creation_time,
                "threads_count_status": scheduled_task.threads_count_status,
                "status": scheduled_task.status
            })
    return active_tasks

async def update_task_status(task_id: str, new_status: str):
    if task_id not in scheduled_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = scheduled_tasks[task_id]
    
    task.status = new_status
    
    return {"message": f"Task {task_id} status updated to {new_status}"}


async def update_task_thread_count(task_id: str, new_thread_count: int):
    if task_id not in scheduled_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = scheduled_tasks[task_id]
    
    task.threads_count_status = new_thread_count
    
    return {"message": f"Task {task_id} status updated to {new_thread_count}"}

@userRouter.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    if task_id in scheduled_tasks:
        scheduled_task = scheduled_tasks[task_id]
        return {
            "task_id": task_id,
            "status": "cancelled" if scheduled_task.cancel_flag.is_set() else "scheduled"
        }
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@userRouter.post("/schedule-task/")
async def schedule_task(request: model.ScheduleTaskRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    if current_user.link_pinned != None:
        if current_user.link_pinned != request.streamer_id:
            return {'Invalid streamer id'}
    
    active_tasks = await get_active_tasks(current_user)

    if len(active_tasks) >= current_user.application_count:
        return {'You have been reached the applications limit'}
    
    total_threads_count = sum(task["threads_count"] for task in active_tasks)
    if total_threads_count + request.num_tasks > current_user.thread_count or request.num_tasks > current_user.thread_count:
        return {'You have been reached the threads limit'}

    task_id = generate_random_id()
    threads_count_status = 0
    scheduled_task = model.ScheduledTask(task_id, current_user.username, request.num_tasks, request.streamer_id, "scheduled", request.delay, datetime.now(), threads_count_status)
    scheduled_tasks[task_id] = scheduled_task
    background_tasks.add_task(perform_custom_task, task_id, request.delay, request.bot_work_time, scheduled_task, request.streamer_id, request.num_tasks, request.cool_down_tasks)
    form_data = model.TaskRegRequestForm(
        task_status="scheduled",
        task_id=request.streamer_id,
        task_delay=request.delay,
        task_user=current_user.username,
        task_datetime=datetime.now(),
        threads_count=request.num_tasks,
        task_work=request.bot_work_time
    )
    await create_task(db=db, form_data=form_data)
    print(f"Task {task_id} is scheduled to run in {request.delay} seconds")
    return {"task_id": task_id}

@userRouter.delete("/cancel-task/{task_id}")
async def cancel_task(task_id: str, db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    if task_id in scheduled_tasks:
        scheduled_task = scheduled_tasks[task_id]
        if scheduled_task.username == current_user.username:
            scheduled_task.cancel_flag.set()
            form_data = model.TaskRegRequestForm(
                task_status="deleted",
                task_id=scheduled_task.task_id,
                task_delay=0,
                task_user=scheduled_task.username,
                task_datetime=datetime.now(),
                threads_count=0,
                task_work=0
            )
            await create_task(db=db, form_data=form_data)
            return {"message": f"Task {task_id} canceled successfully"}
        else:
            return {"error": "You do not have permission to cancel this task"}
    else:
        return {"error": "Task with this ID was not found"}

    
    
@userRouter.post('/create_reg_account')
async def reg_account(db: Session = Depends(get_db), form_data: model.UserRegRequestForm = Depends()):
    current_time = datetime.now()
    print(current_time)
    new_time = current_time + timedelta(days=form_data.sub_end_time)
    new_user_reg = model.UserTable(
        username=form_data.username,
        key=form_data.key,
        hwid=form_data.hwid,
        sub_start=current_time,
        sub_end=new_time,
        role=form_data.role,
        freezed=False
    )
    user_reg = create_user(db=db, user_reg=new_user_reg)
    return {'data': user_reg}

@userRouter.post('/signin', response_model=Token)
async def signin_auth(response:Response, db: Session = Depends(get_db), form_data: model.OAuth2PasswordRequestFormSignin = Depends()):
    user = userController.authenticate_user(
        db          = db,
        username    = form_data.username,
        user_key    = form_data.user_key,
        hwid        = form_data.hwid
    )
    if not user:
        raise HTTPException(status_code=301, detail="Incorrect account information")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url='/index',status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token",value=f"Bearer {access_token}", samesite='none', httponly=True,
                    secure=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60) 
    return response


@userRouter.get("/check-auth")
async def check_auth(db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    # user = current_user.username
    return current_user


# @userRouter.post('/create_task')
async def create_task(db: Session = Depends(get_db), form_data: model.TaskRegRequestForm = Depends()):
    current_time = datetime.now()
    print(current_time)
    new_task_reg = model.TaskTable(
        task_status=form_data.task_status,
        task_id=form_data.task_id,
        task_delay=form_data.task_delay,
        task_user=form_data.task_user,
        task_datetime=form_data.task_datetime,
        threads_count=form_data.threads_count,
        task_work=form_data.task_work,
    )
    task_reg = create_task_func(db=db, task_reg=new_task_reg)
    return {'data': task_reg}


# @userRouter.get('/get_warming_links')
# def get_warming_links_function(current_user_hwid: str, unique_id: str, username: str, db: Session = Depends(get_db)):
#     user_hwid = query_tiktok_table_check_auth(current_user_hwid)
#     if user_hwid is None:
#         raise HTTPException(status_code=311, detail="Autentication failed")
#     else:
#         warming_links = query_tiktok_warming_links(username=username, unique_id=unique_id)
#         return {"warming_links": warming_links}	