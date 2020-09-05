SHELL := /bin/bash

.PHONY: all

scrape:
	python3 scrape_videos.py videos.json

# profile:
# 	python3 -m cProfile -s tottime scrape_videos.py scrape.json 0104

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

debug: render ./static/ ./templates/
	cd output && python3 -m http.server

deploy:
	cp -R output/. /var/www/tauvid