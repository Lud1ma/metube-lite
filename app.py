import os
import threading
import yt_dlp
from flask import Flask, render_template, request, redirect, url_for

from db import (
    init_db,
    set_download,
    get_all_downloads,
    is_downloaded,
)

app = Flask(__name__)

DOWNLOAD_DIR = "/home/navidrome/music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

init_db()


def yt_search(query, limit=10):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(
            f"ytsearch{limit}:{query}",
            download=False,
        )
        return result["entries"]


import re

def safe_filename(title):
    title = re.sub(r'[\\/*?:"<>|]', "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def download_video(video_id, title):
    url = f"https://www.youtube.com/watch?v={video_id}"
    safe_title = safe_filename(title)

    def progress_hook(d):
        if d["status"] == "downloading":
            set_download(video_id, title, "downloading")
        elif d["status"] == "finished":
            filename = f"{safe_title}.mp3"
            set_download(video_id, title, "done", filename)

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": f"{DOWNLOAD_DIR}/{safe_title}.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
        "progress_hooks": [progress_hook],
    }

    set_download(video_id, title, "downloading")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        query = request.form["query"]
    else:
        query = request.args.get("q")

    results = yt_search(query)
    downloads = get_all_downloads()

    for v in results:
        if v["id"] not in downloads:
            set_download(v["id"], v["title"], "not_started")

    downloads = get_all_downloads()

    return render_template(
        "results.html",
        query=query,
        results=results,
        downloads=downloads,
    )

@app.route("/download/<video_id>")
def download(video_id):
    query = request.args.get("q")

    downloads = get_all_downloads()
    entry = downloads.get(video_id)

    if entry and entry["status"] == "downloading":
        return redirect(url_for("search", q=query))

    if is_downloaded(video_id):
        return redirect(url_for("search", q=query))

    title = entry["title"] if entry else video_id

    t = threading.Thread(
        target=download_video,
        args=(video_id, title),
        daemon=True,
    )
    t.start()

    return redirect(url_for("search", q=query))



if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
