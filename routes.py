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

            # Здесь продолжается выполнение вашей логики
            try:
                with open('./reserv.json', 'r') as file:
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