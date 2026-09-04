# LLM Demo Input-Box Shows Only the Original Prompt — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In `apps/llm_demo.py`, make the input text box (`prompt_input`) show only the student's **original prompt** at all times — it must stop mirroring the growing generation context — and reword Section 1's subtitle so the copy matches the new behaviour.

**Architecture:** Three callbacks currently write the growing context into `prompt_input`: `on_choose` (both choice branches, `value=new_context`), `on_stop` (`value=context`), and `show_advanced_help` (`value=active_text`). Each switches to writing `original_prompt` instead. Two of those callbacks then no longer need a parameter they previously used only to build that value: `on_stop` drops `context` and takes `original_prompt`; `show_advanced_help` drops `context` and keeps only `prompt` (the box's current value — the original prompt). Their `.click` wiring is updated to match. `context_state` continues to grow exactly as before — only the textbox display changes — so the "Your generated text" readout under the activity is unaffected. Output tuple arities (15 / 7 / 8) are unchanged.

**Tech Stack:** Python 3.12, Gradio 6, repo virtualenv at `.venv` (run every command with `.venv/bin/python`). No new dependencies. The model must NOT be loaded — `get_predictions` is stubbed in verification, exactly as in the previous plan (`docs/superpowers/plans/2026-09-04-llm-demo-generated-text-readout.md`).

**Spec:** Approved short design from the 2026-09-04 session (bounded change, no spec file). Reproduced in "Design Summary" below.

## Design Summary (approved)

1. `on_choose` — both branches that pushed `value=new_context` into the input box switch to `value=original_prompt` (locked (`interactive=False`) while generating; editable (`interactive=True`) at the max-choices end). The guard branch stays a no-op.
2. `on_stop` — becomes `on_stop(original_prompt)`; the input box shows the original prompt instead of the full context. Side benefit: pressing Predict after Stop no longer trips the 20-word limit warning (the box no longer holds a long context).
3. `show_advanced_help` — drops the now-unused `context` parameter; paused editing still starts from the prompt only (`value=prompt`, which is the box's current content).
4. **Copy (fixed):** Section 1 subtitle becomes exactly:
   `Start with some text. The AI's input keeps growing as you choose — watch the text build in the Generated text section below.`
   (The pipeline strip is untouched — it describes the model's internal input concept, which still grows with each choice.)

**Net effect:** the box = original prompt, always. The growing generation stays live in the "Your generated text" readout (Stop does not clear it — `on_stop` does not output to the readout).

## Global Constraints

- Only `apps/llm_demo.py` changes. Do not touch any other file.
- `prompt_input` must NEVER receive the generation context (no `value=new_context`, no `value=context`, no `value=active_text` anywhere in the file after this change).
- Output tuple arities stay exactly as today: `on_choose`/`on_start`/`on_reset` → 15 elements (via `common_outputs`), `on_stop` → 7, `show_advanced_help` → 8.
- `context_state` behaviour is unchanged: `on_start` seeds it with the raw prompt; choices append `context + token_text`; `on_reset` clears it. The "Your generated text" readout still receives the full `(original_prompt, context)` pair.
- `original_prompt_state` is passed root-mutated/raw (not `.strip()`-ed), exactly as today.
- Run everything with `.venv/bin/python` from repo root. Verification never loads the model.

---

### Task 1: Input box shows the original prompt; reword Section 1 subtitle (atomic)

**Files:**
- Modify: `apps/llm_demo.py`:
  - `on_choose` max-choices branch (currently line ~247)
  - `on_choose` happy-path branch (currently line ~262)
  - `on_stop` (currently line ~268–276)
  - `show_advanced_help` (currently line ~289–307)
  - `advanced_info_btn.click` inputs (currently line ~984–995)
  - `stop_btn.click` inputs (currently line ~1036–1043)
  - Section 1 subtitle string (in the `section_heading(...)` call for the input card, currently ~line 858)

**Interfaces:**
- Consumes: nothing new (existing `original_prompt_state`, `prompt_input`, `context_state`).
- Produces: `on_stop(original_prompt)`, `show_advanced_help(prompt)`; both `.click` handlers take the new argument lists; the readout logic is untouched.

This is one atomic change: after it, the file imports and all callback arities match their `.click` wiring.

- [ ] **Step 1: Fix `on_choose` — stop writing the context into the input box**

In the max-choices branch, change this line:

```python
            gr.update(value=new_context, interactive=True), gr.update(interactive=True),
```

to:

```python
            gr.update(value=original_prompt, interactive=True), gr.update(interactive=True),
```

In the happy-path branch, change this line:

```python
        gr.update(value=new_context, interactive=False), gr.update(interactive=False),
```

to:

```python
        gr.update(value=original_prompt, interactive=False), gr.update(interactive=False),
```

No other part of `on_choose` changes (the guard branch already emits a no-op for the input box; `context_state`/readout outputs keep using `new_context`).

- [ ] **Step 2: Rewrite `on_stop` to take and show the original prompt**

Replace the whole function:

```python
def on_stop(context):
    return (
        empty_token_choices_html("Stopped. Predict again when you are ready."),
        gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
        gr.update(value=context, interactive=True), gr.update(interactive=True),
        gr.update(value="Stopped. Edit the input text or press Predict what comes next to continue.", visible=True),
    )
```

with:

```python
def on_stop(original_prompt):
    return (
        empty_token_choices_html("Stopped. Predict again when you are ready."),
        gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
        gr.update(value=original_prompt, interactive=True), gr.update(interactive=True),
        gr.update(value="Stopped. Edit the input text or press Predict what comes next to continue.", visible=True),
    )
```

- [ ] **Step 3: Rewrite `show_advanced_help` to drop the context parameter**

Replace the whole function:

```python
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
```

with:

```python
def show_advanced_help(prompt):
    """Open advanced settings and pause/unlock any active generation."""
    return (
        gr.update(visible=True),
        empty_token_choices_html(
            "Generation paused while you change Advanced parameters."
        ),
        gr.update(interactive=True),
        gr.update(interactive=False),
        gr.update(interactive=True),
        gr.update(value=prompt, interactive=True),
        gr.update(interactive=True),
        gr.update(value="Paused — change the setting, then predict again.", visible=True),
    )
```

- [ ] **Step 4: Update the click handlers' inputs**

`advanced_info_btn.click` currently passes `inputs=[prompt_input, context_state]`; change to `inputs=[prompt_input]`.

`stop_btn.click` currently passes `inputs=[context_state]`; change to `inputs=[original_prompt_state]`.

Do not change either handler's `outputs` list.

- [ ] **Step 5: Reword the Section 1 subtitle**

Find the input card's `section_heading` call:

```python
        gr.HTML(section_heading(
            "1",
            "Generative AI input text",
            "Start with some text. Every choice you make is added here and becomes the AI's new input.",
        ))
```

Change only the third argument to exactly:

```python
        gr.HTML(section_heading(
            "1",
            "Generative AI input text",
            "Start with some text. The AI's input keeps growing as you choose — watch the text build in the Generated text section below.",
        ))
```

- [ ] **Step 6: Verify callbacks with a stubbed model**

Run (repo root). `get_predictions` is stubbed so NO model is loaded:

```bash
.venv/bin/python - <<'PY'
import sys
sys.path.insert(0, "apps")
import llm_demo as m

m.get_predictions = lambda ctx, k: ([" it", " is", " a", " the", " of"], [0.5, 0.2, 0.1, 0.1, 0.1])
PROMPT = "Artificial intelligence can help us"

# on_start still puts the prompt into the box
o = m.on_start(PROMPT, 5)
assert len(o) == 15
assert o[7] == {"value": PROMPT, "interactive": False, "__type__": "update"} or o[7]["value"] == PROMPT

# on_choose happy path: box keeps the ORIGINAL prompt while context still grows
o2 = m.on_choose("0:1", PROMPT, PROMPT, 1, 5, [" it", " is", " a", " the", " of"])
assert len(o2) == 15
assert o2[7]["value"] == PROMPT            # input box: original prompt only
assert o2[7]["interactive"] is False
assert o2[10] == PROMPT + " it"            # context_state still grows
assert "generated-delta'> it</span>" in o2[14]["value"]  # readout still shows the append

# on_choose max-choices: box shows original prompt, editable
o3 = m.on_choose("0:1", "A", "A", 50, 5, [" it"])
assert len(o3) == 15
assert o3[7]["value"] == "A" and o3[7]["interactive"] is True

# on_stop: 7 outputs, box shows original prompt, editable
s = m.on_stop(PROMPT)
assert len(s) == 7
assert s[4]["value"] == PROMPT and s[4]["interactive"] is True

# show_advanced_help: 8 outputs, box shows its current content (the prompt)
h = m.show_advanced_help(PROMPT)
assert len(h) == 8
assert h[5]["value"] == PROMPT and h[5]["interactive"] is True

print("Task 1 callback verification OK")
PY
```

Expected: prints `Task 1 callback verification OK`, exits 0.

- [ ] **Step 7: Grep + compile + import**

```bash
grep -n "value=new_context\|value=context\|value=active_text\|def on_stop(context)\|def show_advanced_help(prompt, context)" apps/llm_demo.py || true
```

Expected: NO output (none of the old context-writing patterns remain).

```bash
grep -n "watch the text build in the Generated text section below" apps/llm_demo.py
.venv/bin/python -m py_compile apps/llm_demo.py
.venv/bin/python -c "import sys; sys.path.insert(0,'apps'); import llm_demo; print('import OK')"
```

Expected: the subtitle grep prints the section_heading line; `py_compile` silent; `import OK`.

- [ ] **Step 8: Commit**

```bash
git add apps/llm_demo.py
git commit -m "feat(apps): show only the original prompt in the input box"
```

---

### Task 2: End-to-end verification and cleanup

**Files:** none expected to change.

- [ ] **Step 1: Boot the hub and confirm the served page shows the new copy and not the old**

```bash
cd /home/ethan/teaching/qut001/qut001_gradio
.venv/bin/python -m uvicorn main:app --port 7871 --log-level warning &
APP_PID=$!
sleep 14
curl -s -L -o /tmp/llm_demo_input_page.html -w "HTTP %{http_code}\n" http://127.0.0.1:7871/llm-demo/
kill $APP_PID 2>/dev/null; wait $APP_PID 2>/dev/null || true
```

Expected: `HTTP 200`. Then (server already dead):

```bash
grep -c "watch the text build in the Generated text section below" /tmp/llm_demo_input_page.html
grep -c "Every choice you make is added here" /tmp/llm_demo_input_page.html || true
```

Expected: first grep ≥ 1 (new subtitle served); second grep prints 0 (`|| true` swallows grep's non-zero).

- [ ] **Step 2: Final review — clean working tree**

```bash
cd /home/ethan/teaching/qut001/qut001_gradio
git status --short
git log --oneline -3
```

Expected: working tree clean (only the pre-existing untracked files `data/images/test.png`, `data/images/test.txt`, `pyrightconfig.json`); the Task 1 commit on top.