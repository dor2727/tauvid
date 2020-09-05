SHELL := /bin/bash

.PHONY: all

scrape:
	python3 scrape_videos.py videos.json

validate: videos.json
	python3 validate.py videos.json cache.json

render: assets videos.json
	rm -rf output
	mkdir output
	python3 render.py videos.json
	cp -R static/. output

assets:
	curl "https://unpkg.com/purecss@2.0.3/build/pure-min.css" -o "static/css/pure-min.css"
	curl "https://unpkg.com/purecss@2.0.3/build/grids-responsive-min.css" -o "static/css/grids-responsive-min.css"
	curl "fonts.googleapis.com/earlyaccess/opensanshebrew.css" -o "static/css/opensanshebrew.css"
	curl "stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" -o "static/css/font-awesome.min.css"

	curl "https://cdn.jsdelivr.net/npm/hls.js@latest" -o "static/js/hls.js"

	cat static/css/*.css > static/style.css
	cat static/js/*.js > static/script.js

all: 
	make scrape
	make validate
	make render

debug: render ./static/ ./templates/
	cd output && python3 -m http.server

deploy:
	rm -rf /var/www/tauvid/*
	cp -R output/. /var/www/tauvid