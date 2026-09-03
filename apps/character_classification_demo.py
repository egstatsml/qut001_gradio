"""QUT001 interactive character-classification demo."""

from __future__ import annotations

import argparse
import base64
import html
import os
from pathlib import Path
from functools import lru_cache
from io import BytesIO
from typing import Any

import gradio as gr
import numpy as np
import torch
from PIL import Image, ImageOps

from qut001.character_classification_model import (
    CLASS_NAMES,
    INPUT_MEAN,
    INPUT_STD,
    load_model,
)

from qut001.constants import IMAGE_DIR

CANVAS_SIZE = 380
PREVIEW_SIZE = 132

# Visual assets are loaded from data/images/ at startup. The QUT image is the
# official logo image supplied for this demo.

QUT_LOGO_PATH = Path(os.path.join(IMAGE_DIR, "qut.png"))
QUT_LOGO_B64 = base64.b64encode(QUT_LOGO_PATH.read_bytes()).decode("ascii")
BACKGROUND_TEXTURE_PATH = Path(os.path.join(IMAGE_DIR, "background_texture.png"))
BACKGROUND_TEXTURE_B64 = base64.b64encode(BACKGROUND_TEXTURE_PATH.read_bytes()).decode("ascii")

APP_CSS = r"""
:root {
  --qut-blue:#00467f;
  --qut-blue-2:#0a5c9e;
  --ink:#0e1726;
  --muted:#667085;
  --line:#dbe3ed;
  --paper:#ffffff;
  --shadow:0 18px 44px rgba(13,34,61,.14);
}

html,body {
  min-height:100%;
  background-color:#e9eef4;
  background-image:
    url("__BACKGROUND_TEXTURE_URL__"),
    radial-gradient(circle at 15% 0%,#f8fbff 0,#edf2f7 38%,#e5ebf1 100%);
  background-repeat:repeat, no-repeat;
  background-size:800px 520px, cover;
  background-attachment:scroll, scroll;
}

.gradio-container {
  max-width:1480px!important;
  padding:12px 20px 18px!important;
  position:relative;
  z-index:1;
  font-family:Arial,Helvetica,sans-serif!important;
}

footer {display:none!important;}

.hero {
  position:relative;
  overflow:hidden;
  min-height:154px;
  display:grid;
  grid-template-columns:1fr 126px;
  align-items:center;
  gap:18px;
  padding:18px 22px 17px;
  border-radius:26px;
  background:linear-gradient(125deg,#063866 0%,#00467f 58%,#0c5d9f 100%);
  border:1px solid rgba(255,255,255,.22);
  box-shadow:0 22px 55px rgba(0,50,92,.25);
}

.hero:before,.hero:after{
  content:"";
  position:absolute;
  border-radius:50%;
  background:rgba(255,255,255,.06);
  pointer-events:none;
}
.hero:before{width:250px;height:250px;right:30px;top:-170px}
.hero:after{width:190px;height:190px;left:-80px;bottom:-130px}

.title-art {
  display:flex;
  flex-direction:column;
  align-items:flex-start;
  gap:5px;
  position:relative;
  z-index:2;
}

.title-line {
  margin:0;
  font-size:44px;
  line-height:1.15;
  font-weight:800;
  letter-spacing:1.5px;
  color:#ffffff;
  white-space:nowrap;
  text-shadow:0 2px 10px rgba(0,20,40,.35);
}

.qut-logo-frame {
  position:relative;
  z-index:2;
  width:118px;
  height:72px;
  overflow:hidden;
  border-radius:11px;
  background:#00467f;
  border:1px solid rgba(255,255,255,.34);
  box-shadow:0 8px 18px rgba(0,0,0,.16);
  justify-self:end;
}
.qut-logo-frame img {
  position:absolute;
  width:118px;
  height:118px;
  left:0;
  top:0;
  object-fit:cover;
  object-position:top center;
}

.tagline {
  margin:11px auto 14px;
  text-align:center;
  font-size:23px;
  line-height:1.3;
  font-weight:700;
  letter-spacing:.005em;
  color:#17233a;
  text-shadow:0 1px 0 rgba(255,255,255,.9);
}

.pipeline-row {align-items:stretch!important}

.stage-card {
  position:relative;
  min-height:560px;
  padding:13px!important;
  border-radius:24px!important;
  background:rgba(255,255,255,.96)!important;
  border:1px solid rgba(255,255,255,.90)!important;
  box-shadow:var(--shadow);
  overflow:hidden;
}

.stage-card:before {
  content:"";
  position:absolute;
  inset:0 0 auto 0;
  height:5px;
  background:linear-gradient(90deg,#081a2f,#00467f,#1b78bc);
}

.stage-heading {
  display:flex;
  align-items:center;
  gap:9px;
  height:42px;
  margin-bottom:12px;
  color:#101b2e;
  font-size:19px;
  font-weight:900;
  letter-spacing:.01em;
}
.stage-heading .num {
  width:31px;height:31px;
  border-radius:9px;
  display:grid;
  place-items:center;
  background:#0e1726;
  color:#fff;
  font-size:17px;
  box-shadow:0 5px 12px rgba(14,23,38,.16);
}

.arrow-column {
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  min-width:52px!important;
}
.arrow-wrap {
  width:100%;
  min-height:560px;
  display:flex;
  align-items:center;
  justify-content:center;
}
.arrow {
  width:52px;height:52px;
  border-radius:50%;
  display:grid;
  place-items:center;
  background:#0e1726;
  color:#fff;
  font-size:27px;
  font-weight:900;
  box-shadow:0 10px 24px rgba(14,23,38,.20);
}

.native-canvas-shell {
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:6px;
}

.input-work-area{align-items:flex-start!important;gap:12px!important;flex-wrap:nowrap!important}
.input-work-area > .gradio-column{min-width:0!important}
.input-draw-col{min-width:410px!important}
.input-preview-col{min-width:180px!important}
.canvas-toolbar {
  width:380px;
  max-width:100%;
  min-height:44px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:7px 9px;
  border-radius:13px;
  background:#f1f4f8;
  border:1px solid #dce4ee;
}
.palette{display:flex;align-items:center;gap:6px}
.palette-btn{
  width:27px;height:27px;
  border-radius:50%;
  border:2px solid rgba(14,23,38,.20);
  padding:0;
  cursor:pointer;
  box-shadow:0 2px 5px rgba(0,0,0,.10);
}
.palette-btn.active{outline:3px solid rgba(0,70,127,.23);outline-offset:2px}
.canvas-tool-group{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:800;color:#4f5e73}
.canvas-tool-group input[type=range]{width:86px}
.eraser-toggle{
  border:1px solid #cfd8e4;background:#fff;color:#28364b;
  border-radius:999px;padding:6px 10px;font-size:12px;font-weight:800;cursor:pointer
}
.eraser-toggle.active{background:#0e1726;color:#fff;border-color:#0e1726}

#drawing-canvas {
  display:block;
  width:380px;
  height:380px;
  max-width:100%;
  background:#000;
  border-radius:15px;
  cursor:crosshair;
  touch-action:none;
  box-shadow:0 10px 24px rgba(6,28,52,.18), inset 0 0 0 1px rgba(255,255,255,.10);
}

.button-row{margin:4px auto 0;max-width:380px;width:100%}
.button-row button{
  min-height:50px!important;
  font-family:Arial,Helvetica,sans-serif!important;
  font-size:17px!important;
  font-weight:900!important;
  border-radius:12px!important;
}

.processed-placeholder {
  max-width:none;
  width:100%;
  margin:0;
  min-height:208px;
  border:1px dashed #c8d3e0;
  border-radius:14px;
  display:grid;
  place-items:center;
  color:#78869a;
  font-size:14px;
  font-weight:800;
  background:#f8fafc;
}

.processed-panel {
  max-width:none;
  width:100%;
  margin:0;
  min-height:208px;
  padding:12px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:10px;
  border-radius:15px;
  background:#f5f7fa;
  border:1px solid #dce4ee;
}
.processed-thumb {
  width:128px;height:128px;
  background:#000;
  border-radius:10px;
  padding:0;
  overflow:hidden;
  box-shadow:0 4px 12px rgba(0,0,0,.12);
}
.processed-thumb img{display:block;width:128px;height:128px;image-rendering:pixelated}
.processed-label{
  text-align:center;
  font-size:17px;
  line-height:1.35;
  font-weight:800;
  color:#4b5a6e;
}
.processed-label b{display:block;color:#18253a;font-size:17px;margin-bottom:4px}

.model-stage {
  display:flex;
  flex-direction:column;
}
.model-visual-wrap {
  flex:1;
  display:flex;
  align-items:center;
  justify-content:center;
}
.model-visual {
  position:relative;
  width:170px;height:170px;
  border-radius:44px;
  display:grid;
  place-items:center;
  background:linear-gradient(145deg,#071421 0%,#0f2941 56%,#00467f 100%);
  box-shadow:
    0 22px 42px rgba(4,25,44,.28),
    inset 0 1px 0 rgba(255,255,255,.13);
  border:1px solid rgba(255,255,255,.15);
}
.model-visual:before,.model-visual:after{
  content:"";
  position:absolute;
  width:196px;height:2px;
  left:-16px;
  background:linear-gradient(90deg,transparent,#79c9ff,transparent);
  opacity:.42;
}
.model-visual:before{top:48px}
.model-visual:after{bottom:48px}
.model-chip {
  width:102px;height:102px;
  border-radius:29px;
  display:grid;
  place-items:center;
  background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.18);
  box-shadow:inset 0 0 32px rgba(56,161,227,.14);
}
.model-chip svg{width:68px;height:68px;display:block}
.node-glow{filter:drop-shadow(0 0 5px rgba(117,207,255,.58))}

.output-allowed {
  display:inline-flex;
  padding:8px 12px;
  border-radius:999px;
  background:#eff3f7;
  border:1px solid #dce4ec;
  color:#46566c;
  font-size:14px;
  font-weight:900;
  margin-bottom:11px;
}
.prediction-empty {
  min-height:355px;
  border-radius:18px;
  border:1px dashed #c9d4e0;
  display:grid;
  place-items:center;
  text-align:center;
  color:#8190a3;
  font-size:17px;
  font-weight:800;
  background:linear-gradient(180deg,#fbfcfd,#f5f8fb);
  padding:18px;
}
.prediction-card {
  border-radius:19px;
  border:1px solid #dbe4ee;
  background:linear-gradient(180deg,#fff,#f7f9fc);
  padding:12px;
}
.top-prediction {
  min-height:205px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  border-radius:17px;
  background:linear-gradient(145deg,#0a1726,#0a3154 62%,#005b9d);
  color:#fff;
  box-shadow:0 14px 30px rgba(7,31,53,.20);
}
.top-prediction .label{
  font-size:14px;
  letter-spacing:.12em;
  text-transform:uppercase;
  font-weight:900;
  color:#d8edff;
}
.top-prediction .char{
  font-size:104px;
  line-height:.92;
  font-weight:900;
  margin:8px 0 5px;
  color:#fff;
}
.top-prediction .score{
  font-size:24px;
  font-weight:900;
  color:#fff;
}

.ranking {margin-top:12px}
.rank-row {
  display:grid;
  grid-template-columns:30px 1fr 60px;
  align-items:center;
  gap:8px;
  margin:8px 0;
}
.rank-char{font-size:18px;font-weight:900;color:#18253a}
.rank-track{height:12px;border-radius:999px;background:#e5ebf1;overflow:hidden}
.rank-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#7ac5f7,#005a9b)}
.rank-pct{text-align:right;font-size:14px;font-weight:900;color:#5a687b}

.app-footer{
  margin-top:15px;
  padding:11px 14px 2px;
  border-top:1px solid rgba(28,45,69,.16);
  text-align:center;
  color:#58677c;
  font-size:14px;
  line-height:1.5;
  font-weight:600;
}

@media(max-width:1250px){
  .gradio-container{max-width:1180px!important;padding-left:12px!important;padding-right:12px!important}
  .title-line{font-size:39px}
  .hero{grid-template-columns:1fr 110px}
  .qut-logo-frame{width:105px;height:64px}.qut-logo-frame img{width:105px;height:105px}
  .stage-card{min-height:530px;padding:12px!important}
  .arrow-wrap{min-height:530px}
  .input-draw-col{min-width:380px!important}
}

@media(max-width:980px){
  .hero{grid-template-columns:1fr}.qut-logo-frame{position:absolute;right:18px;top:18px}
  .title-line{font-size:34px}
  .pipeline-row{flex-direction:column!important}
  .stage-card{min-height:auto}
  .input-work-area{flex-direction:column!important}
  .input-draw-col,.input-preview-col{min-width:0!important}
  .arrow-wrap{min-height:auto;padding:5px 0}.arrow{transform:rotate(90deg)}
}

@media(max-width:600px){
  .title-line{font-size:25px;letter-spacing:1px}
  .qut-logo-frame{display:none}
  #drawing-canvas{width:100%;height:auto;aspect-ratio:1}
  .canvas-toolbar,.button-row{width:100%;max-width:100%}
}
"""


# Final laptop-responsive sizing/readability pass.
APP_CSS += r"""
.gradio-container{
  width:min(88vw,1650px)!important;
  max-width:none!important;
  margin-left:auto!important;
  margin-right:auto!important;
  padding-left:10px!important;
  padding-right:10px!important;
}

.tagline{
  font-size:27px!important;
  line-height:1.25!important;
  margin:10px auto 13px!important;
}

.stage-card{
  min-height:525px!important;
  padding:12px!important;
}
.stage-heading{
  height:38px!important;
  margin-bottom:9px!important;
  font-size:20px!important;
}
.arrow-wrap{min-height:525px!important}

.input-work-area{
  gap:14px!important;
  align-items:stretch!important;
}
.input-draw-col{min-width:390px!important}
.input-preview-col{min-width:220px!important}

.canvas-toolbar{
  width:380px!important;
  min-height:42px!important;
}
#drawing-canvas{
  width:380px!important;
  height:380px!important;
}
.button-row{
  width:380px!important;
  max-width:380px!important;
}
.button-row button{
  min-height:52px!important;
  font-size:20px!important;
  line-height:1.1!important;
}

.processed-placeholder,
.processed-panel{
  width:100%!important;
  min-width:0!important;
  box-sizing:border-box!important;
  min-height:196px!important;
  padding:14px!important;
}
.processed-placeholder{
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
  align-items:center!important;
  gap:7px!important;
  text-align:center!important;
  font-size:16px!important;
  line-height:1.35!important;
}
.processed-placeholder b{
  display:block!important;
  color:#18253a!important;
  font-size:21px!important;
  line-height:1.15!important;
}
.processed-placeholder span{
  display:block!important;
  color:#78869a!important;
  font-size:15px!important;
  line-height:1.35!important;
}
.processed-thumb{
  width:132px!important;
  height:132px!important;
  flex:0 0 132px!important;
}
.processed-thumb img{
  width:132px!important;
  height:132px!important;
}
.processed-label{
  font-size:17px!important;
  line-height:1.3!important;
}
.processed-label b{
  font-size:21px!important;
  line-height:1.15!important;
  margin-bottom:5px!important;
}

.model-visual{
  width:158px!important;
  height:158px!important;
}
.model-visual:before,.model-visual:after{width:184px!important}
.model-chip{
  width:96px!important;
  height:96px!important;
}
.model-chip svg{
  width:65px!important;
  height:65px!important;
}

.output-allowed{
  padding:9px 13px!important;
  margin-bottom:9px!important;
  font-size:18px!important;
  line-height:1.2!important;
}
.prediction-empty{
  min-height:344px!important;
  font-size:18px!important;
  line-height:1.4!important;
}
.prediction-card{padding:11px!important}
.top-prediction{
  min-height:190px!important;
}
.top-prediction .label{
  font-size:19px!important;
  line-height:1.15!important;
}
.top-prediction .char{
  font-size:96px!important;
  margin:5px 0 3px!important;
}
.top-prediction .score{
  font-size:27px!important;
}
.ranking{margin-top:10px!important}
.rank-row{
  grid-template-columns:34px 1fr 67px!important;
  gap:9px!important;
  margin:9px 0!important;
}
.rank-char{
  font-size:21px!important;
  line-height:1!important;
}
.rank-track{height:13px!important}
.rank-pct{
  font-size:17px!important;
  line-height:1!important;
}

@media(max-width:1450px){
  .gradio-container{
    width:96vw!important;
    max-width:none!important;
  }
}

@media(max-width:1180px){
  .gradio-container{width:97vw!important}
  .input-work-area{flex-direction:column!important}
  .input-draw-col,.input-preview-col{min-width:0!important}
  .processed-placeholder,.processed-panel{max-width:380px!important;margin:0 auto!important}
}

@media(max-width:980px){
  #drawing-canvas{width:100%!important;height:auto!important;aspect-ratio:1}
  .canvas-toolbar,.button-row{width:100%!important;max-width:100%!important}
}
"""

APP_CSS = APP_CSS.replace(
    "__BACKGROUND_TEXTURE_URL__", f"data:image/png;base64,{BACKGROUND_TEXTURE_B64}"
)


def title_tile_markup() -> str:
    """Header title text for the hero banner."""
    line_texts = ["UNDERSTANDING", "THE AI PIPELINE"]
    return "".join(
        f'<div class="title-line">{html.escape(text)}</div>' for text in line_texts
    )


def header_html() -> str:
    return f"""
    <div class="hero">
      <div class="title-art">{title_tile_markup()}</div>
      <div class="qut-logo-frame">
        <img src="data:image/png;base64,{QUT_LOGO_B64}" alt="QUT logo">
      </div>
    </div>
    <div class="tagline">Draw a number or letter and test the AI model's predictions.</div>
    """


def native_canvas_html() -> str:
    return f"""
    <div class="native-canvas-shell">
      <div class="canvas-toolbar">
        <div class="palette" aria-label="Drawing colours">
          <button type="button" class="palette-btn active" data-colour="#FFFFFF" style="background:#FFFFFF" title="White"></button>
          <button type="button" class="palette-btn" data-colour="#FF5252" style="background:#FF5252" title="Red"></button>
          <button type="button" class="palette-btn" data-colour="#FFD740" style="background:#FFD740" title="Yellow"></button>
          <button type="button" class="palette-btn" data-colour="#69F0AE" style="background:#69F0AE" title="Green"></button>
          <button type="button" class="palette-btn" data-colour="#40C4FF" style="background:#40C4FF" title="Blue"></button>
          <button type="button" class="palette-btn" data-colour="#7C4DFF" style="background:#7C4DFF" title="Purple"></button>
        </div>
        <div class="canvas-tool-group">
          <span>Brush</span>
          <input id="brush-size" type="range" min="8" max="52" value="28" aria-label="Brush size">
          <button type="button" id="eraser-toggle" class="eraser-toggle">Eraser</button>
        </div>
      </div>
      <canvas id="drawing-canvas" width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" aria-label="Drawing canvas"></canvas>
    </div>
    """


APP_JS = r"""
() => {
  function setupCanvas() {
    const canvas = document.getElementById('drawing-canvas');
    if (!canvas) return false;
    if (canvas.dataset.aiReady === '1') return true;

    canvas.dataset.aiReady = '1';
    const ctx = canvas.getContext('2d');
    let drawing = false;
    let colour = '#FFFFFF';
    let brushSize = 28;
    let erasing = false;
    let lastX = 0, lastY = 0;
    let rect = canvas.getBoundingClientRect();
    let pending = [];
    let frame = 0;

    const updateRect = () => { rect = canvas.getBoundingClientRect(); };
    const point = (ev) => ({
      x:(ev.clientX - rect.left) * canvas.width / rect.width,
      y:(ev.clientY - rect.top) * canvas.height / rect.height
    });

    const fillBlack = () => {
      pending = [];
      if (frame) { cancelAnimationFrame(frame); frame = 0; }
      ctx.save();
      ctx.globalCompositeOperation='source-over';
      ctx.fillStyle='#000000';
      ctx.fillRect(0,0,canvas.width,canvas.height);
      ctx.restore();
    };

    const configureBrush = () => {
      ctx.lineCap='round';
      ctx.lineJoin='round';
      ctx.lineWidth=brushSize;
      ctx.strokeStyle=erasing ? '#000000' : colour;
      ctx.fillStyle=erasing ? '#000000' : colour;
    };

    const drawPoint = (p) => {
      configureBrush();
      ctx.beginPath();
      ctx.arc(p.x,p.y,brushSize/2,0,Math.PI*2);
      ctx.fill();
    };

    const flush = () => {
      frame = 0;
      if (!drawing || pending.length === 0) { pending=[]; return; }
      configureBrush();
      for (const ev of pending) {
        const p = point(ev);
        ctx.beginPath();
        ctx.moveTo(lastX,lastY);
        ctx.lineTo(p.x,p.y);
        ctx.stroke();
        lastX=p.x; lastY=p.y;
      }
      pending=[];
    };

    const start = (ev) => {
      ev.preventDefault();
      updateRect();
      drawing=true;
      if (canvas.setPointerCapture) canvas.setPointerCapture(ev.pointerId);
      const p=point(ev);
      lastX=p.x; lastY=p.y;
      drawPoint(p);
    };

    const move = (ev) => {
      if (!drawing) return;
      ev.preventDefault();
      const events = ev.getCoalescedEvents ? ev.getCoalescedEvents() : [ev];
      pending.push(...events);
      if (!frame) frame=requestAnimationFrame(flush);
    };

    const stop = (ev) => {
      if (!drawing) return;
      ev.preventDefault();
      flush();
      drawing=false;
      try {
        if (canvas.releasePointerCapture && canvas.hasPointerCapture(ev.pointerId)) {
          canvas.releasePointerCapture(ev.pointerId);
        }
      } catch (_) {}
    };

    canvas.addEventListener('pointerdown',start,{passive:false});
    canvas.addEventListener('pointermove',move,{passive:false});
    canvas.addEventListener('pointerup',stop,{passive:false});
    canvas.addEventListener('pointercancel',stop,{passive:false});
    window.addEventListener('resize',updateRect,{passive:true});

    document.querySelectorAll('.palette-btn').forEach((button)=>{
      button.addEventListener('click',()=>{
        colour=button.dataset.colour || '#FFFFFF';
        erasing=false;
        document.querySelectorAll('.palette-btn').forEach(b=>b.classList.remove('active'));
        button.classList.add('active');
        document.getElementById('eraser-toggle')?.classList.remove('active');
      });
    });

    document.getElementById('brush-size')?.addEventListener('input',(ev)=>{
      brushSize=Number(ev.target.value)||28;
    });

    document.getElementById('eraser-toggle')?.addEventListener('click',(ev)=>{
      erasing=!erasing;
      ev.currentTarget.classList.toggle('active',erasing);
    });

    fillBlack();
    window.clearAICanvas=fillBlack;
    window.getAICanvasData=()=>canvas.toDataURL('image/png');
    return true;
  }

  window.setupAICanvas=setupCanvas;

  // Gradio's load event normally runs after the HTML component is mounted.
  // Short finite retries cover slower external/reverse-proxy page loads without
  // leaving a MutationObserver running forever.
  let attempts=0;
  const trySetup=()=>{
    if (setupCanvas()) return;
    attempts += 1;
    if (attempts < 12) setTimeout(trySetup, 90 * attempts);
  };
  trySetup();
}
"""


def data_url_to_rgb(data_url: str | None) -> Image.Image:
    if not data_url:
        return Image.new("RGB",(CANVAS_SIZE,CANVAS_SIZE),"black")
    if "," not in data_url:
        raise ValueError("Canvas image data was not in the expected format.")
    _, encoded = data_url.split(",",1)
    raw = base64.b64decode(encoded)
    return Image.open(BytesIO(raw)).convert("RGB")


def shift_with_zeros(image: np.ndarray, shift_y: int, shift_x: int) -> np.ndarray:
    output=np.zeros_like(image)
    source_y0=max(0,-shift_y)
    source_y1=min(image.shape[0],image.shape[0]-shift_y)
    source_x0=max(0,-shift_x)
    source_x1=min(image.shape[1],image.shape[1]-shift_x)
    target_y0=max(0,shift_y)
    target_x0=max(0,shift_x)
    target_y1=target_y0+max(0,source_y1-source_y0)
    target_x1=target_x0+max(0,source_x1-source_x0)
    if source_y1>source_y0 and source_x1>source_x0:
        output[target_y0:target_y1,target_x0:target_x1]=image[source_y0:source_y1,source_x0:source_x1]
    return output


def centre_and_resize(grayscale: Image.Image) -> np.ndarray:
    source=np.asarray(grayscale,dtype=np.uint8)
    active=source>8
    if not np.any(active):
        return np.zeros((28,28),dtype=np.uint8)
    ys,xs=np.where(active)
    crop=grayscale.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
    width,height=crop.size
    scale=min(20/max(width,1),20/max(height,1))
    rw=max(1,round(width*scale)); rh=max(1,round(height*scale))
    crop=crop.resize((rw,rh),Image.Resampling.LANCZOS)
    canvas=Image.new("L",(28,28),0)
    canvas.paste(crop,((28-rw)//2,(28-rh)//2))
    arr=np.asarray(canvas,dtype=np.uint8)
    weights=arr.astype(np.float32)
    total=float(weights.sum())
    if total>0:
        yg,xg=np.indices(arr.shape)
        cy=float((yg*weights).sum()/total)
        cx=float((xg*weights).sum()/total)
        arr=shift_with_zeros(arr,int(round(13.5-cy)),int(round(13.5-cx)))
    return arr


def preprocess(canvas_data_url: str | None) -> np.ndarray:
    rgb=data_url_to_rgb(canvas_data_url)
    return centre_and_resize(ImageOps.grayscale(rgb))


@lru_cache(maxsize=1)
def get_model() -> torch.nn.Module:
    return load_model("cpu")


def image_to_data_uri(image: Image.Image) -> str:
    buf=BytesIO()
    image.save(buf,format="PNG")
    return "data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode("ascii")


def blank_processed_html() -> str:
    return '<div class="processed-placeholder"><b>Image sent to AI</b><span>The 28 × 28 input will appear here after prediction.</span></div>'


def processed_html(model_array: np.ndarray) -> str:
    preview=Image.fromarray(model_array).resize((PREVIEW_SIZE,PREVIEW_SIZE),Image.Resampling.NEAREST)
    uri=image_to_data_uri(preview)
    return f"""
    <div class="processed-panel">
      <div class="processed-thumb"><img src="{uri}" alt="28 by 28 image sent to the AI"></div>
      <div class="processed-label"><b>Image sent to AI</b>28 × 28 grayscale</div>
    </div>
    """


def empty_prediction_html(message: str="Draw something, then click Make prediction.") -> str:
    return f'<div class="prediction-empty">{html.escape(message)}</div>'


def prediction_html(probabilities: np.ndarray) -> str:
    ranking=np.argsort(probabilities)[::-1]
    top=int(ranking[0])
    rows=[]
    for idx in ranking[:5]:
        score=float(probabilities[idx])
        rows.append(
            f'<div class="rank-row"><div class="rank-char">{CLASS_NAMES[int(idx)]}</div>'
            f'<div class="rank-track"><div class="rank-fill" style="width:{score*100:.2f}%"></div></div>'
            f'<div class="rank-pct">{score:.1%}</div></div>'
        )
    return f"""
    <div class="prediction-card">
      <div class="top-prediction">
        <div class="label">Prediction</div>
        <div class="char">{CLASS_NAMES[top]}</div>
        <div class="score">{float(probabilities[top]):.1%}</div>
      </div>
      <div class="ranking">{''.join(rows)}</div>
    </div>
    """


def predict(canvas_data_url: str | None) -> tuple[str,str]:
    try:
        model_array=preprocess(canvas_data_url)
    except Exception as exc:
        return blank_processed_html(), empty_prediction_html(f"Could not read the drawing: {exc}")
    processed=processed_html(model_array)
    if int(model_array.max())<12 or int(model_array.sum())<100:
        return processed, empty_prediction_html("The input appears blank.")
    tensor=torch.from_numpy(model_array.astype(np.float32)/255.0)
    tensor=(tensor-INPUT_MEAN)/INPUT_STD
    tensor=tensor.unsqueeze(0).unsqueeze(0)
    try:
        model=get_model()
        with torch.inference_mode():
            probabilities=torch.softmax(model(tensor),dim=1)[0].cpu().numpy()
    except Exception as exc:
        return processed, empty_prediction_html(f"Prediction unavailable: {exc}")
    return processed,prediction_html(probabilities)


def reset_app() -> tuple[str,str]:
    return blank_processed_html(),empty_prediction_html()


def model_icon_html() -> str:
    return """
    <div class="model-visual-wrap">
      <div class="model-visual">
        <div class="model-chip">
          <svg viewBox="0 0 100 100" role="img" aria-label="AI model icon">
            <g fill="none" stroke="#8ed7ff" stroke-width="4" stroke-linecap="round" class="node-glow">
              <path d="M22 26 L48 18 L75 31 L72 67 L47 80 L23 66 Z"/>
              <path d="M22 26 L47 49 L75 31 M47 49 L72 67 M47 49 L23 66 M48 18 L47 49 L47 80"/>
            </g>
            <g fill="#ffffff" class="node-glow">
              <circle cx="22" cy="26" r="6"/><circle cx="48" cy="18" r="6"/>
              <circle cx="75" cy="31" r="6"/><circle cx="72" cy="67" r="6"/>
              <circle cx="47" cy="80" r="6"/><circle cx="23" cy="66" r="6"/>
              <circle cx="47" cy="49" r="8"/>
            </g>
          </svg>
        </div>
      </div>
    </div>
    """


def gradio_major_version() -> int:
    try:
        return int(str(gr.__version__).split(".",1)[0])
    except Exception:
        return 6


GRADIO_MAJOR=gradio_major_version()
BLOCKS_KWARGS:dict[str,Any]={"title":"Understanding the AI Pipeline"}
if GRADIO_MAJOR<6:
    BLOCKS_KWARGS.update(css=APP_CSS)

with gr.Blocks(**BLOCKS_KWARGS) as demo:
    gr.HTML(header_html())

    with gr.Row(equal_height=True,elem_classes="pipeline-row"):
        with gr.Column(scale=9,min_width=650,elem_classes="stage-card"):
            gr.HTML('<div class="stage-heading"><span class="num">1</span><span>Input</span></div>')
            with gr.Row(equal_height=False, elem_classes="input-work-area"):
                with gr.Column(scale=5, min_width=390, elem_classes="input-draw-col"):
                    gr.HTML(native_canvas_html())
                    canvas_data=gr.Textbox(value="",visible=False)
                    with gr.Row(elem_classes="button-row"):
                        predict_button=gr.Button("Make prediction",variant="primary",scale=3)
                        clear_button=gr.Button("Clear",scale=1)
                with gr.Column(scale=3, min_width=220, elem_classes="input-preview-col"):
                    processed_output=gr.HTML(blank_processed_html())

        with gr.Column(scale=1,min_width=52,elem_classes="arrow-column"):
            gr.HTML('<div class="arrow-wrap"><div class="arrow">→</div></div>')

        with gr.Column(scale=3,min_width=190,elem_classes=["stage-card","model-stage"]):
            gr.HTML('<div class="stage-heading"><span class="num">2</span><span>AI Model</span></div>')
            gr.HTML(model_icon_html())

        with gr.Column(scale=1,min_width=52,elem_classes="arrow-column"):
            gr.HTML('<div class="arrow-wrap"><div class="arrow">→</div></div>')

        with gr.Column(scale=4,min_width=290,elem_classes="stage-card"):
            gr.HTML('<div class="stage-heading"><span class="num">3</span><span>Output/Predictions</span></div>')
            gr.HTML('<div class="output-allowed">Possible outputs: 0–9 and A–Z</div>')
            prediction_output=gr.HTML(empty_prediction_html())

    gr.HTML("""
      <div class="app-footer">
        <div>© 2026 Queensland University of Technology (QUT).</div>
        <div>This AI demo was developed by Dr Dimity Miller and Dr Ethan Goan.
        Thank you to the QUT eResearch team for deployment support.</div>
      </div>
    """)

    predict_button.click(
        fn=predict,
        inputs=[canvas_data],
        outputs=[processed_output,prediction_output],
        js="(_current) => { window.setupAICanvas?.(); return window.getAICanvasData ? window.getAICanvasData() : ''; }",
    )
    clear_button.click(
        fn=reset_app,
        inputs=[],
        outputs=[processed_output,prediction_output],
        js="() => { window.setupAICanvas?.(); window.clearAICanvas?.(); return []; }",
    )

    demo.load(
        fn=None,inputs=[],outputs=[],js=APP_JS,queue=False,show_progress="hidden"
    )


def parse_args() -> argparse.Namespace:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--port",type=int,default=7860)
    parser.add_argument(
        "--root-path",
        default=os.getenv("GRADIO_ROOT_PATH") or None,
        help="Reverse-proxy prefix, e.g. /ai-demo.",
    )
    parser.add_argument("--share",action="store_true")
    return parser.parse_args()


if __name__=="__main__":
    args=parse_args()
    kwargs={
        "server_name":args.host,
        "server_port":args.port,
        "share":args.share,
        "root_path":args.root_path,
        "show_error":True,
    }
    if GRADIO_MAJOR>=6:
        kwargs["css"]=APP_CSS
        demo.launch(**kwargs)
