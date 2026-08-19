import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", 0))