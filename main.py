# main.py
import uvicorn
from webserver import app
from config import SERVER_PORT

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=SERVER_PORT,
        workers=4,  # Adjust based on your CPU cores
        limit_concurrency=1000,  # Limit concurrent connections
    )