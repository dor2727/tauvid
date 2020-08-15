SHELL := /bin/bash

.PHONY: all

scrape:
	python3 scrape_videos.py

render: videos2.json
	python3 render.py videos2.json

local: render ./static/ ./templates/
	rm -rf output
	mkdir output
	cp -R static/. output
	cd output && python3 -m http.server