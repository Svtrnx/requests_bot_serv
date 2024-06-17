import json
import asyncio
import aiohttp
import uuid
import time
import base64
from fake_useragent import UserAgent
import random
import string
import datetime
import httpx

def extract_cookies(cookie_list):
    cookies = {}
    for cookie in cookie_list:
        cookies[cookie['name']] = cookie['value']
    return cookies

def generate_newrelic_header():
    # Sample data structure for the newrelic header
    newrelic_data = {
        "v": [0, 1],
        "d": {
            "ty": "Browser",
            "ac": "1418997",  # Your account ID
            "ap": "24506750",  # Your application ID
            "id": uuid.uuid4().hex[:16],
            "tr": uuid.uuid4().hex[:16],
            "ti": int(time.time() * 1000)
        }
    }
    
    # Convert to JSON string
    newrelic_json = json.dumps(newrelic_data)
    
    # Encode JSON string in base64
    newrelic_base64 = base64.b64encode(newrelic_json.encode()).decode()
    
    return newrelic_base64

# Example usage
newrelic_header = generate_newrelic_header()

def generate_traceparent():
    version = "00"
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    trace_flags = "01"
    return f"{version}-{trace_id}-{span_id}-{trace_flags}"

def generate_accept_language():
    languages = [
        "ru-RU",        # Russian (Russia)
        "ru;q=0.9",     # Russian (generic), with lower preference
        "en-US;q=0.8",  # English (United States), with lower preference
        "en;q=0.7"      # English (generic), with lowest preference
    ]
    
    # Shuffle the list of languages to simulate different preferences
    random.shuffle(languages)
    
    # Join the shuffled languages list into a single string
    accept_language = ", ".join(languages)
    
    return accept_language

# Generate accept-language header
accept_language = generate_accept_language()

def generate_presence_id(length=10):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choices(characters, k=length))

presence_id = generate_presence_id()
# Function to generate tracestate header
def generate_tracestate():
    account_id = "1418997"
    app_id = "24506750"
    span_id = uuid.uuid4().hex[:16]
    timestamp = int(time.time() * 1000)
    return f"{account_id}@nr=0-1-{account_id}-{app_id}-{span_id}----{timestamp}"

# Function to generate x-newrelic-id header
def generate_x_newrelic_id():
    return "VQIGWV9aDxACUFNVDgMEUw=="

# Create a UserAgent instance
ua = UserAgent()
user_agent = ua.random

# Function to parse User-Agent string and generate sec-ch-ua headers
def generate_sec_ch_ua_headers(user_agent):
    # Simple example, you might need to expand this based on different user agents
    if "Chrome" in user_agent:
        browser_version = user_agent.split("Chrome/")[1].split(" ")[0]
        sec_ch_ua = f"\"Google Chrome\";v=\"{browser_version.split('.')[0]}\", \"Chromium\";v=\"{browser_version.split('.')[0]}\", \"Not.A/Brand\";v=\"24\""
        sec_ch_ua_mobile = "?0"
        sec_ch_ua_platform = "\"Windows\"" if "Windows" in user_agent else "\"Unknown\""
    else:
        sec_ch_ua = "\"Not.A/Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\""
        sec_ch_ua_mobile = "?0"
        sec_ch_ua_platform = "\"Unknown\""
    
    return sec_ch_ua, sec_ch_ua_mobile, sec_ch_ua_platform

sec_ch_ua, sec_ch_ua_mobile, sec_ch_ua_platform = generate_sec_ch_ua_headers(user_agent)

async def fetch_data(session, url, headers, cookies, proxy_url, get_cancel_flag, bot_work_time_minutes, model_id):
    while True:
        
        if datetime.datetime.now() >= bot_work_time_minutes:
            break
        if get_cancel_flag():
            break
        try:
            async with session.get(url, headers=headers, cookies=cookies, proxy=f"socks5://{proxy_url}") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"{url}:")
                    # print(data)
                else:
                    # print(f"Error: {response.status} for URL: {url}")
                    pass
            
        except Exception as e:
            print(f"Exception occurred", url, e)
        if url == f"https://chaturbate.com/push_service/room_user_count/{model_id}/?presence_id={presence_id}":
            for i in range(11):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
                await asyncio.sleep(5)
            await asyncio.sleep(5)
        if url == f"https://chaturbate.com/api/panel_context/{model_id}/":
            for i in range(1):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
                await asyncio.sleep(5)
            await asyncio.sleep(5)
        if url == f"https://chaturbate.com/notifications/updates/?notification_type=twitter_feed&notification_type=offline_tip":
            for i in range(29):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
                await asyncio.sleep(5)
            await asyncio.sleep(5)
        if url == f"https://chaturbate.com/photo_videos/api/pvcontext/{model_id}/":
            for i in range(15):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
                await asyncio.sleep(5)
            await asyncio.sleep(5)
        if url == f"https://chaturbate.com/api/more_like/{model_id}/":
            for i in range(17):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
                await asyncio.sleep(5)
            await asyncio.sleep(5)
        if url == f"https://chaturbate.com/api/ts/games/current/room/{model_id}":
            for i in range(8):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
                await asyncio.sleep(5)
            await asyncio.sleep(7)
        if url == f"https://chaturbate.com/api/biocontext/{model_id}/?":
            for i in range(5):
                if datetime.datetime.now() >= bot_work_time_minutes:
                    break
                if get_cancel_flag():
                    break
            await asyncio.sleep(7)


async def make_request(credentials, proxy_url, bot_work_time_minutes, scheduled_task, model_id):
    current_time = datetime.datetime.now()
    time_until_bot_work = bot_work_time_minutes - current_time
    seconds_until_bot_work = time_until_bot_work.total_seconds()
    def get_cancel_flag():
        return scheduled_task.cancel_flag.is_set()
    ua = UserAgent()
    headers = {
        "accept": "*/*",
        "accept-language": accept_language,
        "newrelic": newrelic_header,
        "priority": "u=1, i",
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": sec_ch_ua_mobile,
        "sec-ch-ua-platform": sec_ch_ua_platform,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "traceparent": generate_traceparent(),
        "tracestate": generate_tracestate(),
        "x-newrelic-id": generate_x_newrelic_id(),
        "x-requested-with": "XMLHttpRequest",
        "Referer": "https://chaturbate.com",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "User-Agent": ua.random
    }

    cookies = {cookie['name']: cookie['value'] for cookie in credentials['cookies_trnsl']}
    
    urls_and_intervals = [
        (f"https://chaturbate.com/push_service/room_user_count/{model_id}/?presence_id={presence_id}"),
        (f"https://chaturbate.com/api/panel_context/{model_id}/"),
        (f"https://chaturbate.com/notifications/updates/?notification_type=twitter_feed&notification_type=offline_tip"),
        (f"https://chaturbate.com/photo_videos/api/pvcontext/{model_id}/"),
        (f"https://chaturbate.com/api/more_like/{model_id}/"),
        (f"https://chaturbate.com/api/ts/games/current/room/{model_id}"),
        (f"https://chaturbate.com/api/biocontext/{model_id}/?")
    ]
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_data(session, url, headers, cookies, proxy_url, get_cancel_flag, bot_work_time_minutes, model_id)
                for url in urls_and_intervals 
            ]

            await asyncio.gather(*tasks)
    
    except asyncio.TimeoutError:
        print(f"Task timed out after {bot_work_time_minutes} minutes")
    
    except asyncio.CancelledError:
            print("Coroutine was cancelled.")
    except Exception as e:
        print(f"Exception occurred: {e}")

async def main():
    try:
        with open('reserv.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("File not found")
        return []

    return data