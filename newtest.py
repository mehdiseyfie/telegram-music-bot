
import asyncio
import aiohttp
import time
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import ssl


# تنظیمات تست
NUM_USERS = 100000  # تعداد کاربران شبیه‌سازی شده
CONCURRENT_USERS = 1000  # تعداد کاربران همزمان
TEST_DURATION = 300  # مدت زمان تست به ثانیه
BOT_TOKEN = "6495954669:AAEHpP9oviTKnJBWfqVDO7MFgopJ7XSGjR8"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def simulate_user(session, user_id):
    try:
        await session.get(f"{BASE_URL}sendMessage", params={
            "chat_id": user_id,
            "text": "/start"
        })
        
        # شبیه‌سازی جستجوی آهنگ
        await session.get(f"{BASE_URL}answerInlineQuery", params={
            "inline_query_id": f"query_{user_id}",
            "results": '[{"type": "article", "id": "1", "title": "Test Song", "input_message_content": {"message_text": "Test Song"}}]'
        })
        
        # شبیه‌سازی ایجاد پلی‌لیست
        await session.get(f"{BASE_URL}sendMessage", params={
            "chat_id": user_id,
            "text": "Creating playlist..."
        })
    except Exception as e:
        print(f"Error for user {user_id}: {str(e)}")

async def run_user_simulation(start_id, end_id):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = [simulate_user(session, user_id) for user_id in range(start_id, end_id)]
        await asyncio.gather(*tasks)

def process_chunk(start_id, end_id):
    asyncio.run(run_user_simulation(start_id, end_id))

async def main():
    start_time = time.time()
    cpu_count = multiprocessing.cpu_count()
    chunk_size = NUM_USERS // cpu_count
    
    with ProcessPoolExecutor(max_workers=cpu_count) as executor:
        futures = []
        for i in range(0, NUM_USERS, chunk_size):
            futures.append(executor.submit(process_chunk, i, min(i + chunk_size, NUM_USERS)))
        
        for future in futures:
            future.result()
    
    end_time = time.time()
    total_time = end_time - start_time
    requests_per_second = NUM_USERS / total_time
    
    print(f"Test completed in {total_time:.2f} seconds")
    print(f"Processed {NUM_USERS} users")
    print(f"Average requests per second: {requests_per_second:.2f}")

if __name__ == "__main__":
    asyncio.run(main())