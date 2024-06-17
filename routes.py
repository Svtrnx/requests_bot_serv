from fastapi import Depends, APIRouter, BackgroundTasks, HTTPException
import asyncio
from invoke_requests import main, make_request
import json
import datetime
from pydantic import BaseModel
import random
import string
userRouter = APIRouter()

scheduled_tasks = {}

class ScheduleTaskRequest(BaseModel):
    delay: int
    bot_work_time: int
    model_id: str
    num_tasks: int
    cool_down_tasks: int
    
class ScheduledTask:
    def __init__(self, task_id):
        self.task_id = task_id
        self.cancel_flag = asyncio.Event()

def generate_random_id(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length))

async def read_proxies_from_file(filename):
    proxies = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                proxies.append(line.strip())
    except FileNotFoundError:
        print(f"Файл {filename} не найден.")
    return proxies


#############################################################################
async def perform_custom_task(task_id, delay, bot_work_time, scheduled_task, model_id, num_tasks, cool_down_tasks):
    try:
        await asyncio.sleep(delay)
        info = await get_task_status(task_id=task_id)
        print(info)
        if info['status'] == 'scheduled':
            current_time = datetime.datetime.now()
            bot_work_time_minutes = current_time + datetime.timedelta(minutes=bot_work_time)

            data = [
                    {
                        "username_trnsl": "Remi1785",
                        "password_trnsl": "9GGHCSzTgVMAfw9",
                        "cookies_trnsl": [
                        {
                            "name": "sessionid",
                            "value": "ywu886dmzet6nlhncww552ycjp4q70ub",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": -1,
                            "size": 41,
                            "httpOnly": True,
                            "secure": True,
                            "session": True,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "csrftoken",
                            "value": "CVZs1gTgCDscCQzm0JY4r5UQVMQAbDBkKEClyo4KvYnsUIFAXGiTqNryYBXQGBOW",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1749892787.458345,
                            "size": 73,
                            "httpOnly": False,
                            "secure": True,
                            "session": False,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "_ga_GX0FLQH21P",
                            "value": "GS1.1.1718443183.1.0.1718443187.0.0.0",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1753003187.467447,
                            "size": 51,
                            "httpOnly": False,
                            "secure": False,
                            "session": False,
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "cf_clearance",
                            "value": "z3VhZ6LBI0iTITZz4ZaII3ygTzVujEHuEbUbFeoTZVs-1718443185-1.0.1.1-UHpqyfa4rRzdTzxafGwwVGuYbtLLyhFDNkPDThid0H.x8OC9hRelnkjv4EHUqB5l6XgoTegsL2kOgSIvqGWisw",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1749979183.896999,
                            "size": 161,
                            "httpOnly": True,
                            "secure": True,
                            "session": False,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure",
                            "partitionKey": {
                            "topLevelSite": "https://chaturbate.com",
                            "hasCrossSiteAncestor": False
                            }
                        },
                        {
                            "name": "__cf_bm",
                            "value": "dHUf5lUA4v.0i7huUBDoIdNqhU2ucMq1S61iXZXjABY-1718443189-1.0.1.1-jUQH1zd2fjYldHdMTMdCEKySHFhrGcgPWwOYdXnazvw.cVYJgdOJTSqSudutN4HyzhtnIV3St5Lu0RgIav5Ctg",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1718444987.458454,
                            "size": 156,
                            "httpOnly": True,
                            "secure": True,
                            "session": False,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "_ga",
                            "value": "GA1.1.322658472.1718443183",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1753003183.316805,
                            "size": 29,
                            "httpOnly": False,
                            "secure": False,
                            "session": False,
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "__utfpp",
                            "value": "f:trnxbc2dd803b41dfc5b31b159677e4475d6:1sIPZb:t1pZwln5b6KOThnoTYZ9RA5ZzodLEuLK1t7mX_ZRpZk",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1753003185.045099,
                            "size": 96,
                            "httpOnly": False,
                            "secure": True,
                            "session": False,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "sbr",
                            "value": "sec:sbre0ed061d-47b9-425e-b4d9-fd840f5b92af:1sIPZX:Di6_Az_xc141mWUT5dkN2F7gv57Fko3JJhtMteKkntk",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1753003181.268763,
                            "size": 97,
                            "httpOnly": True,
                            "secure": True,
                            "session": False,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        },
                        {
                            "name": "affkey",
                            "value": "eJyrVipSslJQUtJRUEoBMYwMjEx0Dcx0DU2VagFVGwXN",
                            "domain": ".chaturbate.com",
                            "path": "/",
                            "expires": 1721035181.26873,
                            "size": 50,
                            "httpOnly": False,
                            "secure": True,
                            "session": False,
                            "sameSite": "None",
                            "priority": "Medium",
                            "sameParty": False,
                            "sourceScheme": "Secure"
                        }
                        ]
                    }
                    ]

            print("Total accounts: ", len(data))

            credentials_data = await main()
            print("Total credentials: ", credentials_data)
            if not credentials_data:
                return

            cool_down = cool_down_tasks
            num_tasks_ = num_tasks

            proxies = await read_proxies_from_file('proxy.txt')
            if not proxies:
                print("Не удалось загрузить прокси из файла.")
                return

            tasks = []
            for i in range(num_tasks_):
                proxy = proxies[i % len(proxies)]
                task = asyncio.create_task(make_request(credentials_data[i], proxy, bot_work_time_minutes, scheduled_task, model_id))
                tasks.append(task)
                await asyncio.sleep(cool_down)
                if scheduled_task.cancel_flag.is_set() or datetime.datetime.now() >= bot_work_time_minutes:
                    print(f"Задача {task_id} отменена")
                    break

            await asyncio.gather(*tasks)
        print(f"Выполнение задачи {task_id} завершено")
        info_cancel = await cancel_task(task_id)
        print(info_cancel)
    except Exception as e:
        print(f"Ошибка в задаче {task_id}: {e}")


@userRouter.get("/tasks")
async def get_active_tasks():
    active_tasks = []
    for task_id, scheduled_task in scheduled_tasks.items():
        if not scheduled_task.cancel_flag.is_set():
            active_tasks.append({
                "task_id": task_id,
                "status": "scheduled"
            })
    return active_tasks

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
async def schedule_task(request: ScheduleTaskRequest, background_tasks: BackgroundTasks):
    # task_id = len(scheduled_tasks) + 1
    task_id = generate_random_id()
    scheduled_task = ScheduledTask(task_id)
    scheduled_tasks[task_id] = scheduled_task
    background_tasks.add_task(perform_custom_task, task_id, request.delay, request.bot_work_time, scheduled_task, request.model_id, request.num_tasks, request.cool_down_tasks)
    print(f"Задача {task_id} запланирована на выполнение через {request.delay} секунд")
    return {"task_id": task_id}

@userRouter.delete("/cancel-task/{task_id}")
async def cancel_task(task_id: str):
    if task_id in scheduled_tasks:
        scheduled_task = scheduled_tasks[task_id]
        scheduled_task.cancel_flag.set()
        return {"message": f"Задача {task_id} отменена успешно"}
    else:
        return {"error": "Задача с таким ID не найдена"}