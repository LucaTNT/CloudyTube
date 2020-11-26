This simple web app allows you to submit the URL of a video (from any of the websites supported by [youtube-dl](https://youtube-dl.org/)): the video will be downloaded, its audio will be extracted, converted to mp3 and uploaded to your own [Overcast® player](https://overcast.fm/). This requires an Overcast® Premium membership.

Let me just make one thing clear: design was not a priority when building this tool, it was mostly for my own use (and it shows).

## Demo installation
You can use my demo install at [cloudytube.lucatnt.com](https://cloudytube.lucatnt.com/).

## How to use this thing
You can either run this with Python (it requires Flask, so `pip3 install flask`)

	python3 main.py

Or you can use the `lucatnt/cloudytube` Docker image

	docker run -p 5000:80 lucatnt/als2cue_web

Either way you will end up with a webserver running on port 5000.