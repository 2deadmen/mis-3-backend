from fastapi import FastAPI
from routers import data_handler # Assuming 'routers' is a package/directory

app = FastAPI()

# Include the router from data_handler.py
# The prefix ensures that all routes in data_handler will start with /data
app.include_router(data_handler.router, prefix="/data", tags=["Data Operations"])

@app.get("/")
async def root():
    return {"message": "Hello World from main.py"}
