"""FastAPI host that mounts every discovered Gradio app under a single server.

Run locally with:      uvicorn main:app --reload
Run in Docker with:    docker compose up
"""

from __future__ import annotations

import base64
import html
import logging
import os
import resource
from pathlib import Path

import gradio as gr
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from hub import BrokenApp, LoadedApp, discover_apps
from qut001.constants import IMAGE_DIR

def enforce_container_memory_limit():
    # Sets the memory limit to the cgroup (or container) limit to prevent OOM kills
    # and instead return MemoryError.
    cgroup_v2_path = "/sys/fs/cgroup/memory.max"
    limit_bytes = None

    if os.path.exists(cgroup_v2_path):
        with open(cgroup_v2_path, "r") as f:
            val = f.read().strip()
            if val != "max":  # "max" means no specific limit is set
                limit_bytes = int(val)

    if limit_bytes:
        allowed_mem = int(limit_bytes * 0.95) # use 95% of allocated memory
        resource.setrlimit(resource.RLIMIT_AS, (allowed_mem, allowed_mem))
        print(f"Python memory limit locked to cgroup maximum: {allowed_mem // (1024**2)} MB")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("hub.main")

SITE_TITLE = os.getenv("SITE_TITLE", "AI in the Real World")

# QUT logo for the hub hero, embedded as base64 (same trick as apps/llm_demo.py).
# Degrades gracefully: a missing logo leaves a text-only hero instead of
# crashing the whole hub at import time.
_QUT_LOGO_PATH = Path(IMAGE_DIR, "qut.png")
QUT_LOGO_B64 = ""
try:
    QUT_LOGO_B64 = base64.b64encode(_QUT_LOGO_PATH.read_bytes()).decode("ascii")
except OSError:
    logger.warning("QUT logo not found at %s; hero will be text-only.", _QUT_LOGO_PATH)

app = FastAPI(title=SITE_TITLE)

loaded_apps, broken_apps = discover_apps()


def _render_card(item: LoadedApp) -> str:
    description = (
        f'<p class="desc">{html.escape(item.description)}</p>' if item.description else ""
    )
    return f"""
      <a class="card" href="/{html.escape(item.slug)}/">
        <h2>{html.escape(item.title)}</h2>
        {description}
      </a>"""


def _render_broken(item: BrokenApp) -> str:
    detail = (
        f"<pre>{html.escape(item.traceback)}</pre>" if item.traceback else ""
    )
    return f"""
      <details class="broken">
        <summary><strong>apps/{html.escape(item.module)}.py</strong> &mdash; {html.escape(item.error)}</summary>
        {detail}
      </details>"""


def _render_hero() -> str:
    logo = (
        f'<div class="hero-logo-wrap">'
        f'<img src="data:image/png;base64,{QUT_LOGO_B64}" alt="QUT logo">'
        f'</div>'
        if QUT_LOGO_B64
        else ""
    )
    return f"""
    <section class="llm-hero">
      <div class="hero-copy">
        <div class="hero-eyebrow">QUT001 &middot; AI Demos</div>
        <h1>{html.escape(SITE_TITLE)}</h1>
        <p>Interactive demonstrations of AI Models.</p>
      </div>
      {logo}
    </section>"""


def _render_index() -> str:
    if loaded_apps:
        cards = "".join(_render_card(item) for item in loaded_apps)
    else:
        cards = (
            '<p class="empty">No apps found yet. Copy <code>apps/_template.py</code> '
            "to <code>apps/my_demo.py</code> to add the first one.</p>"
        )

    problems = ""
    if broken_apps:
        problems = (
            '<section class="problems"><h3>These apps failed to load</h3>'
            + "".join(_render_broken(item) for item in broken_apps)
            + "</section>"
        )

    hero = _render_hero()

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(SITE_TITLE)}</title>
    <style>
      :root {{
        --qut-blue:#006DAE; --qut-deep:#043B68; --qut-navy:#062D4E; --qut-orange:#F4A024;
        --ink:#18324A; --muted:#5E7185; --line:#D9E4EE; --soft:#F3F7FA;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0 auto; padding: 3rem 1.5rem; max-width: 64rem; line-height: 1.5;
        font-family: Arial, Helvetica, sans-serif; font-synthesis: none;
        color: var(--ink);
        background:
          radial-gradient(circle at 88% -10%, rgba(0,109,174,.13), transparent 32%),
          linear-gradient(180deg, #F7FAFC 0%, #EEF4F8 100%);
      }}
      /* compact QUT hero, same design language as apps/llm_demo.py */
      .llm-hero {{
        min-height: 92px; display: grid;
        grid-template-columns: minmax(0,1fr) 76px;
        align-items: center; gap: 16px; padding: 16px 18px;
        border-radius: 19px; color: #fff;
        background: linear-gradient(125deg, var(--qut-navy), var(--qut-deep) 58%, #075B93);
        border: 1px solid rgba(255,255,255,.18);
        box-shadow: 0 10px 28px rgba(6,45,78,.15); overflow: hidden;
      }}
      .hero-copy {{ min-width: 0; }}
      .hero-eyebrow {{
        font-size: 15px; font-weight: 800; letter-spacing: .11em;
        color: #BFE4FA; margin-bottom: 4px;
      }}
      .llm-hero h1 {{ margin: 0; color: #fff; font-size: 30px; line-height: 1.06; letter-spacing: -.02em; font-weight: 800; }}
      .llm-hero p {{ margin: 6px 0 0; color: #EAF5FC; font-size: 17px; line-height: 1.3; }}
      .hero-logo-wrap {{
        width: 72px; height: 72px; border-radius: 15px; overflow: hidden;
        background: var(--qut-blue);
        box-shadow: 0 7px 20px rgba(0,0,0,.18);
        border: 1px solid rgba(255,255,255,.24);
      }}
      .hero-logo-wrap img {{ width: 100%; height: 100%; display: block; object-fit: contain; }}
      .grid {{
        display: grid; gap: 1rem; margin-top: 1.5rem;
        grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
      }}
      .card {{
        display: block; padding: 1.25rem; border: 1px solid var(--line);
        border-radius: 16px; background: #fff; text-decoration: none; color: var(--ink);
        box-shadow: 0 5px 16px rgba(30,68,102,.06);
        transition: border-color .15s ease, transform .15s ease, box-shadow .15s ease;
      }}
      .card:hover {{ border-color: var(--qut-blue); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(30,68,102,.10); }}
      .card h2 {{ margin: 0 0 .4rem; font-size: 1.1rem; }}
      .desc {{ margin: 0; font-size: .9rem; opacity: .75; }}
      .empty {{
        margin-top: 1.5rem; padding: 1.25rem;
        border: 1px dashed #C8D8E4; border-radius: 13px;
        background: linear-gradient(180deg,#FAFCFD,#F5F8FA); color: #74879A;
      }}
      .problems {{ margin-top: 2.5rem; }}
      .problems h3 {{ margin-bottom: .6rem; color: var(--ink); }}
      .broken {{
        border: 1px solid #F0C39F; border-left: 3px solid #dc2626; border-radius: 12px;
        padding: .6rem .9rem; margin-bottom: .6rem; background: rgba(220,38,38,.07);
      }}
      .broken summary {{ cursor: pointer; font-weight: 700; }}
      pre {{ overflow-x: auto; font-size: .8rem; }}
      @media (max-width: 600px) {{ .llm-hero {{ grid-template-columns: 1fr 64px; }} }}
      .dark {{--body-background-fill: white !important; --body-text-color: black !important; --block-background-fill: white !important;}}
      .dark body {{ background: white !important; color: black !important;}}
    </style>
  </head>
  <body>
    {hero}
    <div class="grid">{cards}
    </div>
    {problems}
  </body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _render_index()


@app.get("/healthz")
def healthz() -> dict:
    """Liveness probe used by the Docker HEALTHCHECK."""
    return {
        "status": "ok",
        "apps_loaded": len(loaded_apps),
        "apps_failed": len(broken_apps),
    }


for item in loaded_apps:
    app = gr.mount_gradio_app(app, item.demo, path=f"/{item.slug}", css=item.css or None)
    logger.info("Mounted %-28s -> /%s", item.title, item.slug)

if broken_apps:
    for item in broken_apps:
        logger.error("Could not load apps/%s.py: %s", item.module, item.error)
