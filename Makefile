SHELL := /bin/bash

.PHONY: all

scrape:
	python3 scrape_videos.py

render:
	python3 render.py

local: render ./static/ ./templates/
	cp -R static/. output
	cd output && python3 -m http.server