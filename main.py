import uvicorn
from dotenv import load_dotenv
from SRC.api.app import create_app
from SRC.core.config import config

load_dotenv()

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info",
    )