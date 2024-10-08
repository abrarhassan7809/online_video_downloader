from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from chatbot.chat import get_response
from downloader import download_video
import uvicorn
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/atoms/download/")
async def download_video_api(url: str = Form(...)):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return JSONResponse(content={"error": "Invalid URL"}, status_code=400)

    try:
        file_path = download_video(url)
        if 'is not a valid URL' in file_path:
            return JSONResponse(content={"error": "Invalid URL"}, status_code=400)
        return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/predict/")
async def predict(request: Request):
    body = await request.json()
    text = body.get("message")
    response = get_response(text)
    message = {"answer": response}
    return message

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
