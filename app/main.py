#!/usr/bin/env python3
import os, youtube_dl, threading, random, json
from flask import Flask, render_template, request, Response

app = Flask(__name__)

OVERCAST_USERNAME = os.getenv("OVERCAST_USERNAME")
OVERCAST_PASSWORD = os.getenv("OVERCAST_PASSWORD")

class ExportingThread(threading.Thread):
    def __init__(self, video_url):
        self.status = "downloading"
        self.video_url = video_url
        super().__init__()

    def run(self):
        class MyLogger(object):
            def debug(self, msg):
                print(msg)
                pass

            def warning(self, msg):
                print(msg)
                pass

            def error(self, msg):
                print(msg)


        def my_hook(d):
            print(d)
            if d['status'] == 'finished':
                self.status = "converting"
                print('Done downloading, now converting ...')

        ydl_opts = {
            'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'logger': MyLogger(),
            'progress_hooks': [my_hook],
            'playlistend': 2,
            "restrictfilenames": True,
            "outtmpl": "%(upload_date)s_%(title)s.%(ext)s"
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([self.video_url])
            self.status = "done"
            print(result)


exporting_threads = {}

@app.route("/")
def form():
    env_credentials_supplied = (len(OVERCAST_USERNAME) > 0 and len(OVERCAST_PASSWORD) > 0)
    return render_template("form.html", env_credentials_supplied=env_credentials_supplied)

@app.route("/submit", methods=["GET", "POST"])
def handleSubmit():
    if request.method == 'POST':
        use_env_credentials = ("use_env_credentials" in request.form and request.form["use_env_credentials"] == "true")
        username = request.form["username"]
        password = request.form["password"]
        video_url = request.form["video_url"]

        global exporting_threads

        thread_id = random.randint(0, 10000)
        exporting_threads[thread_id] = ExportingThread(video_url)
        exporting_threads[thread_id].start()

        r = Response(response=json.dumps({"progress_id": thread_id}), status=200, mimetype="application/json")
        r.headers["Content-Type"] = "application/json; charset=utf-8"

        return r
    else:
        return form()

@app.route('/progress/<int:thread_id>')
def progress(thread_id):
    global exporting_threads

    return str(exporting_threads[thread_id].status)

if __name__ == "__main__":
    app.run(debug=("DEBUG" in os.environ))
