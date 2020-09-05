# tauvid

Work in progress.

To scrape, create a file called tau_login.py in the root directory:

```python
creds = ('<tau username>', '<tau password>')
```

then run `scrape_videos.py`.

To render, run `render.py` and then serve the `output` directory as a static site.

### TODO:
handle bad videos
empty categories
uncategorized
login like bid-it
concurrent scraping
don't scrape videos that we already have in our json
