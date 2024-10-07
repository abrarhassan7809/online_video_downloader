from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from downloader import download_video
import uvicorn
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

if not os.path.exists("downloads"):
    os.makedirs("downloads")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/atoms/download/")
async def download_video_api(url: str = Form(...)):
    try:
        file_path = download_video(url)
        return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
