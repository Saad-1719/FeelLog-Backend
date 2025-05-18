from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(eval(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES")))
DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FERNET_KEY = os.getenv("FERNET_KEY")
EMAIL = os.getenv("EMAIL")
PORT = os.getenv("PORT")
APP_PASSWORD = os.getenv("APP_PASSWORD")
# Check if the environment variables are set
if not SECRET_KEY or not ALGORITHM:
    raise ValueError(
        "SECRET_KEY and ALGORITHM must be set in the environment variables."
    )
