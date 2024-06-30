from fastapi import Depends, APIRouter, BackgroundTasks, HTTPException, Body, Response, Request, status, WebSocket, WebSocketDisconnect
from starlette.responses import RedirectResponse
import asyncio
from sqlalchemy.orm import Session
from invoke_requests import main, make_request
import json
from typing import Dict, List, Deque
from collections import deque
from requests import create_user, delete_account, get_proxy_list_count, get_accounts_list_count, get_tasks_list, get_user_only_by_username, delete_user, take_users, delete_account_by_username, get_accounts_list, create_task_func, create_account_list, create_proxy_list, get_proxy_list, delete_proxy
from connection import get_db
from datetime import datetime, timedelta, timezone
import model
from bs4 import BeautifulSoup
import aiohttp
import random
from schema import Token
import string
import userController
import websockets
from authSecurity import create_access_token, get_current_user
from fake_useragent import UserAgent
from dotenv import load_dotenv
from config import ACCESS_TOKEN_EXPIRE_MINUTES
import logging
from config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASS
import time
from curl_cffi.requests import AsyncSession
# from asyncio import WindowsSelectorEventLoopPolicy

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
    uri = f"wss://extended-candide-mypula-43126005.koyeb.app/ws/{task_id}"
    async def websocket_client():
        async with websockets.connect(uri) as websocket:
            # await websocket.send("Hello Server!")
            response = await websocket.recv()
            print(f"Received message from server: {response}")
    asyncio.create_task(websocket_client())
    return {"message": "WebSocket client started"}



def generate_random_id(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length))


#############################################################################
async def perform_custom_task(task_id, delay, bot_work_time, scheduled_task, model_id, num_tasks, cool_down_tasks, db, num_tasks_first, num_tasks_second):
    try:
        proxy_list = get_proxy_list_count(db=db, username=scheduled_task.username, start_id=num_tasks_first, end_id=num_tasks_second)
        accounts_list = get_accounts_list_count(db=db, username=scheduled_task.username, start_id=num_tasks_first, end_id=num_tasks_second)
        print('account list:', len(accounts_list))
        print('proxy_list list:', len(proxy_list))
        cookies = []
        for cookie in accounts_list:
            formatted_cookie = f"{cookie.acc_cookie}"
            cookies.append(formatted_cookie)
        # print(cookies)
        
        proxies = []
        for proxy in proxy_list:
            formatted_proxy = f"{proxy.proxy_username}:{proxy.proxy_password}@{proxy.proxy_host}:{proxy.proxy_port}"
            proxies.append(formatted_proxy)
        # print(proxies)
        user = scheduled_task.username
        # await asyncio.sleep(3)
        # await send_message(task_id=task_id, message='123')
        if delay > 0:
            await asyncio.sleep(delay)
        await connect_websocket(task_id=user)
        
        # await increment_threads_count_status(task_id, 3)
        info = await get_task_status(task_id=task_id)
        print(info)
        if info['status'] == 'scheduled':
            current_time = datetime.now(timezone.utc)
            bot_work_time_minutes = current_time + timedelta(minutes=bot_work_time)

            # websocket = await websockets.connect(f'ws://localhost:8000/ws/{task_id}')
            await update_task_status(task_id, 'active')
            # try:
            #     with open('reserv.json', 'r') as file:
            #         data = json.load(file)
            # except FileNotFoundError:
            #     print("File not found")
            #     data = []

            if isinstance(cookies, list):
                print('Total accounts: ', len(cookies))

            # credentials_data = await main()

            # if not credentials_data:
            #     return

            cool_down = cool_down_tasks
            num_tasks_ = num_tasks

            # proxies = await read_proxies_from_file('proxy.txt')
            # if not proxies:
            #     print("Failed to load the proxy from the file.")
            #     return
            # print(cookies)
            current_iteration = 0
            tasks = []
            for i in range(num_tasks_):
                proxy = proxies[i % len(proxies)]
                print('cookies[i]', cookies[i])
                task = asyncio.create_task(make_request(cookies[i], proxy, bot_work_time_minutes, scheduled_task, model_id, random.randint(0, 1)))
                tasks.append(task)
                current_iteration += 1
                await send_message(task_id=user, message=f'{task_id}:{current_iteration}')
                await update_task_thread_count(task_id=task_id, new_thread_count=current_iteration)
                await asyncio.sleep(cool_down)
                if scheduled_task.cancel_flag.is_set() or datetime.now(timezone.utc) >= bot_work_time_minutes:
                    print(f"Task {task_id} has been canceled")
                    break

            for task in tasks:
                await task 
        print(f"Execution of task {task_id} completed")
        # info_cancel = await cancel_task(task_id)
        # print(info_cancel)
        if scheduled_task.cancel_flag.set():
            form_data = model.TaskRegRequestForm(
                task_status="deleted",
                task_id=scheduled_task.task_id,
                task_delay=0,
                task_user=scheduled_task.username,
                task_datetime=datetime.now(timezone.utc),
                threads_count=0,
                task_work=0
            )
            await create_task(db=db, form_data=form_data)
        else:
            form_data = model.TaskRegRequestForm(
                task_status="active",
                task_id=scheduled_task.task_id,
                task_delay=0,
                task_user=scheduled_task.username,
                task_datetime=datetime.now(timezone.utc),
                threads_count=0,
                task_work=0
            )
            await create_task(db=db, form_data=form_data)
            scheduled_task.cancel_flag.set()
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
                "end_time": scheduled_task.end_time,
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
            raise HTTPException(status_code=400, detail="Invalid streamer id, you have limited access")
    
    active_tasks = await get_active_tasks(current_user)
    
    active_tasks_with_status = [task for task in active_tasks if task.get("status") == "active"]
    new_task_status = ''
    if request.delay > 0:
        new_task_status = 'scheduled'
    else:
        new_task_status = 'active'
    
    check = False
    if new_task_status == "scheduled" and len(active_tasks_with_status) >= current_user.application_count:
        check = True
    
    if new_task_status == "active" and len(active_tasks_with_status) >= current_user.application_count:
        raise HTTPException(status_code=400, detail="You have reached the applications limit")
    
    if check == True:
        print('check')
        for task in active_tasks:
            creation_time = task["creation_time"]
            end_time = task["end_time"]
            
            if creation_time <= datetime.now(timezone.utc) + timedelta(seconds=request.delay) <= end_time:
                raise HTTPException(status_code=400, detail="This time is already busy!")
    
    num_tasks_first, num_tasks_second = request.num_tasks.split(":")
    print(num_tasks_first, num_tasks_second)
    sum_time = int(num_tasks_second) - int(num_tasks_first)
    if sum_time > current_user.thread_count:
        raise HTTPException(status_code=400, detail="You have reached the threads limit")


    print(request.bot_work_time)
    end_time_ = datetime.now(timezone.utc) + timedelta(minutes=request.bot_work_time)
    start_time_ = ''
    if request.delay > 0:
        start_time_ = datetime.now(timezone.utc) + timedelta(seconds=request.delay)
        end_time_ = datetime.now(timezone.utc) + timedelta(minutes=request.bot_work_time) + timedelta(seconds=request.delay)
    else:
        start_time_ = datetime.now(timezone.utc)
        end_time_ = datetime.now(timezone.utc) + timedelta(minutes=request.bot_work_time)
    task_id = generate_random_id()
    threads_count_status = 0
    scheduled_task = model.ScheduledTask(task_id, current_user.username, sum_time, request.streamer_id, "scheduled", request.delay, start_time_, end_time_, threads_count_status)
    scheduled_tasks[task_id] = scheduled_task
    background_tasks.add_task(perform_custom_task, task_id, request.delay, request.bot_work_time, scheduled_task, request.streamer_id, sum_time, request.cool_down_tasks, db, int(num_tasks_first), int(num_tasks_second))
    form_data = model.TaskRegRequestForm(
        task_status="scheduled",
        task_id=request.streamer_id,
        task_delay=request.delay,
        task_user=current_user.username,
        task_datetime=datetime.now(timezone.utc),
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
                task_datetime=datetime.now(timezone.utc),
                threads_count=0,
                task_work=0
            )
            await create_task(db=db, form_data=form_data)
            return {"message": f"Task {task_id} canceled successfully"}
        else:
            raise HTTPException(status_code=400, detail="You do not have permission to cancel this task")
    else:
        raise HTTPException(status_code=400, detail="Task with this ID was not found")

    
    
@userRouter.post('/create_reg_account')
async def reg_account(db: Session = Depends(get_db), form_data: model.UserRegRequestForm = Depends(), current_user: model.UserTable = Depends(get_current_user)):
    if current_user.role == 'admin':
        current_time = datetime.now(timezone.utc)
        new_time = current_time + timedelta(days=form_data.sub_end_time)
        new_user_reg = model.UserTable(
            username=form_data.username,
            key=form_data.key,
            hwid=form_data.hwid,
            thread_count=form_data.thread_count,
            application_count=form_data.application_count,
            link_pinned=form_data.link_pinned,
            sub_start=current_time,
            sub_end=new_time,
            role=form_data.role,
            freezed=False
        )
        user_reg = create_user(db=db, user_reg=new_user_reg)
        return {'data': user_reg}
    else:
        raise HTTPException(status_code=400, detail="Access denied")

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
    current_time = datetime.now(timezone.utc)
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


@userRouter.post('/create-proxy')
def create_proxy_func(proxy_list: List[str] = Body(...), db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    try:
        new_proxies = []
        for proxy in proxy_list:
            credentials, host_info = proxy.split('@')
            proxy_username, proxy_password = credentials.split(':')
            proxy_host, proxy_port = host_info.split(':')
            
            new_proxy = model.ProxyTable(
                proxy_host=proxy_host,
                proxy_port=proxy_port,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
                proxy_user_id=current_user.username,
                proxy_datetime=datetime.now(timezone.utc)
            )
            new_proxies.append(new_proxy)

        create_proxy_list(db=db, proxy_media=new_proxies)
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")
    
    
@userRouter.get('/get-proxy-list')
def get_proxy_list_func(db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    proxy = get_proxy_list(db=db, username=current_user.username)
    return proxy


@userRouter.delete("/delete-proxy")
async def delete_proxy_func(proxy_list: List[str] = Body(...), db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    try:
        print(proxy_list)
        if "all" in proxy_list:
            print("The proxy_list array contains the value 'all'")
            delete_proxy(db=db, proxy_list=proxy_list, user=current_user.username, delete_all_user_proxies=True)
        else:
            print("The proxy_list array does not contain the value 'all'")
            delete_proxy(db=db, proxy_list=proxy_list, user=current_user.username, delete_all_user_proxies=False)
            
  
        return {'status': 'successfully deleted proxy'}
    
    except HTTPException as e:
        return {"error": str(e)}


async def fetch_data_cookies(account, proxy):
    try:
        async with AsyncSession() as session:
            ua = UserAgent()
            username, password = account.split(':')
            # session = requests.Session()

            # print(response.text())
            proxies = { 
                "https" : proxy, 
            }
            try:
                response = await session.get("https://chaturbate.com/auth/login", impersonate="chrome110", proxies=proxies)
            except Exception as e:
                return {}
            # print(response.text)
            csrf_token = ''
            if response.status_code == 200:
                html_content = response.content
                soup = BeautifulSoup(html_content, 'html.parser')
                csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
                # print(csrf_token)
                
            else:
                print(f'Failed to fetch login page. Status code: {response.status_code}')
                
                
            url = 'https://chaturbate.com/auth/login/'
            headers = {
                'Referer': 'https://chaturbate.com/auth/login/',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                "User-Agent": ua.random
            }
            data = {
                'next': '',
                'csrfmiddlewaretoken': csrf_token,
                'username': username,
                'password': password
            }
            try:
                response = await session.post(url, headers=headers, data=data, impersonate="chrome110", proxies=proxies)
            except Exception as e:
                return {}
            print(response.status_code)

            if response.status_code == 200:
                print(session.cookies.get('sessionid'))
                if session.cookies.get('sessionid'):
                    return {"acc_login": username, "acc_password": password, 'acc_cookie': session.cookies.get('sessionid')}
            else:
                print(f"Error to login {username}: {response.status_code}")
    except Exception as e:
        return {}
    
    
async def main_checker_func(accounts, proxies):
    tasks = []
    for account, proxy in zip(accounts, proxies):
        tasks.append(fetch_data_cookies(account, proxy))

    results = await asyncio.gather(*tasks)

    return results    

def sync_main(accounts, proxies):
    # asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    results = [] 
    all_results = asyncio.run(main_checker_func(accounts, proxies))

    for result in all_results:
        if result:
            results.append(result)

    return results

@userRouter.post('/create-account')
def create_account_func(acccount_list: List[str] = Body(...), proxies_list: List[str] = Body(...), db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    try:
        checker_results = sync_main(acccount_list, proxies_list)
        print(checker_results)
        print(len(checker_results))
        new_accounts = [
            model.AccountTable(
                acc_login=account['acc_login'],
                acc_password=account['acc_password'],
                acc_cookie=account['acc_cookie'],
                acc_user_id=current_user.username,
                acc_datetime=datetime.now(timezone.utc),
            )
            for account in checker_results
        ]
        create_account_list(db=db, user=current_user.username, account_media=new_accounts)
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {e}")
    

@userRouter.get('/get-accounts-list')
def get_accounts_list_func(db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    account = get_accounts_list(db=db, username=current_user.username)
    return account


@userRouter.delete("/delete-account")
async def delete_account_func(account_list: List[str] = Body(...), db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    try:
        print(account_list)
        if "all" in account_list:
            print("The account_list array contains the value 'all'")
            delete_account(db=db, account_list=account_list, user=current_user.username, delete_all_user_accounts=True)
        else:
            print("The proxy_list array does not contain the value 'all'")
            delete_account(db=db, account_list=account_list, user=current_user.username, delete_all_user_accounts=False)
            
  
        return {'status': 'successfully deleted accounts'}
    
    except HTTPException as e:
        return {"error": str(e)}
    

async def make_request_check(session, sessionid, username, proxy_url):
    resp = ''
    try:
        print(proxy_url)
        ua = UserAgent()
        headers = {
            "x-requested-with": "XMLHttpRequest",
            "Referer": "https://chaturbate.com",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "User-Agent": ua.random
        }
        cookies = {"sessionid": sessionid}
        url = "https://chaturbate.com/api/ts/accounts/editsettings/?"
        async with session.get(url, headers=headers, cookies=cookies, proxy=f"socks5://{proxy_url}") as response:
            # result = await response.text() 
            # soup = BeautifulSoup(result, 'html.parser')
            # resp = soup

            # found_variables = soup.find_all(string=lambda text: username.lower() in text.lower())

            if response.status == 200:
                return {"username": username, 'sessionid': sessionid}
    except Exception as e:
        print(f"error in make_request_check: {e}\n proxy: {proxy_url}")
    
async def perform_custom_check(proxies, cookies, usernames):
    try:

        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(len(cookies)):
                proxy = proxies[i % len(proxies)]
                sessionid = cookies[i]
                username = usernames[i]
                task = asyncio.create_task(make_request_check(session, sessionid, username, proxy))
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return results
    except Exception as e:
        print(f"error : {e}")

@userRouter.get("/quick-check-validation")
def get_index(db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    proxy_list = get_proxy_list(db=db, username=current_user.username)
    accounts_list = get_accounts_list(db=db, username=current_user.username)
    
    if proxy_list and accounts_list:
    
        formatted_proxies = []
        for proxy in proxy_list:
            formatted_proxy = f"{proxy.proxy_username}:{proxy.proxy_password}@{proxy.proxy_host}:{proxy.proxy_port}"
            formatted_proxies.append(formatted_proxy)
        
        formatted_accounts = []
        for account in accounts_list:
            formatted_account = f"{account.acc_login}"
            formatted_accounts.append(formatted_account)
            
        formatted_cookies = []
        for cookie in accounts_list:
            formatted_cookie = f"{cookie.acc_cookie}"
            formatted_cookies.append(formatted_cookie)
        # return proxy
        
        results = asyncio.run(perform_custom_check(formatted_proxies, formatted_cookies, formatted_accounts))
        # print(results)
        usernames_in_results = [result['username'] for result in results if result]

        not_in_results = [account for account in formatted_accounts if account not in usernames_in_results]
        
        if not_in_results:
            print(not_in_results)
            delete_account_by_username(db, not_in_results, current_user.username)
            return not_in_results
        else:
            return []

    # return {"res": results}
    
@userRouter.get('/get-users')
def get_users_func(db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    if current_user.role == 'admin':
        users = take_users(db=db, username=current_user.username)
        return users
    
@userRouter.delete("/delete-user")
async def delete_user_func(user_id: str = Body(embed=True), db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    if current_user.role == 'admin' or current_user.username == 'booster' or current_user.username == 'kenzo':
        try:
            delete_user(db=db, user_id=user_id, user=current_user.username)
    
            return {'status': 'successfully deleted'}
        except Exception as e:
            raise HTTPException(status_code=400, detail="Access denied")
    else: 
        raise HTTPException(status_code=400, detail="Access denied")
    
    

@userRouter.patch("/update-user")
async def update_user_func(
    form_data: model.UpdateUserRequestForm = Depends(),
    db: Session = Depends(get_db),
    current_user: model.UserTable = Depends(get_current_user)
):
    if current_user.role == 'admin':
        db_user = get_user_only_by_username(db=db, username=form_data.username)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        print(db_user.role)

        # if form_data.username:
        #     db_user.username = form_data.username
        if form_data.key:
            db_user.key = form_data.key
        if form_data.hwid:
            db_user.hwid = form_data.hwid
        if form_data.sub_start:
            db_user.sub_start = form_data.sub_start
        if form_data.sub_end:
            db_user.sub_end = form_data.sub_end
        if form_data.role:
            db_user.role = form_data.role
        if form_data.freezed:
            db_user.freezed = form_data.freezed
        if form_data.thread_count:
            db_user.thread_count = form_data.thread_count
        if form_data.application_count:
            db_user.application_count = form_data.application_count
        if form_data.link_pinned:
            if form_data.link_pinned == 'delete':
                db_user.link_pinned = None
            else:
                db_user.link_pinned = form_data.link_pinned
        

        db.commit()
        db.refresh(db_user)
        return {"user": db_user}
    else: 
        raise HTTPException(status_code=400, detail="Access denied")
    

@userRouter.get('/get-tasks-list')
def get_tasks_list_func(username: str, db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    if current_user.role == 'admin':
        tasks = get_tasks_list(db=db, username=username)
        return tasks
    else: 
        raise HTTPException(status_code=400, detail="Access denied")
    
    
@userRouter.get("/all-active-tasks")
async def get_all_active_tasks(current_user: model.UserTable = Depends(get_current_user)):
    if current_user.role == 'admin':
        active_tasks = []
        for task_id, scheduled_task in scheduled_tasks.items():
            if not scheduled_task.cancel_flag.is_set():
                active_tasks.append({
                    "task_id": task_id,
                    "threads_count": scheduled_task.num_tasks,
                    "username": scheduled_task.username,
                    "streamer_id": scheduled_task.streamer_id,
                    "task_delay": scheduled_task.task_delay,
                    "creation_time": scheduled_task.creation_time,
                    "end_time": scheduled_task.end_time,
                    "threads_count_status": scheduled_task.threads_count_status,
                    "status": scheduled_task.status
                })
        return active_tasks
    else: 
        raise HTTPException(status_code=400, detail="Access denied")
    

async def fetch_data_cookies_checker(account, proxy):
    async with AsyncSession() as session:
        ua = UserAgent()
        usAgent = ua.random
        try:
            username, password = account.split(':')
        except Exception as e:
            return
        # session = requests.Session()

        # print(response.text())
        proxies = { 
            "https" : proxy, 
        }
        try:
            response = await session.get("https://chaturbate.com/auth/login", impersonate="chrome110", proxies=proxies)
        except Exception as e:
            return {"acc_login": username, "acc_password": password, "type": 'error', "token_balance": "0", "transaction": ""}
        
        
        # print(response.text)
        csrf_token = ''
        if response.status_code == 200:
            html_content = response.content
            soup = BeautifulSoup(html_content, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')
            # print(csrf_token)
            
        else:
            print(f'Failed to fetch login page. Status code: {response.status_code}')
            
            
        url = 'https://chaturbate.com/auth/login/'
        headers = {
            'Referer': 'https://chaturbate.com/auth/login/',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            "User-Agent": usAgent
        }
        data = {
            'next': '',
            'csrfmiddlewaretoken': csrf_token,
            'username': username,
            'password': password
        }
        try:
            response = await session.post(url, headers=headers, data=data, impersonate="chrome110", proxies=proxies)
        except Exception as e:
            return {"acc_login": username, "acc_password": password, "type": 'error', "token_balance": "0", "transaction": ""}
        

        print(response)
        
        url = f'https://chaturbate.com/api/ts/tipping/token-stats/?room={username}&currentpage=&max_transaction_id=&cashpage=0'
        try:
            response = await session.get(url, cookies=session.cookies, impersonate="chrome110", proxies=proxies)
        except Exception as e:
            return {"acc_login": username, "acc_password": password, "type": 'error', "token_balance": "0", "transaction": ""}
        
        if response.status_code != 200:
            return {"acc_login": username, "acc_password": password, "type": 'error', "token_balance": "0", "transaction": ""}
        try:
            data = response.json()
            if isinstance(data, dict):
                # print(data)
                pass
            else:
                return {"acc_login": username, "acc_password": password, "type": 'error', "token_balance": "0", "transaction": ""}
        except Exception as e:
            return {}
            
        if not data:
            return {}
     
        # if isinstance(data, dict):
        if 'transactions' in data:
            transactions = data['transactions']
            if transactions:
                token_balance = data['token_balance']
                last_transaction_date = transactions[0]['date']
                return {"acc_login": username, "acc_password": password, "type": 'complete', "token_balance": token_balance, "transaction": last_transaction_date}
            else:
                if 'periods' in data:
                    token_balance = data['token_balance']
                    return {"acc_login": username, "acc_password": password, "type": 'empty', "token_balance": token_balance, "transaction": ""}
                else:
                    return {}
        else:
            if 'periods' in data:
                return {"acc_login": username, "acc_password": password, "type": 'empty', "transaction": ""}
            else:
                return {}
        
        

        # if response.status_code == 200:
        #     return {"acc_login": username, "acc_password": password, 'acc_cookie': session.cookies.get('sessionid')}
        # else:
        #     print(f"Error to login {username}: {response.status_code}")

async def main_checker_func_second(accounts, proxies):
    semaphore = asyncio.Semaphore(70)
    tasks = []
    for account, proxy in zip(accounts, proxies):
        async with semaphore:
            tasks.append(fetch_data_cookies_checker(account, proxy))
        # await asyncio.sleep(1)

    results = await asyncio.gather(*tasks)

    return results    

def sync_main_checker(accounts, proxies):
    # asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    results = [] 
    all_results = asyncio.run(main_checker_func_second(accounts, proxies))

    for result in all_results:
        print(result)
        if result:
            results.append(result)

    return results

@userRouter.post('/make-check')
def create_account_func(acccount_list: List[str] = Body(...), proxies_list: List[str] = Body(...), db: Session = Depends(get_db), current_user: model.UserTable = Depends(get_current_user)):
    if current_user.role == 'admin':
        try:
            checker_results = sync_main_checker(acccount_list, proxies_list)
            print(checker_results)
            print(len(checker_results))
            return checker_results
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error: {e}")
    else: 
        raise HTTPException(status_code=400, detail="Access denied")