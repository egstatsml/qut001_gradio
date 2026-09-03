import ast
import base64
import html
import os
from pathlib import Path

import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM

from qut001.constants import MODEL_WEIGHTS_DIR, IMAGE_DIR

# ============================================================
# Easy-to-edit teaching/demo settings
# ============================================================
# Maximum length of the INITIAL text entered by a student.
# Change this one number if you want to allow longer/shorter starting text.
MAX_INITIAL_WORDS = 20

# Fixed for the student-facing activity (not shown as an advanced parameter).
MAX_GENERATION_CHOICES = 50

# Maximum number of model inference requests that can run at the same time.
# Start with 1. Increase this later only after load-testing the deployment.
INFERENCE_CONCURRENCY = 1

# Number of possible next-text options shown by default.
DEFAULT_TOP_K = 5
MAX_TOP_K = 20

MODEL_NAME = "Qwen/Qwen3-0.6B"
tokenizer: AutoTokenizer | None = None
model: AutoModelForCausalLM | None = None
QUT_LOGO_PATH = Path(os.path.join(IMAGE_DIR, "qut.png"))
QUT_LOGO_B64 = base64.b64encode(QUT_LOGO_PATH.read_bytes()).decode("ascii")


def load_model():
    global tokenizer, model

    # Load once per Python process. Every student session then shares this
    # read-only model/tokenizer instance.
    if tokenizer is not None and model is not None:
        return

    model_path = os.path.join(MODEL_WEIGHTS_DIR, "qwen3_06b")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    model.eval()


def word_count(text):
    return len(text.strip().split())


def get_predictions(context, top_k):
    # Lazy load: when the app is mounted by the hub (main.py) the __main__
    # startup block never runs, so make sure the model is loaded on first use.
    load_model()
    if tokenizer is None or model is None:
        raise RuntimeError("Qwen model is not loaded; call load_model() first.")
    inputs = tokenizer(context, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits[0, -1]
    probs = torch.softmax(logits, dim=-1)
    top_probs, top_indices = torch.topk(probs, int(top_k))

    tokens = []
    probabilities = []
    for i in range(int(top_k)):
        tokens.append(tokenizer.decode([top_indices[i]]))
        probabilities.append(top_probs[i].item())
    return tokens, probabilities


def friendly_token(token):
    """Make whitespace-heavy model outputs readable without changing the token."""
    if token == "":
        return "(empty)"
    if token == "\n":
        return "↵ new line"
    if token == "\t":
        return "tab"
    if token.strip() == "":
        return "space"
    return token.strip()

def empty_probability_chart_html():
    return (
        "<div class='probability-empty'>"
        "Predict what comes next to see the AI's probabilities."
        "</div>"
    )


def build_probability_chart(tokens, probabilities):
    """Responsive probability display that scales cleanly from 5–20 predictions."""
    if not tokens:
        return empty_probability_chart_html()

    max_prob = max(probabilities) if probabilities else 1.0
    layout_class = " many-predictions" if len(tokens) > 10 else ""

    rows = []
    for i, (token, prob) in enumerate(zip(tokens, probabilities)):
        relative_width = 100.0 * prob / max_prob if max_prob > 0 else 0.0
        relative_width = max(3.0, relative_width)
        label = html.escape(friendly_token(token))
        top_class = " top-prediction" if i == 0 else ""

        rows.append(
            f"<div class='probability-row{top_class}'>"
            f"<div class='probability-label'>{label}</div>"
            f"<div class='probability-meter'>"
            f"<span style='width:{relative_width:.2f}%'></span>"
            f"</div>"
            f"<div class='probability-value'>{prob:.1%}</div>"
            f"</div>"
        )

    return (
        f"<div class='probability-chart{layout_class}'>"
        + "".join(rows)
        + "</div>"
    )

def build_step_log_df(step_log):
    rows = []
    for entry in step_log:
        ctx = entry["context_before"]
        if len(ctx) > 90:
            ctx = "..." + ctx[-87:]
        rows.append([entry["choice"], repr(entry["text"]), entry["prob"], ctx])
    return rows


def token_choices_html(tokens=None, probabilities=None, interactive=True):
    """Render true content-width text bubbles, weighted subtly by probability."""
    tokens = tokens or []
    probabilities = probabilities or []

    if not tokens:
        return (
            "<div class='token-choice-empty'>"
            "Predict what comes next to see the AI's possible next text."
            "</div>"
        )

    max_prob = max(probabilities) if probabilities else 1.0
    parts = ["<div class='token-bubble-cloud'>"]

    for i, token in enumerate(tokens):
        prob = probabilities[i] if i < len(probabilities) else 0.0
        relative = prob / max_prob if max_prob > 0 else 0.0
        font_size = 18 + round(9 * (relative ** 0.55))
        display = html.escape(friendly_token(token))
        top_class = " top-choice" if i == 0 else ""
        data_attr = f" data-token-index='{i}'" if interactive else ""
        disabled_class = "" if interactive else " disabled-choice"

        parts.append(
            f"<button type='button' class='next-text-bubble{top_class}{disabled_class}'"
            f"{data_attr} style='font-size:{font_size}px'"
            f" aria-label='Choose {display}'>{display}</button>"
        )

    parts.append("</div>")
    return "".join(parts)


def empty_token_choices_html(message=None):
    message = message or "Predict what comes next to see the AI's possible next text."
    return f"<div class='token-choice-empty'>{html.escape(message)}</div>"

def input_warning(message):
    return f"<div class='input-warning'>{html.escape(message)}</div>"


def on_start(prompt, top_k):
    top_k = int(top_k)

    if not prompt or not prompt.strip():
        return (
            empty_probability_chart_html(),
            empty_token_choices_html(),
            input_warning("Please enter some starting text."),
            gr.update(visible=False),
            gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
            gr.update(value=prompt or "", interactive=True), gr.update(interactive=True),
            "", "", 0, [], top_k, [],
            gr.update(value=[]),
        )

    n_words = word_count(prompt)
    if n_words > MAX_INITIAL_WORDS:
        return (
            empty_probability_chart_html(),
            empty_token_choices_html(),
            input_warning(
                f"Your starting text is {n_words:,} words long. "
                f"Please shorten it to {MAX_INITIAL_WORDS:,} words or fewer."
            ),
            gr.update(visible=False),
            gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
            gr.update(value=prompt, interactive=True), gr.update(interactive=True),
            "", "", 0, [], top_k, [],
            gr.update(value=[]),
        )

    tokens, probs = get_predictions(prompt, top_k)
    fig = build_probability_chart(tokens, probs)

    return (
        fig,
        token_choices_html(tokens, probs, interactive=True),
        "",
        gr.update(value=f"Choice 1 of {MAX_GENERATION_CHOICES}", visible=True),
        gr.update(interactive=False), gr.update(interactive=True), gr.update(interactive=True),
        gr.update(value=prompt, interactive=False), gr.update(interactive=False),
        prompt, prompt, 1, [], top_k, tokens,
        gr.update(value=[]),
    )


def on_choose(selection, original_prompt, context, choice_number, step_log, top_k, tokens):
    top_k = int(top_k)
    choice_number = int(choice_number)

    try:
        index = int(str(selection).split(":", 1)[0])
    except (TypeError, ValueError):
        index = -1

    if not original_prompt or not tokens or index < 0 or index >= len(tokens):
        return (
            gr.update(),
            gr.update(),
            "",
            gr.update(),
            gr.update(), gr.update(), gr.update(),
            gr.update(), gr.update(),
            original_prompt, context, choice_number, step_log, top_k, tokens,
            gr.update(value=build_step_log_df(step_log)),
        )

    token_text = tokens[index]
    current_tokens, current_probs = get_predictions(context, top_k)
    try:
        matched_index = current_tokens.index(token_text)
        prob = current_probs[matched_index]
    except ValueError:
        prob = 0.0

    new_context = context + token_text
    new_log = step_log + [{
        "choice": choice_number,
        "text": token_text,
        "prob": f"{prob:.2%}",
        "context_before": context,
    }]

    if choice_number >= MAX_GENERATION_CHOICES:
        return (
            gr.update(),
            empty_token_choices_html("Maximum of 100 choices reached."),
            "<div class='done-message'>Maximum of 100 choices reached.</div>",
            gr.update(value=f"Done after {MAX_GENERATION_CHOICES} choices", visible=True),
            gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
            gr.update(value=new_context, interactive=True), gr.update(interactive=True),
            original_prompt, new_context, choice_number, new_log, top_k, [],
            gr.update(value=build_step_log_df(new_log)),
        )

    new_tokens, new_probs = get_predictions(new_context, top_k)
    fig = build_probability_chart(new_tokens, new_probs)
    next_choice = choice_number + 1

    return (
        fig,
        token_choices_html(new_tokens, new_probs, interactive=True),
        "",
        gr.update(value=f"Choice {next_choice} of {MAX_GENERATION_CHOICES}", visible=True),
        gr.update(interactive=False), gr.update(interactive=True), gr.update(interactive=True),
        gr.update(value=new_context, interactive=False), gr.update(interactive=False),
        original_prompt, new_context, next_choice, new_log, top_k, new_tokens,
        gr.update(value=build_step_log_df(new_log)),
    )


def on_stop(context):
    return (
        empty_token_choices_html("Stopped. Predict again when you are ready."),
        gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
        gr.update(value=context, interactive=True), gr.update(interactive=True),
        gr.update(value="Stopped. Edit the input text or press Predict what comes next to continue.", visible=True),
    )


def on_reset():
    return (
        empty_probability_chart_html(),
        empty_token_choices_html(),
        "",
        gr.update(visible=False),
        gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
        gr.update(value="", interactive=True), gr.update(value=DEFAULT_TOP_K, interactive=True),
        "", "", 0, [], DEFAULT_TOP_K, [],
        gr.update(value=[]),
    )

def show_advanced_help(prompt, context):
    """Open advanced settings and pause/unlock any active generation."""
    active_text = context if context else (prompt or "")
    return (
        gr.update(visible=True),
        empty_token_choices_html(
            "Generation paused while you change Advanced parameters."
        ),
        gr.update(interactive=True),
        gr.update(interactive=False),
        gr.update(interactive=True),
        gr.update(value=active_text, interactive=True),
        gr.update(interactive=True),
        gr.update(value="Paused — change the setting, then predict again.", visible=True),
    )


def hide_advanced_help():
    return gr.update(visible=False)


def show_history(step_log):
    return gr.update(visible=True), gr.update(value=build_step_log_df(step_log))


def hide_history():
    return gr.update(visible=False)


def hero_html():
    return f"""
    <section class="llm-hero">
      <div class="hero-copy">
        <div class="hero-eyebrow">QUT001 · AI IN THE REAL WORLD</div>
        <h1>Understanding how Generative AI creates text</h1>
        <p>See how a Generative AI system repeatedly predicts what could come next, one small piece of text at a time.</p>
      </div>
      <div class="hero-logo-wrap"><img src="data:image/png;base64,{QUT_LOGO_B64}" alt="QUT logo"></div>
    </section>
    """


def pipeline_html():
    return """
    <div class="pipeline-strip" aria-label="How generative AI creates text">
      <div class="pipe-step"><div class="pipe-icon">1</div><div><b>Input text</b><span>the text so far</span></div></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><div class="pipe-icon">2</div><div><b>Predict next text</b><span>possible options get probabilities</span></div></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><div class="pipe-icon">3</div><div><b>Choose and repeat</b><span>your choice becomes part of the next input</span></div></div>
      <div class="pipe-repeat">↻ REPEAT</div>
    </div>
    """


def section_heading(number, title, subtitle):
    return f"""
    <div class="section-heading">
      <div class="section-number">{number}</div>
      <div><h2>{html.escape(title)}</h2><p>{html.escape(subtitle)}</p></div>
    </div>
    """


def empty_generated_text_html():
    return (
        "<div class='generated-text-empty'>"
        "Your generated text will appear here as you choose what comes next."
        "</div>"
    )


def generated_text_heading():
    return """
    <div class="section-heading">
      <div><h2>Your generated text</h2><p>Your starting prompt, then the text you built from the AI's predictions.</p></div>
    </div>
    """


def build_generated_text_html(original_prompt, context):
    """Render the student's starting prompt (italicised, muted) followed by
    the text they built by choosing the AI's predictions. Whitespace is
    preserved via CSS pre-wrap so model-produced spaces/newlines display
    naturally; the generated part is intentionally NOT stripped (the first
    generated token usually carries the separating space)."""
    if not original_prompt or not context:
        return empty_generated_text_html()

    prompt_html = html.escape(original_prompt)
    generated = context[len(original_prompt):]  # safe: prefix invariant, see Global Constraints
    generated_html = html.escape(generated)

    return (
        f"<div class='generated-text-body'>"
        f"<span class='generated-prompt'>{prompt_html}</span>"
        f"<span class='generated-delta'>{generated_html}</span>"
        f"</div>"
    )


def advanced_help_html():
    return """
    <div class="advanced-help-content">
      <div class="advanced-help-kicker">OPTIONAL SETTING</div>
      <h2>Advanced parameters</h2>
      <p>You can leave this at the default. This setting changes <b>how many of the AI's most likely next-text predictions</b> the demo shows you.</p>
      <div class="advanced-explainer">
        <div class="advanced-help-icon">5</div>
        <div>
          <h3>Top predictions</h3>
          <p>If this is set to 5, you see the five possibilities the AI currently considers most likely. Increase it to see more alternatives. <b>It does not make the AI more accurate or more intelligent</b> — it only changes how many possibilities are displayed.</p>
        </div>
      </div>
    </div>
    """

def footer_html():
    return """
    <div class="app-footer">
      This AI demo was developed by <b>Dr Ethan Goan</b> and <b>Dr Dimity Miller</b>.
      Thank you to the QUT eResearch team for deployment support.
    </div>
    """


CSS = r"""
:root{
  --qut-blue:#006DAE;--qut-deep:#043B68;--qut-navy:#062D4E;--qut-orange:#F4A024;
  --ink:#18324A;--muted:#5E7185;--line:#D9E4EE;--soft:#F3F7FA;
}
*{box-sizing:border-box}
body{background:radial-gradient(circle at 88% -10%,rgba(0,109,174,.13),transparent 32%),linear-gradient(180deg,#F7FAFC 0%,#EEF4F8 100%)!important}
.gradio-container{width:min(97vw,1520px)!important;max-width:1520px!important;margin:0 auto!important;padding:7px 14px 14px!important;background:transparent!important;color:var(--ink)!important;font-family:Arial,Helvetica,sans-serif!important;font-synthesis:none!important}
.gradio-container *{font-family:Arial,Helvetica,sans-serif;font-synthesis:none}
footer{display:none!important}

/* compact hero */
.llm-hero{min-height:92px;display:grid;grid-template-columns:minmax(0,1fr) 76px;align-items:center;gap:16px;padding:11px 16px;border-radius:19px;background:linear-gradient(125deg,var(--qut-navy),var(--qut-deep) 58%,#075B93);color:#fff;border:1px solid rgba(255,255,255,.18);box-shadow:0 10px 28px rgba(6,45,78,.15);overflow:hidden}
.hero-eyebrow{font-size:18px;font-weight:800;letter-spacing:.11em;color:#BFE4FA;margin-bottom:3px}
.llm-hero h1{margin:0!important;color:#fff!important;font-size:29px!important;line-height:1.04!important;letter-spacing:-.02em;font-weight:800!important}
.llm-hero p{margin:5px 0 0!important;color:#EAF5FC!important;font-size:18px!important;line-height:1.25!important}
.hero-logo-wrap{width:72px;height:72px;border-radius:15px;overflow:hidden;background:#006DAE;box-shadow:0 7px 20px rgba(0,0,0,.18);border:1px solid rgba(255,255,255,.24)}
.hero-logo-wrap img{width:100%;height:100%;display:block;object-fit:contain}

/* 3-stage strip */
.pipeline-strip{display:grid;grid-template-columns:1fr auto 1.25fr auto 1.65fr auto;align-items:center;gap:7px;margin:6px 0;padding:6px 10px;border:1px solid #D7E4EF;border-radius:14px;background:rgba(255,255,255,.95);box-shadow:0 3px 11px rgba(26,67,102,.05)}
.pipe-step{display:flex;align-items:center;gap:7px;min-width:0}.pipe-icon{width:28px;height:28px;flex:0 0 28px;display:grid;place-items:center;border-radius:9px;background:#E8F3FA;color:var(--qut-blue);font-size:18px;font-weight:900}.pipe-step b{display:block;font-size:18px;line-height:1.05}.pipe-step span{display:block;font-size:18px;color:var(--muted);line-height:1.1;margin-top:1px}.pipe-arrow{font-size:18px;color:#9BAABD;font-weight:700}.pipe-repeat{font-size:18px;font-weight:800;color:#7B5A16;background:#FFF2D8;padding:6px 8px;border-radius:9px;text-align:center}

.panel-card{border:1px solid var(--line)!important;border-radius:16px!important;background:#fff!important;box-shadow:0 5px 16px rgba(30,68,102,.06)!important;padding:8px 11px!important}
.section-heading{display:flex;align-items:center;gap:8px;margin:0 0 4px}.section-number{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;background:var(--qut-blue);color:#fff;font-size:18px;font-weight:900;flex:0 0 28px}.section-heading h2{margin:0!important;font-size:19px!important;line-height:1.06!important;color:var(--ink)!important}.section-heading p{margin:1px 0 0!important;font-size:18px!important;color:var(--muted)!important;line-height:1.18!important}

/* section 1: compact, live input */
.top-row{gap:7px!important;align-items:stretch!important;margin-bottom:5px!important}.input-card{padding:8px 11px!important}.input-card .section-heading{margin-bottom:2px!important}
#prompt-input label,#top-k-input label{font-size:18px!important;font-weight:800!important;color:#344B60!important}
#prompt-input textarea{min-height:58px!important;max-height:90px!important;font-size:18px!important;line-height:1.35!important;border-radius:11px!important;padding:8px 10px!important;background:#FAFCFE!important}
.action-row{gap:7px!important;margin-top:1px!important}.action-row button{min-height:40px!important;border-radius:10px!important;font-size:18px!important;font-weight:800!important}.action-row .primary{background:var(--qut-orange)!important;border-color:#DB8610!important;color:#2C210C!important}
#status-html{min-height:0!important}.input-warning,.done-message{margin-top:5px;padding:7px 9px;border-radius:9px;font-size:18px;font-weight:700}.input-warning{background:#FFF0E5;border:1px solid #F0C39F;color:#8A4B18}.done-message{background:#EAF7F2;border:1px solid #C1E7D7;color:#17674D}

/* advanced parameter */
.advanced-card{max-width:360px!important;padding:9px 11px!important;background:linear-gradient(120deg,#F4F8FC,#F8F6FE)!important;border:1px solid #D8E3EF!important;display:flex!important;flex-direction:column!important;justify-content:center!important}.advanced-title-row{gap:5px!important;align-items:center!important;margin-bottom:3px!important}.advanced-title span{display:block;font-size:18px;font-weight:800;color:#2D4861}.advanced-title small{display:block;font-size:18px;color:#6A7D90;margin-top:1px}
#advanced-info-btn{min-width:140px!important;max-width:140px!important;margin-left:0!important}#advanced-info-btn button{min-width:136px!important;height:42px!important;padding:0 10px!important;border-radius:11px!important;font-size:18px!important;font-weight:800!important;background:#E1F2FB!important;color:#075F96!important;border:2px solid #95CCE7!important;box-shadow:0 4px 11px rgba(0,109,174,.10)!important}
#top-k-input{margin-top:2px!important}#top-k-input input,#top-k-input button{font-size:18px!important}

/* help modal */
#advanced-help-modal{position:fixed!important;inset:0!important;z-index:9999!important;background:rgba(8,28,46,.64)!important;backdrop-filter:blur(4px)!important;padding:22px!important;overflow:auto!important}#advanced-help-modal>div{min-height:100%!important;display:flex!important;align-items:center!important;justify-content:center!important}.advanced-help-card{width:min(760px,94vw)!important;max-width:760px!important;padding:27px 29px!important;border-radius:22px!important;background:#fff!important;border:1px solid #D7E3ED!important;box-shadow:0 24px 70px rgba(2,25,44,.28)!important}.advanced-help-kicker{font-size:18px;font-weight:900;letter-spacing:.12em;color:var(--qut-blue)}.advanced-help-content h2{font-size:27px!important;margin:5px 0 9px!important}.advanced-help-content>p,.advanced-help-item p{font-size:18px!important;line-height:1.5!important;color:#536A7E!important}.advanced-help-item{display:grid;grid-template-columns:48px 1fr;gap:14px;align-items:start;padding:14px 0;border-top:1px solid #E3EAF1}.advanced-help-icon{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;background:#E7F3FA;color:#08679D;font-size:18px;font-weight:900}.advanced-help-item h3{font-size:20px!important;margin:0 0 3px!important}.advanced-help-item p{margin:0!important}#advanced-close-btn button{min-height:46px!important;font-size:18px!important;font-weight:800!important;border-radius:11px!important;background:var(--qut-blue)!important}

#step-label{margin:0!important;min-height:0!important}#step-label p{display:inline-flex!important;margin:0 0 4px!important;padding:3px 8px!important;border-radius:999px!important;background:#E7F3FA!important;color:#075A91!important;font-size:18px!important;font-weight:800!important}

/* sections 2 + 3 */
.prediction-row{gap:7px!important;align-items:stretch!important}.prediction-card{min-height:238px!important;padding:8px 10px!important}.choice-card{min-height:238px!important;padding:8px 10px!important;max-width:480px!important}.prediction-card .section-heading,.choice-card .section-heading{margin-bottom:2px!important}
#bar-chart{margin-top:10px!important;min-height:200px!important;max-height:218px!important}#bar-chart>label,#bar-chart .label-wrap{display:none!important}

.token-cloud{display:flex!important;flex-wrap:wrap!important;align-content:flex-start!important;justify-content:center!important;gap:8px!important;padding:11px 6px 5px!important;min-height:165px!important}.token-cloud>div{flex:0 0 auto!important;min-width:0!important;width:auto!important}.token-bubble button{border-radius:999px!important;border:1px solid #BBD7E8!important;background:linear-gradient(180deg,#F5FBFE,#E7F4FA)!important;color:#0B527F!important;font-weight:800!important;box-shadow:0 4px 11px rgba(19,82,121,.08)!important;padding:7px 12px!important;min-width:54px!important;min-height:42px!important;transition:transform .12s ease,box-shadow .12s ease!important}.token-bubble button:hover{transform:translateY(-2px)!important;background:#DFF1F9!important;box-shadow:0 7px 15px rgba(19,82,121,.14)!important}.token-rank-1 button{font-size:26px!important;background:linear-gradient(180deg,#FFF5DF,#FFE7B4)!important;border-color:#E7B75A!important;color:#744A00!important;min-height:52px!important}.token-rank-2 button{font-size:23px!important}.token-rank-3 button{font-size:21px!important}.token-rank-4 button,.token-rank-5 button{font-size:19px!important}.token-rank-6 button,.token-rank-7 button,.token-rank-8 button{font-size:18px!important}.token-rank-9 button,.token-rank-10 button,.token-rank-11 button,.token-rank-12 button,.token-rank-13 button,.token-rank-14 button,.token-rank-15 button,.token-rank-16 button,.token-rank-17 button,.token-rank-18 button,.token-rank-19 button,.token-rank-20 button{font-size:18px!important}

.history-wrap{margin-top:5px!important}.history-wrap summary{font-size:18px!important;font-weight:800!important;color:#52677A!important}.history-wrap table{font-size:18px!important}
.app-footer{margin:6px 0 0;padding:7px 10px;border-top:1px solid #D9E4EE;text-align:center;font-size:18px;line-height:1.25;color:#66798B}.app-footer b{color:#3F556A}

@media(min-width:1000px) and (max-height:850px){.gradio-container{padding-top:5px!important}.llm-hero{min-height:82px!important;padding:8px 13px!important;grid-template-columns:minmax(0,1fr) 66px!important}.llm-hero h1{font-size:27px!important}.llm-hero p{font-size:18px!important}.hero-logo-wrap{width:64px;height:64px}.pipeline-strip{margin:4px 0!important;padding:5px 9px!important}.top-row{margin-bottom:4px!important}.input-card,.advanced-card{padding-top:6px!important;padding-bottom:6px!important}#prompt-input textarea{min-height:48px!important;max-height:70px!important}.action-row button{min-height:37px!important}.prediction-card,.choice-card{min-height:216px!important}#bar-chart{min-height:178px!important;max-height:194px!important;margin-top:8px!important}.token-cloud{min-height:145px!important;padding-top:8px!important}.token-bubble button{min-height:39px!important;padding:6px 10px!important}.token-rank-1 button{min-height:46px!important}}
@media(max-width:900px){.llm-hero{grid-template-columns:1fr 66px}.pipeline-strip{grid-template-columns:1fr;gap:4px}.pipe-arrow{transform:rotate(90deg);justify-self:center}.pipe-repeat{justify-self:start}.top-row,.prediction-row{display:block!important}.advanced-card,.choice-card{max-width:none!important;margin-top:7px!important}#bar-chart{max-height:none!important}}

/* v4 final interaction polish */
.input-card{margin-bottom:5px!important;padding:8px 11px!important}.input-card .section-heading{margin-bottom:3px!important}.input-card .section-heading h2{font-size:19px!important}.input-card .section-heading p{font-size:18px!important}#prompt-input textarea{min-height:48px!important;max-height:76px!important}.action-row{gap:7px!important;margin-top:2px!important;align-items:stretch!important}
#advanced-info-btn{min-width:176px!important}#advanced-info-btn button{min-height:40px!important;width:100%!important;border-radius:10px!important;padding:0 11px!important;background:#EDF6FB!important;border:1px solid #B8D8E9!important;color:#075E93!important;font-size:18px!important;font-weight:800!important;box-shadow:none!important}#advanced-info-btn button:hover{background:#DFF1FA!important;border-color:#8CC5E1!important}
#advanced-help-modal{position:fixed!important;inset:0!important;z-index:9999!important;background:rgba(8,28,46,.66)!important;backdrop-filter:blur(4px)!important;padding:22px!important;overflow:auto!important}#advanced-help-modal>div{min-height:100%!important;display:flex!important;align-items:center!important;justify-content:center!important}.advanced-help-card{width:min(690px,94vw)!important;max-width:690px!important;padding:27px 29px!important;border-radius:22px!important;background:#fff!important;border:1px solid #D7E3ED!important;box-shadow:0 24px 70px rgba(2,25,44,.28)!important}.advanced-help-kicker{font-size:18px!important;font-weight:900!important;letter-spacing:.12em!important;color:var(--qut-blue)!important}.advanced-help-content h2{margin:5px 0 8px!important;font-size:27px!important;color:var(--ink)!important}.advanced-help-content>p{margin:0 0 15px!important;font-size:18px!important;line-height:1.48!important;color:#536A7E!important}.advanced-explainer{display:grid;grid-template-columns:48px 1fr;gap:14px;align-items:start;padding:14px 0 5px;border-top:1px solid #E2EAF1}.advanced-explainer h3{margin:0 0 4px!important;font-size:20px!important;color:var(--ink)!important}.advanced-explainer p{margin:0!important;font-size:18px!important;line-height:1.48!important;color:#536A7E!important}#top-k-input{margin:13px 0 0!important}#top-k-input label{font-size:18px!important;font-weight:800!important}.advanced-slider-note{margin-top:-3px;text-align:center;font-size:18px;color:#718398}#advanced-close-btn button{min-height:45px!important;margin-top:4px!important;font-size:18px!important;font-weight:800!important;border-radius:11px!important;background:var(--qut-blue)!important}
#token-choice-html{min-height:155px!important}.token-bubble-cloud{min-height:155px;display:flex;flex-wrap:wrap;gap:10px 11px;align-content:center;justify-content:center;padding:10px 6px 8px}.next-text-bubble{appearance:none;-webkit-appearance:none;flex:0 0 auto;width:auto;max-width:100%;min-width:0;min-height:44px;padding:9px 16px;border-radius:999px;border:1px solid #B5D8E9;background:linear-gradient(180deg,#F1FAFE 0%,#DFF2FA 100%);color:#075B8E;font-family:Arial,Helvetica,sans-serif!important;font-weight:800;line-height:1.05;white-space:nowrap;box-shadow:0 5px 13px rgba(16,82,122,.10),inset 0 1px 0 rgba(255,255,255,.8);cursor:pointer;transition:transform .12s ease,box-shadow .12s ease,background .12s ease}.next-text-bubble:nth-child(3n+2){background:linear-gradient(180deg,#F4F8FF 0%,#E5EEFB 100%);border-color:#C0D2EB;color:#355A87}.next-text-bubble:nth-child(3n){background:linear-gradient(180deg,#F3FBF9 0%,#E1F3EE 100%);border-color:#BBDDD3;color:#256B5E}.next-text-bubble.top-choice{background:linear-gradient(180deg,#FFF7E7 0%,#FFE8B9 100%);border-color:#E7B75A;color:#744A00;box-shadow:0 6px 16px rgba(177,116,13,.14),inset 0 1px 0 rgba(255,255,255,.85)}.next-text-bubble:hover{transform:translateY(-2px) scale(1.02);box-shadow:0 8px 18px rgba(16,82,122,.16)}.next-text-bubble:active{transform:translateY(0) scale(.99)}.disabled-choice{cursor:default!important;opacity:.60}.token-choice-empty{min-height:145px;display:grid;place-items:center;padding:14px;border:1px dashed #C8D8E4;border-radius:13px;background:linear-gradient(180deg,#FAFCFD,#F5F8FA);color:#74879A;text-align:center;font-size:18px}.selection-bridge{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important;margin:0!important;padding:0!important}
.choice-card{min-height:232px!important;max-width:500px!important;padding-bottom:7px!important}.choice-card .section-heading h2{font-size:18px!important;line-height:1.13!important}#history-show-btn{max-width:210px!important;margin:0 auto!important}#history-show-btn button{min-height:34px!important;border:none!important;background:transparent!important;box-shadow:none!important;color:#536D82!important;text-decoration:underline!important;font-size:18px!important;font-weight:700!important}#history-show-btn button:hover{color:#075F96!important;background:#F3F8FB!important}
.history-panel{margin-top:6px!important;padding:9px 11px!important;border:1px solid #D8E4ED!important;border-radius:14px!important;background:#fff!important;box-shadow:0 5px 15px rgba(30,68,102,.055)!important}.history-heading-row{align-items:center!important;margin-bottom:5px!important}.history-heading b{display:block;font-size:18px;color:var(--ink)}.history-heading span{display:block;margin-top:1px;font-size:18px;color:#708296}#history-hide-btn{max-width:120px!important}#history-hide-btn button{min-height:34px!important;font-size:18px!important;border-radius:9px!important}#step-log-table table{font-family:Arial,Helvetica,sans-serif!important}#step-log-table th{font-size:18px!important;font-weight:800!important;background:#F1F6F9!important}#step-log-table td{font-size:18px!important}
@media(min-width:1000px) and (max-height:850px){.input-card{padding-top:6px!important;padding-bottom:6px!important}#prompt-input textarea{min-height:42px!important;max-height:62px!important}.action-row button{min-height:37px!important}#token-choice-html,.token-bubble-cloud{min-height:136px!important}.next-text-bubble{min-height:39px!important;padding:7px 13px!important}.choice-card{min-height:214px!important}}
@media(max-width:900px){#advanced-info-btn{min-width:150px!important}.next-text-bubble{white-space:normal}}


/* ============================================================
   v5 responsive predictions + laptop readability
   ============================================================ */
#probability-chart{margin-top:7px!important;min-height:0!important}
.probability-chart{
  display:grid;
  grid-template-columns:1fr;
  gap:7px;
  padding:8px 4px 5px;
}
.probability-chart.many-predictions{
  grid-template-columns:repeat(2,minmax(0,1fr));
  column-gap:18px;
  row-gap:7px;
}
.probability-row{
  display:grid;
  grid-template-columns:minmax(72px,28%) minmax(90px,1fr) 58px;
  align-items:center;
  gap:9px;
  min-height:34px;
  padding:3px 5px;
  border-radius:9px;
}
.probability-row.top-prediction{background:#FFF8E9}
.probability-label{
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  font-size:18px;font-weight:800;color:#26445D
}
.probability-meter{
  position:relative;height:11px;overflow:hidden;border-radius:999px;background:#E8F0F5
}
.probability-meter span{
  display:block;height:100%;border-radius:999px;
  background:linear-gradient(90deg,#6DB6DA,#1784B9)
}
.probability-row.top-prediction .probability-meter span{
  background:linear-gradient(90deg,#F8C35D,#F29A13)
}
.probability-value{text-align:right;font-size:18px;font-weight:800;color:#496276}
.probability-empty{
  min-height:150px;display:grid;place-items:center;padding:14px;
  border:1px dashed #C8D8E4;border-radius:13px;
  background:linear-gradient(180deg,#FAFCFD,#F5F8FA);
  color:#74879A;text-align:center;font-size:18px
}
.prediction-card{min-height:0!important;height:auto!important}
.prediction-row{align-items:flex-start!important}

/* Generation history belongs underneath the whole prediction/choice activity. */
.history-control-row{
  justify-content:center!important;
  margin:3px 0 0!important;
  min-height:32px!important
}
#history-show-btn{
  width:auto!important;min-width:190px!important;max-width:230px!important;margin:0 auto!important
}
#history-show-btn button{min-height:34px!important;padding:4px 12px!important}

/* "Input text" is 14px in the current design: use that as the absolute floor
   for anything a student is expected to read. */
.gradio-container small,
.gradio-container summary,
.gradio-container label,
.gradio-container .caption,
.hero-eyebrow,
.hero-model-pill,
.pipe-repeat,
.pipe-step span,
.advanced-slider-note,
.app-footer,
.history-heading span,
#history-show-btn button,
#step-label p{
  font-size:18px!important
}

/* Laptop space savings come from geometry, never from shrinking readable text. */
@media(min-width:1000px) and (max-height:850px){
  .probability-chart{gap:5px!important;padding-top:5px!important}
  .probability-chart.many-predictions{column-gap:14px!important;row-gap:5px!important}
  .probability-row{min-height:30px!important;padding-top:2px!important;padding-bottom:2px!important}
  .probability-label{font-size:18px!important}
  .probability-value{font-size:18px!important}
  .history-control-row{margin-top:1px!important}
}
@media(max-width:1050px){
  .probability-chart.many-predictions{grid-template-columns:1fr}
}


/* ============================================================
   v6 13-inch laptop readability pass
   ============================================================ */

/* 16px minimum for student-readable text. */
.gradio-container,
.gradio-container p,
.gradio-container span,
.gradio-container div,
.gradio-container label,
.gradio-container small,
.gradio-container summary,
.gradio-container button,
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container table,
.gradio-container th,
.gradio-container td{
  font-size:18px;
}

/* Key content sits above the minimum. */
.llm-hero h1{font-size:31px!important}
.llm-hero p{font-size:18px!important}
.hero-eyebrow{font-size:18px!important}
.hero-model-pill{font-size:18px!important}

.pipe-copy b{font-size:18px!important}
.pipe-copy span{font-size:18px!important}
.pipe-repeat{font-size:18px!important}
.pipe-icon{font-size:18px!important}

.section-heading h2{font-size:21px!important}
.section-heading p{font-size:18px!important}
.section-number{font-size:18px!important}

.input-card .section-heading h2{font-size:21px!important}
.input-card .section-heading p{font-size:18px!important}
#prompt-input label{font-size:18px!important}
#prompt-input textarea{
  font-size:18px!important;
  line-height:1.42!important;
}

#start-btn button,
#stop-btn button,
#reset-btn button,
#advanced-info-btn button{
  font-size:18px!important;
}

#step-label p{font-size:18px!important}

.prediction-card .section-heading h2,
.choice-card .section-heading h2{
  font-size:20px!important;
}
.prediction-card .section-heading p,
.choice-card .section-heading p{
  font-size:18px!important;
}

.probability-label{font-size:18px!important}
.probability-value{font-size:18px!important}
.probability-empty{font-size:18px!important}

.next-text-bubble{min-height:46px!important}
.token-choice-empty{font-size:18px!important}

.advanced-help-kicker{font-size:18px!important}
.advanced-help-content h2{font-size:28px!important}
.advanced-help-content>p{font-size:18px!important}
.advanced-explainer h3{font-size:21px!important}
.advanced-explainer p{font-size:18px!important}
#top-k-input label{font-size:18px!important}
.advanced-slider-note{font-size:18px!important}
#advanced-close-btn button{font-size:18px!important}

#history-show-btn button{font-size:18px!important}
.history-heading b{font-size:18px!important}
.history-heading span{font-size:18px!important}
#history-hide-btn button{font-size:18px!important}
#step-log-table th{font-size:18px!important}
#step-log-table td{font-size:18px!important}
.app-footer{font-size:18px!important}

/* Laptop compacting through geometry, not smaller fonts. */
@media(min-width:1000px) and (max-height:850px){
  .gradio-container{
    padding-top:5px!important;
    padding-bottom:10px!important;
  }
  .llm-hero{
    min-height:82px!important;
    padding-top:9px!important;
    padding-bottom:9px!important;
  }
  .llm-hero h1{font-size:29px!important}
  .llm-hero p{font-size:18px!important}

  .pipeline-strip{
    margin-top:4px!important;
    margin-bottom:5px!important;
    padding-top:5px!important;
    padding-bottom:5px!important;
  }

  .input-card{
    padding-top:6px!important;
    padding-bottom:6px!important;
  }
  #prompt-input textarea{
    min-height:44px!important;
    max-height:66px!important;
  }

  .action-row{margin-top:1px!important}
  .action-row button{min-height:39px!important}

  .prediction-card,
  .choice-card{
    padding-top:7px!important;
    padding-bottom:7px!important;
  }

  .probability-chart{
    gap:4px!important;
    padding-top:4px!important;
    padding-bottom:3px!important;
  }
  .probability-chart.many-predictions{
    row-gap:4px!important;
  }
  .probability-row{
    min-height:31px!important;
    padding-top:1px!important;
    padding-bottom:1px!important;
  }

  .token-bubble-cloud{
    padding-top:8px!important;
    padding-bottom:6px!important;
  }

  .history-control-row{margin-top:1px!important}
}


/* ============================================================
   v7: 18px minimum readability for 13-inch laptops
   ============================================================ */

/* Anything students are expected to read is at least 18px. */
.gradio-container,
.gradio-container p,
.gradio-container span,
.gradio-container div,
.gradio-container label,
.gradio-container small,
.gradio-container summary,
.gradio-container button,
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container th,
.gradio-container td{
  font-size:18px;
}

/* Main instructional content deliberately sits above the floor. */
.llm-hero h1{font-size:32px!important}
.llm-hero p{font-size:19px!important}
.hero-eyebrow{font-size:18px!important}
.hero-model-pill{font-size:18px!important}

.pipe-copy b{font-size:19px!important}
.pipe-copy span{font-size:18px!important}
.pipe-repeat{font-size:18px!important}
.pipe-icon{font-size:18px!important}

.section-heading h2{font-size:23px!important}
.section-heading p{font-size:19px!important}
.section-number{font-size:19px!important}

.input-card .section-heading h2{font-size:23px!important}
.input-card .section-heading p{font-size:19px!important}
#prompt-input label{font-size:18px!important}
#prompt-input textarea{
  font-size:19px!important;
  line-height:1.42!important;
}

.action-row button{font-size:18px!important}
#advanced-info-btn button{font-size:18px!important}
#step-label p{font-size:18px!important}

.prediction-card .section-heading h2,
.choice-card .section-heading h2{
  font-size:22px!important;
}
.prediction-card .section-heading p,
.choice-card .section-heading p{
  font-size:19px!important;
}

.probability-label{font-size:19px!important}
.probability-value{font-size:18px!important}
.probability-empty{font-size:18px!important}
.token-choice-empty{font-size:18px!important}

.advanced-help-kicker{font-size:18px!important}
.advanced-help-content h2{font-size:30px!important}
.advanced-help-content>p{font-size:19px!important}
.advanced-explainer h3{font-size:23px!important}
.advanced-explainer p{font-size:19px!important}
#top-k-input label{font-size:19px!important}
.advanced-slider-note{font-size:18px!important}
#advanced-close-btn button{font-size:18px!important}

#history-show-btn button{font-size:18px!important}
.history-heading b{font-size:20px!important}
.history-heading span{font-size:18px!important}
#history-hide-btn button{font-size:18px!important}
#step-log-table th{font-size:18px!important}
#step-log-table td{font-size:18px!important}
.app-footer{font-size:18px!important}

/* Keep the 13-inch layout compact through spacing, not tiny typography. */
@media(min-width:1000px) and (max-height:850px){
  .gradio-container{
    padding-top:4px!important;
    padding-bottom:8px!important;
  }

  .llm-hero{
    min-height:80px!important;
    padding-top:8px!important;
    padding-bottom:8px!important;
  }
  .llm-hero h1{font-size:30px!important}
  .llm-hero p{font-size:18px!important}

  .pipeline-strip{
    margin-top:3px!important;
    margin-bottom:4px!important;
    padding-top:4px!important;
    padding-bottom:4px!important;
  }

  .input-card{
    padding-top:5px!important;
    padding-bottom:5px!important;
  }
  #prompt-input textarea{
    min-height:44px!important;
    max-height:68px!important;
  }

  .action-row{
    margin-top:1px!important;
    gap:6px!important;
  }
  .action-row button{min-height:40px!important}

  .prediction-card,
  .choice-card{
    padding-top:6px!important;
    padding-bottom:6px!important;
  }

  .probability-chart{
    gap:4px!important;
    padding-top:3px!important;
    padding-bottom:2px!important;
  }
  .probability-chart.many-predictions{row-gap:4px!important}
  .probability-row{
    min-height:32px!important;
    padding-top:1px!important;
    padding-bottom:1px!important;
  }

  .token-bubble-cloud{
    padding-top:7px!important;
    padding-bottom:5px!important;
  }

  .history-control-row{margin-top:1px!important}
}

"""


with gr.Blocks(title="QUT001 · Understanding how Generative AI creates text") as demo:
    gr.HTML(hero_html())
    gr.HTML(pipeline_html())

    with gr.Group(elem_classes=["panel-card", "input-card"]):
        gr.HTML(section_heading(
            "1",
            "Generative AI input text",
            "Start with some text. Every choice you make is added here and becomes the AI's new input.",
        ))
        prompt_input = gr.Textbox(
            label=f"Input text (up to {MAX_INITIAL_WORDS:,} starting words)",
            placeholder="Try: Artificial intelligence can help us...",
            elem_id="prompt-input",
        )
        with gr.Row(elem_classes=["action-row"]):
            start_btn = gr.Button("Predict what comes next", variant="primary", scale=3)
            stop_btn = gr.Button("Stop", variant="stop", interactive=False, scale=1)
            reset_btn = gr.Button("Reset", variant="secondary", scale=1)
            advanced_info_btn = gr.Button(
                "⚙ Advanced parameters",
                variant="secondary",
                scale=1,
                elem_id="advanced-info-btn",
            )
        status_html = gr.HTML("", elem_id="status-html")

    with gr.Group(visible=False, elem_id="advanced-help-modal") as advanced_help_modal:
        with gr.Column(elem_classes=["advanced-help-card"]):
            gr.HTML(advanced_help_html())
            top_k_input = gr.Slider(
                minimum=5,
                maximum=MAX_TOP_K,
                value=DEFAULT_TOP_K,
                step=1,
                label="Number of top predictions to show",
                elem_id="top-k-input",
            )
            gr.HTML(
                '<div class="advanced-slider-note">'
                'Default: 5 &nbsp;·&nbsp; Range: 5–20'
                '</div>'
            )
            advanced_close_btn = gr.Button("Done", variant="primary", elem_id="advanced-close-btn")

    step_label = gr.Markdown(visible=False, elem_id="step-label")

    with gr.Row(equal_height=False, elem_classes=["prediction-row"]):
        with gr.Column(scale=5, min_width=520):
            with gr.Group(elem_classes=["panel-card", "prediction-card"]):
                gr.HTML(section_heading(
                    "2",
                    "Predicted next text",
                    "The AI predicts possible next text and assigns how likely that text is.",
                ))
                probability_chart = gr.HTML(
                    empty_probability_chart_html(),
                    elem_id="probability-chart",
                )

        with gr.Column(scale=3, min_width=360):
            with gr.Group(elem_classes=["panel-card", "choice-card"]):
                gr.HTML(section_heading(
                    "3",
                    "You choose what comes next and test the Generative AI again",
                    "Choose one option. It is added to the input text, then the AI predicts again.",
                ))
                token_choice_html = gr.HTML(
                    empty_token_choices_html(),
                    elem_id="token-choice-html",
                )
                selection_bridge = gr.Textbox(
                    value="",
                    label="selection bridge",
                    elem_id="token-selection-bridge",
                    elem_classes=["selection-bridge"],
                )

    with gr.Row(elem_classes=["history-control-row"]):
        history_show_btn = gr.Button(
            "View generation history",
            variant="secondary",
            elem_id="history-show-btn",
        )

    with gr.Group(visible=False, elem_classes=["history-panel"]) as history_panel:
        with gr.Row(equal_height=True, elem_classes=["history-heading-row"]):
            gr.HTML(
                '<div class="history-heading">'
                '<b>Generation history</b>'
                '<span>This updates as you continue choosing text.</span>'
                '</div>'
            )
            history_hide_btn = gr.Button(
                "Hide history",
                size="sm",
                elem_id="history-hide-btn",
            )
        step_log_table = gr.Dataframe(
            headers=["Choice", "Chosen text", "Probability", "Text before choice"],
            label=None,
            visible=True,
            interactive=False,
            elem_id="step-log-table",
        )

    original_prompt_state = gr.State("")
    context_state = gr.State("")
    choice_state = gr.State(0)
    step_log_state = gr.State([])
    top_k_state = gr.State(DEFAULT_TOP_K)
    token_texts_state = gr.State([])

    demo.load(
        fn=None,
        inputs=None,
        outputs=None,
        js=r"""
        () => {
          if (window.__qut001LlmChoiceBridgeInstalled) return;
          window.__qut001LlmChoiceBridgeInstalled = true;

          document.addEventListener("click", (event) => {
            const bubble = event.target.closest("[data-token-index]");
            if (!bubble) return;

            event.preventDefault();
            const input = document.querySelector(
              "#token-selection-bridge input, #token-selection-bridge textarea"
            );
            if (!input) return;

            const value = bubble.dataset.tokenIndex + ":" + Date.now();
            const proto = input.tagName === "TEXTAREA"
              ? window.HTMLTextAreaElement.prototype
              : window.HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, "value").set;
            setter.call(input, value);
            input.dispatchEvent(new Event("input", {bubbles: true}));
            input.dispatchEvent(new Event("change", {bubbles: true}));
          }, true);
        }
        """
    )

    advanced_info_btn.click(
        fn=show_advanced_help,
        inputs=[prompt_input, context_state],
        outputs=[
            advanced_help_modal,
            token_choice_html,
            start_btn,
            stop_btn,
            reset_btn,
            prompt_input,
            top_k_input,
            step_label,
        ],
    )
    advanced_close_btn.click(
        fn=hide_advanced_help,
        inputs=None,
        outputs=advanced_help_modal,
    )

    history_show_btn.click(
        fn=show_history,
        inputs=[step_log_state],
        outputs=[history_panel, step_log_table],
    )
    history_hide_btn.click(
        fn=hide_history,
        inputs=None,
        outputs=history_panel,
    )

    common_outputs = [
        probability_chart,
        token_choice_html,
        status_html,
        step_label,
        start_btn, stop_btn, reset_btn,
        prompt_input, top_k_input,
        original_prompt_state, context_state, choice_state,
        step_log_state, top_k_state, token_texts_state,
        step_log_table,
    ]

    start_btn.click(
        fn=on_start,
        concurrency_limit=INFERENCE_CONCURRENCY,
        concurrency_id="llm_inference",
        inputs=[prompt_input, top_k_input],
        outputs=common_outputs,
    )

    selection_bridge.change(
        fn=on_choose,
        concurrency_limit=INFERENCE_CONCURRENCY,
        concurrency_id="llm_inference",
        inputs=[
            selection_bridge,
            original_prompt_state, context_state, choice_state,
            step_log_state, top_k_state, token_texts_state,
        ],
        outputs=common_outputs,
    )

    stop_btn.click(
        fn=on_stop,
        inputs=[context_state],
        outputs=[
            token_choice_html,
            start_btn, stop_btn, reset_btn,
            prompt_input, top_k_input,
            step_label,
        ],
    )

    reset_btn.click(
        fn=on_reset,
        inputs=None,
        outputs=common_outputs,
    )

    gr.HTML(footer_html())


if __name__ == "__main__":
    print("Loading Qwen model once at application startup...")
    load_model()
    print("Model loaded. Starting Gradio server.")

    demo.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7870,
        css=CSS,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="orange",
            neutral_hue="slate",
        ),
    )
