import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

load_dotenv()

# استفاده از quote_plus برای کدگذاری صحیح رمز عبور
DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD'))

DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{DB_PASSWORD}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

print(f"Database URL: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print("Connected successfully!")
except Exception as e:
    print(f"Connection failed: {e}")