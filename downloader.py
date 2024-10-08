import yt_dlp
from fastapi import HTTPException
import os


def download_video(url: str, output_path: str = "downloads") -> str:
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
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
