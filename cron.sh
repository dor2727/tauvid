#!/bin/sh
cd ~/tauvid
make scrape
make validate
make render
make deploy
