# tauvid

To scrape, create a file called tau_login.py in the root directory:

```python
creds = ('<tau username>', '<tau password>')
```

then run `make scrape`.

Run `make validate` to check that all scraped videos exist and have valid thumbnails.

To render, run `make render` and then serve the `output` directory as a static site.

### TODO:

- volume boost above 100%
- move to https://oauth2-proxy.github.io/oauth2-proxy/configuration
- "my courses" in cookies