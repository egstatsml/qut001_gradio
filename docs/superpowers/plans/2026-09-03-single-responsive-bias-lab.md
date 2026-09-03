# Single Responsive Bias Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the runtime source-patching wrapper `apps/bias_lab_responsive.py` with a single self-contained responsive bias-lab app (no `exec`/`read_text`/`compile`/string-patching).

**Architecture:** A throwaway generator runs the existing patch pipeline once and materializes the fully-patched source into a normal Python file. The frozen file embeds the simulation, the responsive helpers, the combined CSS, hub metadata, and a standalone launcher.

**Tech Stack:** Python 3, Gradio 6, numpy/pandas/scikit-learn (already in `apps/bias_lab.py`); `.venv` at repo root.

**Spec:** `docs/superpowers/specs/2026-09-03-single-responsive-bias-lab-design.md` (the binding authority — read it first).

## Global Constraints

- Keep `apps/bias_lab.py` and `apps/qut001_bias_lab.py` **untouched**.
- Frozen file must contain **no** runtime `exec(`, `compile(`, `read_text`, `_load_patched_app`, `_harden_runtime_source_for_kubernetes`, `types.ModuleType`, or `with_name`.
- Module-level `demo`, `CSS`, and metadata `TITLE`/`DESCRIPTION`/`SLUG`/`ORDER` must exist.
- Module-level `demo.queue(default_concurrency_limit=..., max_size=...)` with env defaults `QUT001_CONCURRENCY=64`, `QUT001_QUEUE_SIZE=500`.
- `max_threads` / `state_session_capacity` are `launch()`-only and stay `__main__`-only.
- `__main__` launcher keeps the CLI: `--host`, `--port` (7862), `--root-path`, `--share`, `--concurrency`, `--queue-size`, `--max-threads`, `--state-session-capacity`.
- Drop vestigial `QUT_LOGO_B64` / `QUT_LOGO_PATH` / `import base64`.
- The freeze generator is throwaway: never `git add` it; delete it before the final commit.
- Run everything with `.venv/bin/python` (the repo virtualenv).

---

### Task 1: Expose the patch pipeline as `_build_patched_source()`

**Files:**
- Modify: `apps/bias_lab_responsive.py` (function `_load_patched_app`, currently lines ~1137–1348)

**Interfaces:**
- Consumes: nothing new (refactor only).
- Produces: `_build_patched_source() -> str` — returns the fully-patched source (bias_lab.py content + injected overrides + Mission-5/news-modal/header replacements + `demo.load` hook + async hardening), **without** executing it.

- [ ] **Step 1: Split the function**

In `apps/bias_lab_responsive.py`, change the function header and body boundaries so the source-building code lives in a new function. The mechanical edit is:

- Rename the existing `def _load_patched_app():` block's *first line* to introduce `def _build_patched_source() -> str:` and move everything that builds `source` into it, ending with `return source` right after `source = _harden_runtime_source_for_kubernetes(source)`.

Concretely, the current function starts:

```python
def _load_patched_app():
    source_path = Path(__file__).with_name('bias_lab.py')
    if not source_path.exists():
        raise FileNotFoundError(
            f"Could not find {source_path.name}. Put this file beside your original bias_lab.py."
        )
    source = source_path.read_text(encoding='utf-8')
    ...
```

and ends:

```python
    source = _harden_runtime_source_for_kubernetes(source)

    module = types.ModuleType('_qut001_bias_lab_compact_runtime')
    module.__file__ = str(source_path)
    module.__name__ = '_qut001_bias_lab_compact_runtime'
    module.PAGE_PROGRESS_JS = PAGE_PROGRESS_JS
    exec(compile(source, str(source_path), 'exec'), module.__dict__)
    return module
```

Replace those two boundaries so the result is:

```python
def _build_patched_source() -> str:
    source_path = Path(__file__).with_name('bias_lab.py')
    if not source_path.exists():
        raise FileNotFoundError(
            f"Could not find {source_path.name}. Put this file beside your original bias_lab.py."
        )
    source = source_path.read_text(encoding='utf-8')
    ...            # ALL existing replacement/rewrite statements stay here, verbatim
    source = _harden_runtime_source_for_kubernetes(source)
    return source


def _load_patched_app():
    source_path = Path(__file__).with_name('bias_lab.py')
    source = _build_patched_source()
    module = types.ModuleType('_qut001_bias_lab_compact_runtime')
    module.__file__ = str(source_path)
    module.__name__ = '_qut001_bias_lab_compact_runtime'
    module.PAGE_PROGRESS_JS = PAGE_PROGRESS_JS
    exec(compile(source, str(source_path), 'exec'), module.__dict__)
    return module
```

Do **not** alter any of the intermediate statements (the `ui_marker`, `old_event`, `mission5_pattern`, `mission7_pattern`, `header_pattern`, `main_marker`/`load_hook`, and `_harden_runtime_source_for_kubernetes` lines) — only relocate them inside the new function and add the `return source` / call.

- [ ] **Step 2: Verify import still works and the new function returns a string**

Run:

```bash
.venv/bin/python -c "
import apps.bias_lab_responsive as w
s = w._build_patched_source()
assert isinstance(s, str) and len(s) > 10000, len(s)
print('OK', len(s), 'chars')
"
```

Expected: `OK <large> chars` and no exception.

- [ ] **Step 3: Commit**

```bash
git add apps/bias_lab_responsive.py
git commit -m "refactor: expose _build_patched_source for freezing"
```

---

### Task 2: Freeze generator → self-contained app

**Files:**
- Create: `scripts/freeze_bias_lab_responsive.py` (throwaway — never committed)
- Modify: `apps/bias_lab_responsive.py` (overwritten by the generator's output)

**Interfaces:**
- Consumes: `apps.bias_lab_responsive._build_patched_source()`, `apps.bias_lab_responsive.PAGE_PROGRESS_JS`, `apps.bias_lab_responsive.EXTRA_CSS` (all from Task 1 / the current module).
- Produces: a self-contained `apps/bias_lab_responsive.py` with module-level `demo`, `CSS`, `PAGE_PROGRESS_JS`, `TITLE`, `DESCRIPTION`, `SLUG`, `ORDER`, module-level `demo.queue(...)`, and an `__main__` launcher.

- [ ] **Step 1: Write the generator**

`scripts/freeze_bias_lab_responsive.py`:

```python
"""Throwaway freeze generator. Run once, then delete (never committed)."""
from pathlib import Path

import apps.bias_lab_responsive as w

TARGET = Path(__file__).resolve().parent.parent / "apps" / "bias_lab_responsive.py"

# The fully-patched body, minus its original __main__ launch block.
source = w._build_patched_source()
main_marker = '\n\nif __name__ == "__main__":'
idx = source.rfind(main_marker)
if idx < 0:
    raise RuntimeError("Could not find the __main__ block to strip.")
source = source[:idx]  # keeps the injected demo.load(...) hook; drops the 7860/share launch

DOCSTRING = '''"""QUT001 Zylometry Lab - self-contained responsive variant.

Frozen from apps/bias_lab.py (v33) plus the responsive presentation layer.
This file no longer reads or patches bias_lab.py at runtime.
"""
'''

IMPORTS = '''import argparse
import os
'''

PAGE_PROGRESS = f'\n\nPAGE_PROGRESS_JS = r"""{w.PAGE_PROGRESS_JS}"""\n'

EXTRA = f'\n\nCSS += r"""{w.EXTRA_CSS}"""\n'

METADATA = '''

TITLE = "QUT001 Zylometry Lab (Responsive)"
DESCRIPTION = "Compact, laptop-first hiring-AI simulation."
SLUG = "bias-lab-responsive"
ORDER = 100
'''

QUEUE = '''

# Classroom-safe concurrency defaults apply under hub-mounting too.
demo.queue(
    default_concurrency_limit=int(os.getenv("QUT001_CONCURRENCY", "64")),
    max_size=int(os.getenv("QUT001_QUEUE_SIZE", "500")),
)
'''

LAUNCHER = '''

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7862)
    parser.add_argument("--root-path", default=os.getenv("GRADIO_ROOT_PATH") or None)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("QUT001_CONCURRENCY", "64")))
    parser.add_argument("--queue-size", type=int, default=int(os.getenv("QUT001_QUEUE_SIZE", "500")))
    parser.add_argument("--max-threads", type=int, default=int(os.getenv("QUT001_MAX_THREADS", "40")))
    parser.add_argument("--state-session-capacity", type=int, default=int(os.getenv("QUT001_STATE_SESSION_CAPACITY", "2000")))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.concurrency < 1:
        raise ValueError("--concurrency must be at least 1.")
    if args.queue_size < 1:
        raise ValueError("--queue-size must be at least 1.")
    if args.max_threads < 1:
        raise ValueError("--max-threads must be at least 1.")
    if args.state_session_capacity < 1:
        raise ValueError("--state-session-capacity must be at least 1.")
    demo.queue(max_size=args.queue_size, default_concurrency_limit=args.concurrency)
    demo.launch(
        css=CSS,
        server_name=args.host,
        server_port=args.port,
        root_path=args.root_path,
        share=args.share,
        max_threads=args.max_threads,
        state_session_capacity=args.state_session_capacity,
    )
'''

content = DOCSTRING + IMPORTS + PAGE_PROGRESS + source + EXTRA + METADATA + QUEUE + LAUNCHER
TARGET.write_text(content, encoding="utf-8")
print(f"Wrote {TARGET} ({len(content)} chars)")
```

- [ ] **Step 2: Run the generator**

```bash
.venv/bin/python scripts/freeze_bias_lab_responsive.py
```

Expected: prints `Wrote .../apps/bias_lab_responsive.py (<large> chars)`.

- [ ] **Step 3: Verify the frozen file imports and exposes the required names**

```bash
.venv/bin/python -c "
import apps.bias_lab_responsive as m
assert m.TITLE == 'QUT001 Zylometry Lab (Responsive)', m.TITLE
assert m.SLUG == 'bias-lab-responsive', m.SLUG
assert hasattr(m, 'demo') and hasattr(m, 'CSS')
print('OK', type(m.demo).__name__, len(m.CSS), 'css chars')
"
```

Expected: `OK Blocks <large> css chars`.

- [ ] **Step 4: Verify no patching machinery remains + async hardening survived**

```bash
grep -nE 'exec\(|compile\(|read_text|_load_patched_app|_harden_runtime_source_for_kubernetes|types\.ModuleType|with_name|import base64|QUT_LOGO_B64' apps/bias_lab_responsive.py
```

Expected: **no matches** (empty output, non-zero exit is fine).

```bash
grep -c 'await asyncio.sleep(' apps/bias_lab_responsive.py
! grep -q 'time.sleep(' apps/bias_lab_responsive.py && echo 'no blocking time.sleep' || echo 'BLOCKING SLEEP PRESENT'
```

Expected: a positive count (≥4) for `await asyncio.sleep(`, and `no blocking time.sleep`.

- [ ] **Step 5: Commit (generator stays untracked)**

```bash
git add apps/bias_lab_responsive.py
git commit -m "feat: freeze responsive bias lab into self-contained app"
```

---

### Task 3: End-to-end verification and cleanup

**Files:**
- Delete: `scripts/freeze_bias_lab_responsive.py` (throwaway)

**Interfaces:**
- Consumes: the frozen `apps/bias_lab_responsive.py` from Task 2.
- Produces: verified app + removed generator. **No commit** (verification only; the generator was never tracked).

- [ ] **Step 1: Boot the hub and confirm the app now loads**

```bash
.venv/bin/python -m uvicorn main:app --port 8792 > /tmp/qut_hub_verify.log 2>&1 &
for i in $(seq 1 90); do curl -sf -o /dev/null http://127.0.0.1:8792/healthz 2>/dev/null && break; sleep 1; done
curl -s http://127.0.0.1:8792/healthz
```

Expected: `{"status":"ok","apps_loaded":5,"apps_failed":0}` (the responsive app now loads; nothing fails).

- [ ] **Step 2: Confirm the responsive page serves its CSS**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8792/bias-lab-responsive/
curl -s http://127.0.0.1:8792/bias-lab-responsive/ | grep -c "qut-blue\|llm-hero\|page-progress"
```

Expected: `200` then a positive count.

- [ ] **Step 3: Kill the hub and smoke-test standalone launch**

```bash
kill %1 2>/dev/null; sleep 1
.venv/bin/python apps/bias_lab_responsive.py --port 7862 > /tmp/qut_standalone_verify.log 2>&1 &
for i in $(seq 1 90); do curl -sf -o /dev/null http://127.0.0.1:7862/ 2>/dev/null && break; sleep 1; done
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:7862/
kill %1 2>/dev/null
```

Expected: `200`.

- [ ] **Step 4: Remove the throwaway generator and confirm clean state**

```bash
rm scripts/freeze_bias_lab_responsive.py
git status --porcelain
```

Expected: `apps/bias_lab_responsive.py` no longer listed as modified/untracked beyond its committed state; the two frozen-out files (`apps/bias_lab.py`, `apps/qut001_bias_lab.py`) are untouched; `scripts/freeze_bias_lab_responsive.py` gone.
