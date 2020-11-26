#!/usr/bin/env python3
import os, youtube_dl, threading, random, json, subprocess
from flask import Flask, render_template, request, Response

app = Flask(__name__, static_folder="templates/static")

OVERCAST_USERNAME = os.getenv("OVERCAST_USERNAME")
OVERCAST_PASSWORD = os.getenv("OVERCAST_PASSWORD")
DEFAULT_VIDEO_URL = os.getenv("DEFAULT_VIDEO_URL") or ""
env_credentials_supplied = (OVERCAST_USERNAME != None and
                            OVERCAST_PASSWORD != None and
                            len(OVERCAST_USERNAME) > 0 and
                            len(OVERCAST_PASSWORD) > 0)
jobs = {}

class DownloadUploadThread(threading.Thread):
    def __init__(self, video_url, cloudyconfig):
        self.status = "downloading"
        self.cloudyconfig = cloudyconfig
        self.progress = "0%"
        self.error_text = ""
        self.video_url = video_url
        self.mp3_path = ""
        super().__init__()

    def upload(self):
        self.status = "uploading"
        cloudyuploader = subprocess.run([
            "%s/cloudy-uploader" % os.path.dirname(os.path.realpath(__file__)),
            "--no-load-creds",
            "--silent",
            "--login", self.cloudyconfig["username"],
            "--password", self.cloudyconfig["password"],
            self.mp3_path
        ], capture_output=True)
        print(cloudyuploader)
        if (cloudyuploader.returncode != 0):
            self.status = "error"
            self.error_text = "Wrong username or password"
        else:
            self.status = "done"

        os.unlink(self.mp3_path)

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
            if d["status"] == "downloading":
                self.progress = d["_percent_str"]
            if d['status'] == 'finished':
                self.status = "converting"
                self.progress = "100%"
                filename_parts = d["filename"].split(".")
                filename_parts.pop()
                filename_parts.append("mp3")
                self.mp3_path = ".".join(filename_parts)
                print('Done downloading, now converting…' + self.mp3_path)

        ydl_opts = {
            'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio/best ',
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
            try:
                result = ydl.download([self.video_url])
                print(result)
                self.upload()
            except Exception as e:
                self.status = "error"
                self.error_text = "Video not found or not downloadable"
                print(e)


@app.route("/")
def form():
    return render_template("form.html", env_credentials_supplied=env_credentials_supplied, default_video_url=DEFAULT_VIDEO_URL)

@app.route("/api/v1/job", methods=["POST"])
def jobPost():
    use_env_credentials = ("use_env_credentials" in request.form and request.form["use_env_credentials"] == "true" and env_credentials_supplied)
    
    if use_env_credentials:
        username = OVERCAST_USERNAME
        password = OVERCAST_PASSWORD
    else:
        username = request.form["username"] or ""
        password = request.form["password"] or ""

    if (username == "" or password == ""):
        output = {
            "status": "error",
            "error": "Missing or invalid Overcast credentials"
        }
        status = 400
    else:
        cloudyconfig = {
            "username": username,
            "password": password
        }
        video_url = request.form["video_url"]

        job_id = random.randint(0, 10000)
        jobs[job_id] = DownloadUploadThread(video_url, cloudyconfig)
        jobs[job_id].start()
        output = {
            "status": "created",
            "status_id": job_id
        }
        status = 200

    r = Response(response=json.dumps(output), status=status, mimetype="application/json")
    r.headers["Content-Type"] = "application/json; charset=utf-8"

    return r

@app.route('/api/v1/status/<int:job_id>')
def status(job_id):
    if (job_id in jobs):
        output = {
            "status": jobs[job_id].status,
            "progress": jobs[job_id].progress
        }

        if (output["status"] == "error"):
            output["error_text"] = str(jobs[job_id].error_text)
    else:
        output = {
            "status": "error",
            "error_text": "Task not found"
        }

    status = (200 if output["status"] != "error" else 400)

    r = Response(response=json.dumps(output), status=status, mimetype="application/json")
    r.headers["Content-Type"] = "application/json; charset=utf-8"
    return r

if __name__ == "__main__":
    app.run(debug=("DEBUG" in os.environ))
