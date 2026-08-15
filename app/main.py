#!/usr/bin/env python3
import os, shutil, yt_dlp, threading, uuid, time, json, subprocess, traceback
from flask import Flask, render_template, request, Response

app = Flask(__name__, static_folder="templates/static")

OVERCAST_USERNAME = os.getenv("OVERCAST_USERNAME")
OVERCAST_PASSWORD = os.getenv("OVERCAST_PASSWORD")
ENV_CREDENTIALS_DEFAULT = ("checked" if os.getenv("ENV_CREDENTIALS_DEFAULT") == "true" else "")
DEFAULT_VIDEO_URL = os.getenv("DEFAULT_VIDEO_URL") or ""
env_credentials_supplied = (OVERCAST_USERNAME != None and
                            OVERCAST_PASSWORD != None and
                            len(OVERCAST_USERNAME) > 0 and
                            len(OVERCAST_PASSWORD) > 0)
jobs = {}
JOB_RETENTION_SECONDS = 3600

def prune_finished_jobs():
    now = time.time()
    stale_ids = [job_id for job_id, job in jobs.items()
                 if job.status in ("done", "error") and (now - job.created_at) > JOB_RETENTION_SECONDS]
    for job_id in stale_ids:
        del jobs[job_id]

class DownloadUploadThread(threading.Thread):
    def __init__(self, video_url, cloudyconfig):
        self.status = "downloading"
        self.cloudyconfig = cloudyconfig
        self.progress = "0%"
        self.error_text = ""
        self.video_url = video_url
        self.mp3_path = ""
        self.created_at = time.time()
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
        print("cloudy-uploader exited with code %d" % cloudyuploader.returncode)
        if cloudyuploader.stdout:
            print(cloudyuploader.stdout.decode(errors="replace"))
        if cloudyuploader.stderr:
            print(cloudyuploader.stderr.decode(errors="replace"))
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

            def warning(self, msg):
                print(msg)

            def error(self, msg):
                print(msg)


        def my_hook(d):
            if d["status"] == "downloading":
                self.progress = d["_percent_str"]
            if d['status'] == 'finished':
                self.status = "converting"
                self.progress = "100%"
                self.mp3_path = os.path.splitext(d["filename"])[0] + ".mp3"
                print('Done downloading, now converting…' + self.mp3_path)

        nodejs_path = shutil.which('nodejs') or shutil.which('node')
        js_runtime_config = {}
        if nodejs_path:
            js_runtime_config['nodejs'] = {'executable': nodejs_path}

        ydl_opts = {
            'format': 'bestaudio[ext=mp3]/bestaudio[ext=m4a]/bestaudio/best ',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'logger': MyLogger(),
            'progress_hooks': [my_hook],
            'color': 'never',
            'playlistend': 2,
            "restrictfilenames": True,
            "outtmpl": "%(upload_date)s_%(title)s.%(ext)s",
            'js_runtimes': js_runtime_config
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.download([self.video_url])
                print(result)
                self.upload()
            except Exception as e:
                self.status = "error"
                self.error_text = "Video not found or not downloadable"
                print(traceback.format_exc())


@app.route("/")
def form():
    return render_template("form.html", env_credentials_supplied=env_credentials_supplied, env_credentials_default=ENV_CREDENTIALS_DEFAULT, default_video_url=DEFAULT_VIDEO_URL)

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

        prune_finished_jobs()
        job_id = uuid.uuid4().hex
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

@app.route('/api/v1/status/<job_id>')
def job_status(job_id):
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
    app.run(host='0.0.0.0', debug=(os.getenv("DEBUG", "").lower() == "true"))
