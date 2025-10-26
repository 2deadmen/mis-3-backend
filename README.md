use  uvicorn main:app --reload to run this app 
# Mis-3-Backend

This project uses FastAPI. Follow the steps below to set up a virtual environment and run the server.

## Setup

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Running FastAPI

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

- Replace `main:app` with the correct module and app name if different.
- The server will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Additional

- To deactivate the virtual environment:

  ```bash
  deactivate
  ```
