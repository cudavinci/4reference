# Site

[Home Page](https://cudavinci.github.io/4reference/)

[Code Snippets](https://cudavinci.github.io/4reference/snippets/)

[WebDev Snippets](https://cudavinci.github.io/4reference/webdev_snippets/)

## Dev stuff

### Local preview
```bash
mkdocs serve
```
Then open: http://127.0.0.1:8000

### Build static site
```bash
mkdocs build
```

### Deploy to GitHub Pages
```bash
mkdocs gh-deploy --force
```

This:
- builds the site
- pushes to the `gh-pages` branch
- publishes to: https://cudavinci.github.io/4reference/

alohamora

### venv

pyenv local 3.12.13
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r base_requirements.txt