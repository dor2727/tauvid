SHELL := /bin/bash

.PHONY: all

scrape:
	python3 scrape_videos.py videos.json

validate: videos.json
	python3 validate.py videos.json cache.json

render: videos.json
	rm -rf output
	mkdir output
	python3 render.py videos.json
	cp -R static/. output

all: 
	make scrape
	make validate
	make render

debug:
	python3 scrape_videos.py debug.json 0104
	python3 validate.py debug.json debug_cache.json
	rm -rf output
	mkdir output
	python3 render.py debug.json
	cp -R static/. output
	cd output && python3 -m http.server

deploy:
	rm -rf /var/www/tauvid/*
	cp -R output/. /var/www/tauvid