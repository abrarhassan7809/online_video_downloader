#main.py
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from chatbot.chat import get_response
from downloader import youtube_download_video, instagram_download_video, youtube_download_audio
import uvicorn
import os
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

YOUTUBE_REGEX = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')
INSTAGRAM_REGEX = re.compile(r'(https?://)?(www\.)?instagram\.com/.+')

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/atoms/download/{type}")
async def download(type: str, url: str = Form(...), format_id: str = Form(...)):
    url = url.strip()
    print(type, url, format_id)
    if not url.startswith(("http://", "https://")):
        return JSONResponse(content={"error": "Invalid URL"}, status_code=400)

    if type == "video":
        if YOUTUBE_REGEX.match(url):
            try:
                file_path = await youtube_download_video(url, format_id)
                return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)

    elif type == "audio":
        if YOUTUBE_REGEX.match(url):
            try:
                file_path = await youtube_download_audio(url, format_id)
                return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)

    elif INSTAGRAM_REGEX.match(url) and type == "video":
        try:
            file_path = instagram_download_video(url)
            if 'No media found' in file_path:
                return JSONResponse(content={"error": "No media found"}, status_code=400)
            return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)

    return JSONResponse(content={"error": "Unsupported URL or type"}, status_code=400)

@app.post("/predict/")
async def predict(request: Request):
    body = await request.json()
    text = body.get("message")
    response = get_response(text)
    message = {"answer": response}
    return message

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
