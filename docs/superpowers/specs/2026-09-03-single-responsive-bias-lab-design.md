# Single Responsive Bias Lab — Design Spec

- **Date:** 2026-09-03
- **Status:** Approved design, awaiting implementation plan
- **Scope:** `apps/bias_lab_responsive.py` (transform in place), with a throwaway freeze generator

## 1. Background

The QUT001 "Zylometry Lab" teaching simulation currently exists as three files:

| File | Role | State |
|------|------|-------|
| `apps/bias_lab.py` | Original v33 app (full Walkthrough UI, port 7860, `share=True`) | tracked, keep untouched |
| `apps/qut001_bias_lab.py` | Near-identical copy (7-line launch-block diff: port 7861, no share) | untracked, keep as redundant copy |
| `apps/bias_lab_responsive.py` | "Responsive" wrapper that patches `bias_lab.py`'s source at runtime | untracked, transform |

The responsive wrapper achieves its laptop-first, classroom-safe presentation by
**reading `bias_lab.py` as a text file and `exec`-ing the rewritten source**:

1. `_source_overrides()` is spliced before the original UI marker, redefining the
   presentation helpers so the existing callbacks pick up the new look.
2. The "applicant pool exhausted" banner is replaced with a modal.
3. Mission 5 is regex-replaced with a custom two-option repair screen.
4. The old title/subtitle header is removed and `demo.load(js=PAGE_PROGRESS_JS)`
   is injected to install the page-progress pill and click bridge.
5. `_harden_runtime_source_for_kubernetes()` rewrites the four animated callbacks
   from `def`→`async def` and `time.sleep()`→`await asyncio.sleep()` for
   classroom-concurrent load, asserting at startup that the rewrite succeeded.
6. The patched string is `exec(compile(...))`-ed into a fresh module namespace.

This mechanism is fragile (tightly coupled to `bias_lab.py`'s exact source text)
and opaque. The goal is to keep the *result* — the responsive presentation — while
removing the runtime source-patching entirely.

## 2. Goal

A single, **self-contained** responsive bias-lab app: one normal `.py` file that
contains the simulation mechanics *and* the responsive presentation as literal
code, with **no runtime `exec`/`read_text`/`compile`/string-patching**.

Success criteria:

- The responsive app no longer reads, patches, or `exec`s `bias_lab.py` at any time.
- The app is **hub-discoverable**: module-level `demo`, `CSS`, and metadata, so
  `hub.discover_apps()` loads it instead of reporting it broken.
- The app remains runnable **standalone** on port 7862 with the existing CLI.
- Student-visible behavior, timing, and state are unchanged from today.

## 3. Non-goals

- Do **not** delete or modify `apps/bias_lab.py` or `apps/qut001_bias_lab.py`
  (the redundant copy is deliberately kept).
- Do **not** refactor the simulation into separate modules (that is a possible
  follow-up, not this change).
- Do **not** keep the freeze generator in the repo. The point is to decouple
  from `bias_lab.py` going forward, not to regenerate automatically.

## 4. Target design

### 4.1 File layout

- Transform `apps/bias_lab_responsive.py` **in place** into the frozen,
  self-contained responsive app (same filename, new contents).
- `apps/bias_lab.py` and `apps/qut001_bias_lab.py` remain untouched.

### 4.2 Contents of the frozen file

The frozen file is produced by running the existing patch pipeline once and
materializing its output. Its structure:

1. **Module docstring** — states this is the frozen, self-contained responsive
   variant and no longer reads `bias_lab.py`.
2. **Imports** — everything the frozen body needs (`time`, `asyncio`, `html`,
   `numpy`, `pandas`, `gradio`, `sklearn`, plus `argparse`/`os` for the launcher).
   `re`, `types`, and `base64` are not needed by the frozen body.
3. **Frozen body** — the fully-patched source as literal code: simulation, data,
   responsive helpers, Mission-5 repair screen, news-alert modal, header removal,
   `demo.load(js=PAGE_PROGRESS_JS)` hook, and async-hardened callbacks.
4. **Combined CSS** — a single module-level `CSS = <original app CSS> + <EXTRA_CSS>`
   (the wrapper's `EXTRA_CSS` blocks are concatenated in). `hub._discover_css`
   reads module-level `CSS`, so this flows into `gr.mount_gradio_app(css=...)`.
5. **`demo` export** — module-level `demo` (already produced by the
   `with gr.Blocks(...) as demo:` block in the frozen source).
6. **Metadata** — module-level `TITLE`, `DESCRIPTION`, `SLUG`, `ORDER` for the hub
   (defaults below, adjustable).
7. **Module-level `demo.queue(...)`** — called with env-var defaults
   (`QUT001_CONCURRENCY`=64, `QUT001_QUEUE_SIZE`=500) so the classroom-safe
   concurrency applies under hub-mounting, not only under `__main__`.
   `max_threads` and `state_session_capacity` are `launch()`-only parameters and
   remain `__main__`-only (they have no meaning under hub-mounting).
8. **`__main__` launcher** — keeps the existing CLI (`--host`, `--port`=7862,
   `--root-path`, `--share`, `--concurrency`, `--queue-size`, `--max-threads`,
   `--state-session-capacity`), overriding queue settings before `demo.launch`.

### 4.3 Removals

- Delete all patching machinery: `_source_overrides`, `_load_patched_app`,
  `_harden_runtime_source_for_kubernetes`, the regex/string replacements, and the
  `types.ModuleType`/`exec`/`compile`/`read_text` calls.
- Delete the vestigial `QUT_LOGO_PATH` / `QUT_LOGO_B64` / `import base64`. The
  QUT logo ships as a static `background-image:url("data:image/png;base64,...")`
  blob inside the CSS, so this code is dead.

### 4.4 Proposed metadata defaults

```python
TITLE = "QUT001 Zylometry Lab (Responsive)"
DESCRIPTION = "Compact, laptop-first hiring-AI simulation."
SLUG = "bias-lab-responsive"
ORDER = 100
```

## 5. Production method

A **one-off throwaway generator** (run locally, not committed) executes today's
pipeline and writes the frozen file:

1. Read `apps/bias_lab.py`.
2. Apply, in order: `_source_overrides()` injection → news-alert modal replacement
   → Mission-5 replacement → Mission-7 handling → header removal → `demo.load`
   hook injection → `_harden_runtime_source_for_kubernetes()`.
3. Write the resulting source to `apps/bias_lab_responsive.py`, appending the
   combined `CSS`, metadata, module-level `demo.queue(...)`, and the `__main__`
   launcher.

The generator is derived from the current `_load_patched_app` + `__main__` code;
it is discarded after the frozen file is committed. The frozen file is thereafter
edited directly as a normal app.

## 6. Verification

1. **Static** — grep the frozen file for `exec`, `compile`, `read_text`,
   `_load_patched_app`, `_harden_runtime_source_for_kubernetes`, `types.ModuleType`,
   and `with_name`: all absent.
2. **Import** — `import apps.bias_lab_responsive` succeeds; `demo`, `CSS`,
   `TITLE`, `DESCRIPTION`, `SLUG`, `ORDER` all present.
3. **Hub** — boot the hub; `apps_bias_lab_responsive` loads (no longer listed
   broken); `GET /bias-lab-responsive/` returns 200 and serves the responsive CSS.
4. **Standalone** — launch on 7862; page returns 200; CLI flags still work.
5. **Behavior spot-check** — the async callbacks are still `async def` and contain
   `await asyncio.sleep(...)` (no blocking `time.sleep` in animated callbacks).

## 7. Risks & trade-offs

- **Monolithic file** — the frozen app is ~3,500 lines. Accepted for this change;
   splitting into modules is a possible future refactor, not this change.
- **Decoupling means no automatic tracking** — future edits to `bias_lab.py` will
   *not* propagate to the responsive app. This is intentional and desirable.
- **Hub now shows three Zylometry variants** — `bias-lab`, `qut001-bias-lab`, and
   `bias-lab-responsive`. Accepted per "keep redundant copy"; the responsive one is
   the primary entry point going forward.
- **Queue config under hub-mount** — module-level `demo.queue(...)` ensures
   concurrency defaults apply when mounted; verified in step 3 of Verification.
