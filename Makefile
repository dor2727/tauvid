.PHONY: all

scrape:
	python scrape_videos.py

render:
	python render.py

local: render
	pushd output
	python -m SimpleHTTPServer
	popd