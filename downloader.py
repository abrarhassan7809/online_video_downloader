#downloader.py
import uuid
import instaloader
import yt_dlp
from fastapi import HTTPException
import os
import re
import requests

session_id = "192799e78e3-7b14fe"

def sanitize_filename(filename):
    return re.sub(r'[\\/:"*?<>|]+', "_", filename)

async def youtube_download_audio(url: str, quality: str, output_path: str = "downloads"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if quality not in ["128", "320"]:
        raise HTTPException(status_code=400, detail="Invalid quality value.")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality
        }],
        'postprocessor_args': ['-af', 'aresample=48000'],
        'noplaylist': True,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            sanitized_title = sanitize_filename(info['title'])
            file_path = os.path.join(output_path, f"{sanitized_title}.mp3")

            if not os.path.exists(file_path):
                raise RuntimeError(f"Audio file {file_path} does not exist.")

            return file_path
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def youtube_download_video(url: str, quality: str, output_path: str = "downloads"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': f'bestvideo[height<={int(quality)}]+bestaudio/best[height<={int(quality)}]',
        # 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{output_path}/%(title)s.mp4',
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        return file_path

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL or download error: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def instagram_download_video(url: str, output_path: str = "downloads"):
    loader = instaloader.Instaloader()
    post = instaloader.Post.from_shortcode(loader.context, url.split("/")[-2])
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    loader.download_post(post, output_path)
    for file in os.listdir(output_path):
        if file.endswith(".mp4"):
            return os.path.join(output_path, file)
    return "No media found"
