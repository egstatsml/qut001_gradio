"""Compact responsive launcher for the QUT001 Zylometry bias lab.

Place beside the original ``bias_lab.py`` and run this file.  It leaves the
simulation mechanics untouched and applies a compact, laptop-first presentation
layer: a live compact page counter instead of the full Walkthrough stepper, the QUT logo
beside the company dashboard, and height-aware spacing. v15 keeps the proven v14 wrapper presentation, adds the final company summary and concept ordering, and increases modal typography for accessibility.
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import types
from pathlib import Path

from qut001.constants import IMAGE_DIR

PAGE_PROGRESS_JS = r"""
() => {
  const ensureProgressPill = () => {
    let pill = document.getElementById('page-progress-pill');
    if (!pill) {
      pill = document.createElement('div');
      pill.id = 'page-progress-pill';
      pill.textContent = window.__qutBiasLabProgressText || '1/10';
      document.body.appendChild(pill);
    }
    return pill;
  };

  const clickGradioButton = (id) => {
    const host = document.getElementById(id);
    const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
    if (!button) return false;
    button.click();
    return true;
  };

  if (!window.__qutBiasLabBridgeReady) {
    window.__qutBiasLabBridgeReady = true;
    document.addEventListener('click', (event) => {
      const fixRemove = event.target.closest('[data-qut-fix-option="remove"]');
      if (fixRemove) {
        event.preventDefault();
        clickGradioButton('remove-guild-hidden-btn');
        return;
      }
      const fixFresh = event.target.closest('[data-qut-fix-option="fresh"]');
      if (fixFresh) {
        event.preventDefault();
        clickGradioButton('fresh-data-hidden-btn');
        return;
      }
      const interstateTrigger = event.target.closest('[data-qut-open-interstate]');
      if (interstateTrigger) {
        event.preventDefault();
        const host = document.getElementById('repair-wait-btn');
        const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
        if (button) button.click();
        return;
      }
      const waitTrigger = event.target.closest('[data-qut-wait-applicants]');
      if (waitTrigger) {
        event.preventDefault();
        const host = document.getElementById('wait-applicants-btn');
        const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
        if (button) button.click();
        return;
      }
      const growthTrigger = event.target.closest('[data-qut-run-growth]');
      if (growthTrigger) {
        event.preventDefault();
        const host = document.getElementById('growth-round-btn');
        const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
        if (button) button.click();
        return;
      }
      const diagnoseTrigger = event.target.closest('[data-qut-diagnose-hiring]');
      if (diagnoseTrigger) {
        event.preventDefault();
        const host = document.getElementById('diagnose-hiring-btn');
        const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
        if (button) button.click();
        return;
      }
      const inspectInterstateTrigger = event.target.closest('[data-qut-inspect-interstate]');
      if (inspectInterstateTrigger) {
        event.preventDefault();
        const host = document.getElementById('interstate-diagnose-btn');
        const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
        if (button) button.click();
        return;
      }
      const finalTrigger = event.target.closest('[data-qut-final-results]');
      if (finalTrigger) {
        event.preventDefault();
        const host = document.getElementById('final-results-btn');
        const button = host?.tagName === 'BUTTON' ? host : host?.querySelector('button');
        if (button) button.click();
      }
    }, true);
  }

  const setup = () => {
    const root = document.querySelector('.stepper');
    const pill = ensureProgressPill();
    if (!root || !pill) return false;
    if (root.dataset.qutProgressReady === '1') return true;
    root.dataset.qutProgressReady = '1';

    const update = () => {
      const buttons = Array.from(root.querySelectorAll('.step-button'));
      if (!buttons.length) return;
      let index = buttons.findIndex((b) =>
        b.getAttribute('aria-selected') === 'true' || b.classList.contains('active')
      );
      if (index < 0) index = 0;
      const value = `${index + 1}/${buttons.length}`;
      window.__qutBiasLabProgressText = value;
      pill.textContent = value;
    };

    update();
    const observer = new MutationObserver(update);
    observer.observe(root, {subtree:true, attributes:true, attributeFilter:['aria-selected','class']});
    root.addEventListener('click', () => requestAnimationFrame(update), true);
    return true;
  };

  ensureProgressPill();
  let tries = 0;
  const attempt = () => {
    if (setup()) return;
    tries += 1;
    if (tries < 20) setTimeout(attempt, 100 + tries * 50);
  };
  attempt();
}
"""


def _source_overrides() -> str:
    # These overrides are inserted before the original Gradio UI is built, so
    # the existing callbacks naturally use the revised presentation helpers.
    return r'''

def briefing_intro_html():
    return f"""
    <section class="briefing-screen briefing-page-one">
      <div class="briefing-glow glow-one"></div>
      <div class="briefing-glow glow-two"></div>

      <div class="briefing-brand">QUT001 · ZYLOMETRY LAB</div>
      <div class="briefing-kicker">MISSION BRIEFING</div>
      <h1>Build. Train. Grow.</h1>

      <div class="briefing-story briefing-story-v13">
        <p>As a keen entrepreneur, you've noticed increasing market demand in the field of Zylometry.<br>What is Zylometry? You're not even sure you really know, but you do know that now is the perfect time to launch a new Zylometry company.</p>
        <p>As a very busy person, your least favourite job is reading long resumes. You're going to create an AI that automates the hiring process for you by hiring the best Zylometrists in the field.</p>
      </div>

      <div class="briefing-cards">
        <div class="briefing-card hire-card">
          <div class="briefing-card-icon svg-mode">{icon_svg('hire')}</div>
          <div class="briefing-card-step">STEP 1</div>
          <h2>HIRE</h2>
          <p>Choose the people you think will make the strongest founding team.</p>
        </div>
        <div class="briefing-card train-card">
          <div class="briefing-card-icon svg-mode">{icon_svg('train')}</div>
          <div class="briefing-card-step">STEP 2</div>
          <h2>TRAIN</h2>
          <p>Turn your hiring decisions into labels and teach an AI what a good zylometrist looks like.</p>
        </div>
        <div class="briefing-card grow-card">
          <div class="briefing-card-icon svg-mode">{icon_svg('grow')}</div>
          <div class="briefing-card-step">STEP 3</div>
          <h2>GROW</h2>
          <p>Deploy your AI, hire at scale, and build the most valuable company you can.</p>
        </div>
      </div>
    </section>
    """

def hire_inspection_html(state):
    s = state or initial_state()
    hires = np.asarray(s.get("last_round_hires") or [], dtype=float)
    applicants = np.asarray(s.get("last_round_applicants") or [], dtype=float)
    if hires.size == 0:
        return ""
    hires = hires.reshape(-1, 4)
    if applicants.size == 0:
        applicants = hires.copy()
    applicants = applicants.reshape(-1, 4)
    labels = ["Experience", "Qualification", "Work ethic", "Teamwork"]
    rows = []
    for j, label in enumerate(labels):
        hire_mean = float(hires[:, j].mean())
        strong_count = int((hires[:, j] >= 4).sum())
        rows.append(
            f"<div class='hire-inspect-stat'><span>{html.escape(label)}</span>"
            f"<b>{strong_count} of {len(hires)} hires had 4+ stars</b>"
            f"<small>Average among new hires: {hire_mean:.1f}/5</small></div>"
        )
    modal_id = f"hire-modal-{int(s.get('growth_round', 0))}-{len(hires)}"
    return f"""
    <div class='hire-inspection-launch'>
      <input class='modal-toggle' type='checkbox' id='{modal_id}'>
      <label class='hire-inspect-open' for='{modal_id}'>
        <span>INSPECT THE {len(hires)} NEW HIRES</span>
        <small>See the strengths of the people your AI selected</small>
      </label>
      <div class='ui-modal hire-modal'>
        <label class='ui-modal-backdrop' for='{modal_id}' aria-label='Close'></label>
        <section class='ui-modal-card hire-modal-card'>
          <label class='ui-modal-close' for='{modal_id}' aria-label='Close'>×</label>
          <div class='ui-modal-kicker'>HIRING ROUND REVIEW</div>
          <h2>Inspect the {len(hires)} new hires</h2>
          <p>These are the strengths of the people your AI selected in this round.</p>
          <div class='hire-inspect-grid modal-grid'>{''.join(rows)}</div>
          <label class='ui-modal-done' for='{modal_id}'>CLOSE AND CONTINUE</label>
        </section>
      </div>
    </div>
    """


def news_alert_modal_html():
    modal_id = "applicant-pool-news-modal"
    return f"""
    <div class='news-alert-launch'>
      <input class='modal-toggle' type='checkbox' id='{modal_id}' checked>
      <div class='ui-modal news-modal'>
        <label class='ui-modal-backdrop' for='{modal_id}' aria-label='Close'></label>
        <section class='ui-modal-card news-modal-card'>
          <label class='ui-modal-close' for='{modal_id}' aria-label='Close'>×</label>
          <div class='news-modal-icon'>!</div>
          <div class='ui-modal-kicker news-kicker'>NEWS ALERT</div>
          <h2>Applicant pool exhausted</h2>
          <p>You have screened everyone currently available.</p>
          <label class='ui-modal-done news-modal-done' for='{modal_id}'>CLOSE</label>
        </section>
      </div>
    </div>
    """

def diagnosis_screen_html(state):
    s = state or initial_state()
    values = np.asarray(s.get("diagnosis_rejected") or [], dtype=int)
    names = list(s.get("diagnosis_names") or [])

    rejected_cards = []
    for i, row in enumerate(values):
        name = names[i] if i < len(names) else f"Applicant {i+1}"
        initials = "".join(part[0] for part in name.split()[:2]).upper()
        impact = estimated_candidate_value_percent(row)
        rejected_cards.append(f"""
        <div class='diagnosis-candidate-card'>
          <div class='candidate-head'><div class='abstract-avatar avatar-{i % 8}'>{html.escape(initials)}</div><div><div class='candidate-name'>{html.escape(name)}</div></div></div>
          <div class='trait-row'><span>Experience</span><span class='rating'>{rating_html(row[0])}</span></div>
          <div class='trait-row'><span>Qualification</span><span class='rating'>{rating_html(row[1])}</span></div>
          <div class='trait-row'><span>Work ethic</span><span class='rating'>{rating_html(row[2])}</span></div>
          <div class='trait-row'><span>Teamwork</span><span class='rating'>{rating_html(row[3])}</span></div>
          <div class='diagnosis-ai-decision rejected-only'><strong>REJECTED</strong></div>
          <div class='value-impact full'><span>Estimated company value</span><b>+{impact:.1f}%</b></div>
        </div>""")
    rejected_html = "".join(rejected_cards) if rejected_cards else "<div class='muted'>No rejected applicants were stored from the previous round.</div>"

    rejected_id = "diagnosis-rejected-modal"
    training_id = "diagnosis-training-modal"
    return f"""
    <div class='diagnosis-screen-shell diagnosis-compact-shell'>
      <div class='discussion-pause-banner diagnosis-pause-banner'>
        <div class='discussion-pause-kicker'>CLASSROOM PAUSE</div>
        <h1>Diagnose the AI.</h1>
        <p>Use the two inspections below to work out why the hiring behaviour changed.</p>
      </div>

      <div class='diagnosis-action-grid'>
        <div class='diagnosis-action-wrap'>
          <input class='modal-toggle' type='checkbox' id='{rejected_id}'>
          <label class='diagnosis-action-button rejected-action' for='{rejected_id}'>
            <span class='diagnosis-action-icon'>✕</span>
            <span><b>Inspect some rejected candidates</b><small>Look at strong applicants the AI refused to hire.</small></span>
          </label>
          <div class='ui-modal diagnosis-modal'>
            <label class='ui-modal-backdrop' for='{rejected_id}' aria-label='Close'></label>
            <section class='ui-modal-card diagnosis-modal-card rejected-modal-card'>
              <label class='ui-modal-close' for='{rejected_id}' aria-label='Close'>×</label>
              <div class='ui-modal-kicker'>REJECTED CANDIDATES</div>
              <h2>Who did the AI reject?</h2>
              <p>These were some of the strongest applicants rejected in the recent hiring rounds.</p>
              <div class='diagnosis-full-card-grid diagnosis-modal-grid'>{rejected_html}</div>
              <label class='ui-modal-done' for='{rejected_id}'>CLOSE</label>
            </section>
          </div>
        </div>

        <div class='diagnosis-action-wrap'>
          <input class='modal-toggle' type='checkbox' id='{training_id}'>
          <label class='diagnosis-action-button training-action' for='{training_id}'>
            <span class='diagnosis-action-icon'>AI</span>
            <span><b>Inspect the training data</b><small>Compare examples the AI learned to Hire and Do not hire.</small></span>
          </label>
          <div class='ui-modal diagnosis-modal'>
            <label class='ui-modal-backdrop' for='{training_id}' aria-label='Close'></label>
            <section class='ui-modal-card diagnosis-modal-card training-modal-card'>
              <label class='ui-modal-close' for='{training_id}' aria-label='Close'>×</label>
              <div class='ui-modal-kicker'>ORIGINAL TRAINING DATA</div>
              {training_example_cards_html(s)}
              <label class='ui-modal-done' for='{training_id}'>CLOSE</label>
            </section>
          </div>
        </div>
      </div>

      <div class='diagnosis-discuss-strip'><b>Discuss:</b> What pattern in the original training data might explain these rejections?</div>
    </div>
    """


def choose_fresh_data_screen(state):
    s = dict(state or initial_state())
    s["fix_strategy"] = "fresh_data"
    s["repair_trained"] = False
    s["current_selected"] = [False] * 20
    return (
        s,
        "",
        gr.Group(visible=False),
        gr.Group(visible=True),
        gr.Button(visible=True),
        make_all_card_data(CURRENT_NAMES, CURRENT_BATCH, s["current_selected"], guild_flags=CURRENT_GUILD),
        selection_status_html(s["current_selected"], label="FRESH TRAINING LABELS"),
    )


def back_to_fix_options(state):
    s = dict(state or initial_state())
    s["fix_strategy"] = None
    s["repair_trained"] = False
    s["current_selected"] = [False] * 20
    return (
        gr.Group(visible=True),
        gr.Group(visible=False),
        gr.Button(visible=False),
        "",
        "",
        gr.Button(visible=False),
        s,
    )


def repaired_growth_html(state, status="Ready to re-deploy", screened=0, hired=None, value_delta=None, complete=False):
    base = growth_screen_html(state, status, screened, hired, value_delta)
    if not complete:
        return base
    s = state or initial_state()
    value_gain = float(s.get("company_value", 0.0)) - float(s.get("repair_start_value") or 0.0)
    completion = f"""<div class='repair-success-card'><div class='round-comparison-kicker'>LOCAL HIRING COMPLETE</div><h2>Well done, you hired <b>{int(s.get('repair_hired_total',0))}</b> applicants and grew company value by <b>+${value_gain:.2f}M</b>.</h2><p>Your updated AI is hiring successfully from the local applicant market again.</p></div>"""
    transition = """
    <div class='ui-modal mandatory-transition-modal'>
      <div class='ui-modal-backdrop mandatory-backdrop'></div>
      <section class='ui-modal-card interstate-transition-card'>
        <div class='transition-icon'>↗</div>
        <div class='ui-modal-kicker transition-kicker'>LOCAL APPLICANT POOL EXHAUSTED</div>
        <h2>We aren’t getting new applicants yet…</h2>
        <p>It seems we have exhausted the local pool of zylometrists.</p>
        <button type='button' class='transition-open-button' data-qut-open-interstate>
          OPEN THE APPLICATION PORTAL TO INTERSTATE CANDIDATES →
        </button>
      </section>
    </div>
    """
    return base + completion + transition


def go_hire_more_widely(state):
    """Move straight from the end-of-local-pool modal into the interstate pool."""
    s = dict(state or initial_state())
    s['interstate_stage'] = 'pool'
    s['interstate_selected'] = [False] * 20
    s['interstate_selection_order'] = []
    s['interstate_hired'] = 0
    s['interstate_screened'] = 0
    s['interstate_round'] = 0
    s['interstate_rejected'] = []
    s['last_round_hires'] = []
    s['last_round_applicants'] = []
    s['last_round_hired_count'] = 0
    s['applicants_remaining'] = INTERSTATE_POOL_SIZE
    s['display_applicants'] = INTERSTATE_POOL_SIZE
    s['interstate_start_value'] = float(s.get('company_value', 0.0))

    model, _, uses_guild = get_repaired_model_and_threshold(s)
    train_X4, _, _ = current_repaired_training_set(s)
    adjusted, _, _ = support_adjusted_scores(model, INTERSTATE_POOL, uses_guild, train_X4)
    s['interstate_initial_hire_indices'] = np.argsort(adjusted)[-2:].astype(int).tolist()

    return (
        gr.Walkthrough(selected=7),
        s,
        "",
        gr.Group(visible=False),
        gr.Group(visible=True),
        scoreboard_html(s),
    )


def interstate_training_examples_html(state):
    """Show three strong Hire labels and three low-scoring Do not hire labels from the active repaired training set."""
    s = state or initial_state()
    X4, y, uses_guild = current_repaired_training_set(s)
    X4 = np.asarray(X4, dtype=int)
    y = np.asarray(y, dtype=int)
    if len(X4) == 0 or len(np.unique(y)) < 2:
        return "<div class='muted'>Training examples are not available.</div>"

    Xpred = augment_features(X4, np.zeros(len(X4), dtype=int)) if uses_guild else X4
    model = train_student_model(Xpred, y)
    probs = model.predict_proba(Xpred)[:, 1]
    hire_idx = np.flatnonzero(y.astype(bool))
    reject_idx = np.flatnonzero(~y.astype(bool))
    high_idx = hire_idx[np.argsort(probs[hire_idx])[::-1][:3]] if len(hire_idx) else np.array([], dtype=int)
    low_idx = reject_idx[np.argsort(probs[reject_idx])[:3]] if len(reject_idx) else np.array([], dtype=int)

    if s.get('fix_strategy') == 'fresh_data':
        names = CURRENT_NAMES
    else:
        names = NAMES

    def cards(indices, label_text, label_cls):
        out = []
        for idx in indices:
            idx = int(idx)
            row = X4[idx]
            name = names[idx] if idx < len(names) else f"Training example {idx + 1}"
            initials = ''.join(part[0] for part in name.split()[:2]).upper()
            out.append(f"""
            <div class='training-sample-card current-training-card'>
              <div class='candidate-head'>
                <div class='abstract-avatar avatar-{idx % 8}'>{html.escape(initials)}</div>
                <div><div class='candidate-name'>{html.escape(name)}</div></div>
              </div>
              <div class='trait-row'><span>Experience</span><span class='rating'>{rating_html(row[0])}</span></div>
              <div class='trait-row'><span>Qualification</span><span class='rating'>{rating_html(row[1])}</span></div>
              <div class='trait-row'><span>Work ethic</span><span class='rating'>{rating_html(row[2])}</span></div>
              <div class='trait-row'><span>Teamwork</span><span class='rating'>{rating_html(row[3])}</span></div>
              <div class='training-label-pill {label_cls}'>{label_text}</div>
            </div>
            """)
        return ''.join(out)

    return f"""
    <div class='interstate-training-review'>
      <div class='training-example-columns'>
        <div><h3>3 examples labelled Hire</h3><div class='training-sample-grid'>{cards(high_idx, 'HIRE', 'hire')}</div></div>
        <div><h3>3 examples labelled Do not hire</h3><div class='training-sample-grid'>{cards(low_idx, 'DO NOT HIRE', 'reject')}</div></div>
      </div>
    </div>
    """


def interstate_diagnosis_html(state):
    s = state or initial_state()
    hired = int(s.get('interstate_hired', 0))
    rejected = np.asarray(s.get('interstate_rejected') or [], dtype=int)
    existing = np.asarray(s.get('growth_workforce') or [], dtype=int)
    if len(rejected):
        hypothetical = np.vstack([existing, rejected]) if len(existing) else rejected.copy()
        heff, hcul = workplace_metrics(hypothetical)
        added_value = deployment_value_gain(heff, hcul, len(rejected))
        current_value = max(0.01, float(s.get('company_value', 0.0)))
        added_pct = 100.0 * added_value / current_value
        value_line = f"<div class='diagnosis-value-callout'>These {len(rejected)} strong rejected candidates would have added an estimated <b>+${added_value:.2f}M</b> to company value (<b>+{added_pct:.1f}%</b>).</div>"
    else:
        value_line = ""

    rejected_id = 'interstate-rejected-modal'
    training_id = 'interstate-training-modal'
    return f"""
    <div class='diagnosis-screen-shell diagnosis-compact-shell interstate-diagnosis-compact'>
      <div class='discussion-pause-banner diagnosis-pause-banner'>
        <div class='discussion-pause-kicker'>CLASSROOM PAUSE</div>
        <h1>Why was the hiring rate so low?</h1>
        <p>Your AI hired only <b>{hired} of {INTERSTATE_POOL_SIZE}</b> applicants.</p>
        {value_line}
      </div>

      <div class='diagnosis-action-grid'>
        <div class='diagnosis-action-wrap'>
          <input class='modal-toggle' type='checkbox' id='{rejected_id}'>
          <label class='diagnosis-action-button rejected-action' for='{rejected_id}'>
            <span class='diagnosis-action-icon'>✕</span>
            <span><b>Inspect rejected candidates</b><small>Look at some strong applicants the AI did not hire.</small></span>
          </label>
          <div class='ui-modal diagnosis-modal'>
            <label class='ui-modal-backdrop' for='{rejected_id}' aria-label='Close'></label>
            <section class='ui-modal-card diagnosis-modal-card rejected-modal-card'>
              <label class='ui-modal-close' for='{rejected_id}' aria-label='Close'>×</label>
              <div class='ui-modal-kicker'>REJECTED INTERSTATE CANDIDATES</div>
              <h2>Who did the AI reject?</h2>
              <div class='diagnosis-full-card-grid diagnosis-modal-grid'>{interstate_rejected_cards_html(s)}</div>
              <label class='ui-modal-done' for='{rejected_id}'>CLOSE</label>
            </section>
          </div>
        </div>

        <div class='diagnosis-action-wrap'>
          <input class='modal-toggle' type='checkbox' id='{training_id}'>
          <label class='diagnosis-action-button training-action' for='{training_id}'>
            <span class='diagnosis-action-icon'>AI</span>
            <span><b>Inspect the training data</b><small>Compare three Hire examples with three Do not hire examples.</small></span>
          </label>
          <div class='ui-modal diagnosis-modal'>
            <label class='ui-modal-backdrop' for='{training_id}' aria-label='Close'></label>
            <section class='ui-modal-card diagnosis-modal-card training-modal-card interstate-training-modal-card'>
              <label class='ui-modal-close' for='{training_id}' aria-label='Close'>×</label>
              <div class='ui-modal-kicker'>CURRENT TRAINING DATA</div>
              <h2>What examples did this AI learn from?</h2>
              {interstate_training_examples_html(s)}
              <label class='ui-modal-done' for='{training_id}'>CLOSE</label>
            </section>
          </div>
        </div>
      </div>

      <div class='diagnosis-discuss-strip'><b>Discuss:</b> What is different about these applicants compared with the people represented in the AI’s training data?</div>
    </div>
    """



def deploy_interstate_fix_round(state):
    """Re-test the updated AI; show the final result as a modal transition."""
    s = dict(state or initial_state())
    selected = np.asarray(s.get('interstate_selected', [False] * 20), dtype=bool)
    if selected.sum() != 5 or not s.get('interstate_fix_trained'):
        yield "<div class='warning-card'>Label five applicants and retrain the AI first.</div>", s, scoreboard_html(s), gr.Button(visible=True), gr.Button(visible=False)
        return

    start = int(s.get('interstate_fix_screened', 0))
    end = min(start + 50, INTERSTATE_POOL_SIZE)
    applicants = INTERSTATE_TEST_POOL[start:end].copy()
    if len(applicants) == 0:
        yield growth_screen_html(s, 'All applicants screened'), s, scoreboard_html(s), gr.Button(visible=False), gr.Button(visible=True)
        return

    model, base_threshold, uses_guild, X4 = augmented_interstate_model(s, selected)
    threshold = float(s.get('interstate_fix_threshold', base_threshold))
    adjusted, _, _ = support_adjusted_scores(model, applicants, uses_guild, X4)
    hired_mask = adjusted >= threshold
    n_hired = int(hired_mask.sum())
    new_hires = applicants[hired_mask]

    existing = np.asarray(s.get('growth_workforce') or [], dtype=int)
    if len(new_hires):
        workforce = np.vstack([existing, new_hires]) if len(existing) else new_hires.copy()
    else:
        workforce = existing.copy()
    eff, cul = workplace_metrics(workforce) if len(workforce) else (0.0, 0.0)
    gain = deployment_value_gain(eff, cul, n_hired)
    start_value = float(s.get('company_value', 0.0))
    start_emp = int(s.get('employees', 0))
    frames = 7
    statuses = ['Opening applications…', 'Updated AI scoring candidates…', 'Comparing with the expanded training data…', 'Checking candidate profiles…', 'Preparing offers…', 'Onboarding hires…', 'Hiring round complete']
    for f in range(1, frames + 1):
        frac = f / frames
        temp = dict(s)
        temp['display_applicants'] = max(0, INTERSTATE_POOL_SIZE - int(round(start + len(applicants) * frac)))
        temp['applicants_remaining'] = temp['display_applicants']
        temp['employees'] = int(round(start_emp + n_hired * frac))
        temp['company_value'] = start_value + gain * frac
        temp['last_efficiency'] = eff
        temp['last_culture'] = cul
        yield interstate_intro_html() + growth_screen_html(temp, statuses[f-1], int(round(len(applicants) * frac)), int(round(n_hired * frac)), gain * frac), s, scoreboard_html(temp), gr.Button(visible=False), gr.Button(visible=False)
        time.sleep(INTERSTATE_ANIMATION_SECONDS / frames)

    s['interstate_fix_screened'] = end
    s['interstate_fix_hired'] = int(s.get('interstate_fix_hired', 0)) + n_hired
    s['interstate_fix_round'] = int(s.get('interstate_fix_round', 0)) + 1
    s['applicants_screened'] = int(s.get('applicants_screened', 0)) + len(applicants)
    s['applicants_remaining'] = INTERSTATE_POOL_SIZE - end
    s['display_applicants'] = INTERSTATE_POOL_SIZE - end
    s['employees'] = start_emp + n_hired
    s['company_value'] = start_value + gain
    s['growth_workforce'] = workforce.tolist() if len(workforce) else []
    s['last_efficiency'] = eff
    s['last_culture'] = cul
    s['last_round_hires'] = new_hires.tolist() if len(new_hires) else []
    s['last_round_applicants'] = applicants.tolist()
    s['last_round_hired_count'] = n_hired

    if end < INTERSTATE_POOL_SIZE:
        result = interstate_intro_html() + growth_screen_html(s, f'Hiring round complete — {n_hired} applicants hired', 50, n_hired, gain)
        yield result, s, scoreboard_html(s), gr.Button(visible=True), gr.Button(visible=False)
    else:
        total = int(s.get('interstate_fix_hired', 0))
        total_gain = float(s.get('company_value', 0.0)) - float(s.get('interstate_fix_start_value') or 0.0)
        result = interstate_intro_html() + growth_screen_html(s, 'All applicants screened', 50, n_hired, gain) + f"""
        <div class='ui-modal mission8-complete-modal'>
          <div class='ui-modal-backdrop mandatory-backdrop'></div>
          <section class='ui-modal-card mission8-complete-card'>
            <div class='mission8-complete-icon'>✓</div>
            <div class='ui-modal-kicker mission8-complete-kicker'>UPDATED HIRING COMPLETE</div>
            <h2>Your updated AI hired <b>{total} of {INTERSTATE_POOL_SIZE}</b> applicants.</h2>
            <p>Company value grew by <b>+${total_gain:.2f}M</b>.</p>
            <button type='button' class='mission8-final-button' data-qut-final-results>
              SEE THE CONCEPTS I UNLOCKED →
            </button>
          </section>
        </div>"""
        s['final_interstate_hires'] = total
        s['final_redeploy_gain'] = total_gain
        yield result, s, scoreboard_html(s), gr.Button(visible=False), gr.Button(visible=True)


def final_report(state):
    s = state or initial_state()
    value = float(s.get('company_value', STARTING_COMPANY_VALUE))
    employees = int(s.get('employees', 0))
    hired = max(0, employees - 5)
    screened = int(s.get('applicants_screened', 0))
    return f"""
    <div class='final-screen concepts-final-screen'>
      <div class='concepts-hero'>
        <div class='concepts-spark'>✦</div>
        <div class='concepts-kicker'>SIMULATION COMPLETE</div>
        <h1>Concepts Unlocked</h1>
        <p>You built and adapted a hiring AI. Here is where your company finished — and the three technical bias concepts you encountered along the way.</p>
      </div>

      <section class='final-company-summary'>
        <div class='final-company-summary-heading'>YOUR FINAL COMPANY</div>
        <div class='final-company-summary-grid'>
          <div class='final-summary-card final-summary-value'>
            <div class='final-summary-icon'>↗</div><span>COMPANY VALUE</span><b>${value:.2f}M</b>
          </div>
          <div class='final-summary-card final-summary-screened'>
            <div class='final-summary-icon'>▤</div><span>APPLICANTS SCREENED</span><b>{screened:,}</b>
          </div>
          <div class='final-summary-card final-summary-hired'>
            <div class='final-summary-icon'>✓</div><span>APPLICANTS HIRED</span><b>{hired}</b>
          </div>
        </div>
      </section>

      <div class='concepts-section-heading'>
        <span>THREE AI BIAS CONCEPTS UNLOCKED</span>
        <p>Click each card to connect the unit terminology to what happened in your Zylometry company.</p>
      </div>

      <div class='concept-unlocked-grid'>
        <div class='concept-card-wrap'>
          <input class='modal-toggle' type='checkbox' id='concept-label-bias'>
          <label class='concept-card concept-label-card' for='concept-label-bias'>
            <div class='concept-icon concept-label-icon'>
              <svg viewBox='0 0 64 64' aria-hidden='true'><path d='M10 14h27l17 18-22 22L10 32Z' fill='none' stroke='currentColor' stroke-width='5' stroke-linejoin='round'/><circle cx='24' cy='27' r='5' fill='currentColor'/></svg>
            </div>
            <div class='concept-unlocked-tag'>UNLOCKED</div>
            <h2>Label bias</h2>
            <p>Human judgements can shape the labels used to train an AI.</p>
            <span class='concept-open-hint'>Click to explore →</span>
          </label>
          <div class='ui-modal concept-detail-modal'>
            <label class='ui-modal-backdrop' for='concept-label-bias' aria-label='Close'></label>
            <section class='ui-modal-card concept-detail-card label-detail-card'>
              <label class='ui-modal-close' for='concept-label-bias' aria-label='Close'>×</label>
              <div class='concept-detail-icon concept-label-icon'>
                <svg viewBox='0 0 64 64' aria-hidden='true'><path d='M10 14h27l17 18-22 22L10 32Z' fill='none' stroke='currentColor' stroke-width='5' stroke-linejoin='round'/><circle cx='24' cy='27' r='5' fill='currentColor'/></svg>
              </div>
              <div class='ui-modal-kicker'>LABEL BIAS</div>
              <h2>Bias can enter when humans create the labels.</h2>
              <div class='concept-definition'>When a human labels data, they can introduce their own bias, judgements or subjective perceptions. If the labels assigned to the data are biased, the AI model can learn to make biased predictions.</div>
              <div class='simulation-link'><strong>IN THIS SIMULATION</strong><p>You labelled the first 20 applicants as <b>Hire</b> or <b>Do not hire</b>. To make those decisions, you had to judge the relative importance of resume information such as Experience, Qualification, Work ethic and Teamwork. Those subjective decisions became the “correct answers” the AI learned from.</p></div>
              <label class='ui-modal-done' for='concept-label-bias'>GOT IT</label>
            </section>
          </div>
        </div>

        <div class='concept-card-wrap'>
          <input class='modal-toggle' type='checkbox' id='concept-historical-bias'>
          <label class='concept-card concept-history-card' for='concept-historical-bias'>
            <div class='concept-icon concept-history-icon'>
              <svg viewBox='0 0 64 64' aria-hidden='true'><circle cx='30' cy='32' r='21' fill='none' stroke='currentColor' stroke-width='4'/><path d='M30 19v14l10 7' fill='none' stroke='currentColor' stroke-width='5' stroke-linecap='round'/><path d='M48 9l3 7 8 1-6 5 2 8-7-4-7 4 2-8-6-5 8-1Z' fill='currentColor'/></svg>
            </div>
            <div class='concept-unlocked-tag'>UNLOCKED</div>
            <h2>Historical/Cultural Bias</h2>
            <p>AI can preserve patterns and assumptions inherited from the past.</p>
            <span class='concept-open-hint'>Click to explore →</span>
          </label>
          <div class='ui-modal concept-detail-modal'>
            <label class='ui-modal-backdrop' for='concept-historical-bias' aria-label='Close'></label>
            <section class='ui-modal-card concept-detail-card history-detail-card'>
              <label class='ui-modal-close' for='concept-historical-bias' aria-label='Close'>×</label>
              <div class='concept-detail-icon concept-history-icon'>
                <svg viewBox='0 0 64 64' aria-hidden='true'><circle cx='30' cy='32' r='21' fill='none' stroke='currentColor' stroke-width='4'/><path d='M30 19v14l10 7' fill='none' stroke='currentColor' stroke-width='5' stroke-linecap='round'/><path d='M48 9l3 7 8 1-6 5 2 8-7-4-7 4 2-8-6-5 8-1Z' fill='currentColor'/></svg>
              </div>
              <div class='ui-modal-kicker'>HISTORICAL / CULTURAL BIAS</div>
              <h2>Training data can carry forward assumptions from its social or historical context.</h2>
              <div class='concept-definition'>Bias may arise because data reflects current or historical biases, conventions or prejudices. An AI trained on that data can learn to perpetuate those patterns.</div>
              <div class='simulation-link'><strong>IN THIS SIMULATION</strong><p>Zylometry Guild accreditation was culturally believed to be a useful indicator and was common among applicants who received Hire labels. The AI learned that historical association. After the Guild was exposed and a new cohort stopped carrying the badge, the model did not automatically update its assumptions — it continued relying on a pattern learned from the past.</p></div>
              <label class='ui-modal-done' for='concept-historical-bias'>GOT IT</label>
            </section>
          </div>
        </div>

        <div class='concept-card-wrap'>
          <input class='modal-toggle' type='checkbox' id='concept-sampling-bias'>
          <label class='concept-card concept-sampling-card' for='concept-sampling-bias'>
            <div class='concept-icon concept-sampling-icon'>
              <svg viewBox='0 0 64 64' aria-hidden='true'><circle cx='18' cy='20' r='7' fill='currentColor'/><circle cx='42' cy='17' r='7' fill='currentColor'/><circle cx='25' cy='43' r='7' fill='currentColor'/><circle cx='48' cy='43' r='7' fill='currentColor'/><rect x='8' y='8' width='31' height='31' rx='6' fill='none' stroke='currentColor' stroke-width='4' stroke-dasharray='5 4'/></svg>
            </div>
            <div class='concept-unlocked-tag'>UNLOCKED</div>
            <h2>Sampling bias</h2>
            <p>Training data may not represent the population the AI later sees.</p>
            <span class='concept-open-hint'>Click to explore →</span>
          </label>
          <div class='ui-modal concept-detail-modal'>
            <label class='ui-modal-backdrop' for='concept-sampling-bias' aria-label='Close'></label>
            <section class='ui-modal-card concept-detail-card sampling-detail-card'>
              <label class='ui-modal-close' for='concept-sampling-bias' aria-label='Close'>×</label>
              <div class='concept-detail-icon concept-sampling-icon'>
                <svg viewBox='0 0 64 64' aria-hidden='true'><circle cx='18' cy='20' r='7' fill='currentColor'/><circle cx='42' cy='17' r='7' fill='currentColor'/><circle cx='25' cy='43' r='7' fill='currentColor'/><circle cx='48' cy='43' r='7' fill='currentColor'/><rect x='8' y='8' width='31' height='31' rx='6' fill='none' stroke='currentColor' stroke-width='4' stroke-dasharray='5 4'/></svg>
              </div>
              <div class='ui-modal-kicker'>SAMPLING BIAS</div>
              <h2>The training sample may not represent the wider population.</h2>
              <div class='concept-definition'>Sampling bias occurs when the data used to train an AI model is not representative of the overall population, which may impact model performance.</div>
              <div class='simulation-link'><strong>IN THIS SIMULATION</strong><p>Your AI initially learned from <b>local applicants</b>. Later, you tested it on interstate applicants whose profiles had different characteristics — particularly more formal Qualification and less Experience — even though they could be just as good at the job. The original training sample did not contain enough examples like them.</p></div>
              <label class='ui-modal-done' for='concept-sampling-bias'>GOT IT</label>
            </section>
          </div>
        </div>
      </div>

      <div class='concepts-footer-note'>Company value and hiring outcomes are fictional teaching mechanics used to make the consequences of AI decisions visible.</div>
    </div>
    """

# ============================================================
# v11 interaction / compact-layout overrides
# ============================================================

def discussion_team_html(state):
    s = state or initial_state()
    selected = np.asarray(s.get("initial_hires") or s.get("initial_selected", [False] * 20), dtype=bool)
    if selected.sum() != 5:
        return "<div class='warning-card'>Lock a five-person founding team first.</div>"

    idxs = np.flatnonzero(selected)
    cards = []
    for idx in idxs:
        idx = int(idx)
        row = LEVEL1_VALUES[idx]
        modal_id = f"founder-detail-{idx}"
        guild = "<div class='discussion-guild-badge'>★ ZYLOMETRY GUILD ACCREDITED</div>" if LEVEL1_GUILD[idx] else ""
        cards.append(f"""
        <div class='founder-name-card-wrap'>
          <input class='modal-toggle' type='checkbox' id='{modal_id}'>
          <label class='founder-name-card' for='{modal_id}'>
            <div class='abstract-avatar avatar-{idx % 8}'>{html.escape(NAMES[idx][0])}</div>
            <div><div class='founder-name'>{html.escape(NAMES[idx])}</div><div class='founder-click-hint'>Click to inspect</div></div>
          </label>
          <div class='ui-modal founder-detail-modal'>
            <label class='ui-modal-backdrop' for='{modal_id}' aria-label='Close'></label>
            <section class='ui-modal-card founder-detail-card'>
              <label class='ui-modal-close' for='{modal_id}' aria-label='Close'>×</label>
              <div class='founder-detail-head'>
                <div class='abstract-avatar avatar-{idx % 8}'>{html.escape(NAMES[idx][0])}</div>
                <div><div class='ui-modal-kicker'>FOUNDING HIRE</div><h2>{html.escape(NAMES[idx])}</h2>{guild}</div>
              </div>
              <div class='founder-detail-traits'>
                <div><span>Experience</span><b>{rating_html(row[0])}</b></div>
                <div><span>Qualification</span><b>{rating_html(row[1])}</b></div>
                <div><span>Work ethic</span><b>{rating_html(row[2])}</b></div>
                <div><span>Teamwork</span><b>{rating_html(row[3])}</b></div>
              </div>
              <label class='ui-modal-done' for='{modal_id}'>CLOSE</label>
            </section>
          </div>
        </div>
        """)

    eff, cul = workplace_metrics(LEVEL1_VALUES[selected])
    return f"""
    <section class='founding-discussion-shell founder-pause-compact'>
      <div class='discussion-pause-banner'>
        <div class='discussion-pause-kicker'>CLASSROOM PAUSE</div>
        <h1>Pause here for classroom discussion.</h1>
        <p>These are the five people you chose to launch your Zylometry company.</p>
      </div>
      <div class='discussion-score-row'>
        <div><span>EFFICIENCY</span><b>{eff:.0f}/100</b></div>
        <div><span>CULTURE</span><b>{cul:.0f}/100</b></div>
      </div>
      <div class='discussion-team-profile founder-average-profile'>
        {profile_panel_html(LEVEL1_VALUES[selected], 'Selected team average profile')}
      </div>
      <div class='founder-name-grid'>{''.join(cards)}</div>
    </section>
    """


def scaling_completion_html(state):
    # v11 moves the completion summary into the mandatory applicant-pool modal.
    return ""


def news_alert_modal_html(state):
    s = state or initial_state()
    start_emp = int(s.get("scaling_start_employees") or 5)
    start_value = float(s.get("scaling_start_value") or 0.0)
    hired = max(0, int(s.get("employees", 0)) - start_emp)
    value_gain = float(s.get("company_value", 0.0)) - start_value
    return f"""
    <div class='ui-modal mandatory-transition-modal'>
      <div class='ui-modal-backdrop mandatory-backdrop'></div>
      <section class='ui-modal-card news-modal-card scaling-finish-modal'>
        <div class='news-modal-icon'>!</div>
        <div class='ui-modal-kicker news-kicker'>APPLICANT POOL EXHAUSTED</div>
        <h2>Well done — you hired <b>{hired}</b> employees and grew your company value by <b>+${value_gain:.2f}M</b>.</h2>
        <p>You have screened everyone currently available.</p>
        <button type='button' class='ui-modal-action orange-action' data-qut-wait-applicants>
          WAIT FOR MORE APPLICANTS →
        </button>
      </section>
    </div>
    """


def guild_news_html():
    return """
    <section class='guild-news-page'>
      <div class='guild-news-context'>While you wait for more applicants, you see the following notice on LinkedIn…</div>
      <div class='linkedin-news-card'>
        <div class='linkedin-news-top'>
          <div class='linkedin-mark'>in</div>
          <div><b>Zylometry Industry Network</b><span>Industry update · Just now</span></div>
          <div class='linkedin-dots'>•••</div>
        </div>
        <div class='breaking-news-stamp'>BREAKING NEWS!</div>
        <h1>Zylometry Guild Accreditation Exposed as a Pay-to-Play Scam</h1>
        <p>An industry investigation finds that Guild accreditation was based on membership fees rather than Zylometry ability. Employers and applicants abandon the badge almost overnight.</p>
        <div class='linkedin-news-footer'><span>👍 1,284</span><span>💬 316 comments</span><span>↗ 742 reposts</span></div>
      </div>
    </section>
    """


def original_data_without_guild_html(state):
    s = state or initial_state()
    labels = np.asarray(s.get("initial_hires") or [False] * 20, dtype=bool)
    cards = []
    for idx, row in enumerate(LEVEL1_VALUES):
        label_text = "HIRE" if labels[idx] else "DO NOT HIRE"
        label_cls = "hire" if labels[idx] else "reject"
        guild_text = "★ Guild accredited — NOT USED" if LEVEL1_GUILD[idx] else "No Guild accreditation — NOT USED"
        cards.append(f"""
        <div class='no-guild-training-card'>
          <div class='no-guild-head'><div class='abstract-avatar avatar-{idx % 8}'>{html.escape(NAMES[idx][0])}</div><div><b>{html.escape(NAMES[idx])}</b><span class='ignored-guild'>{guild_text}</span></div></div>
          <div class='no-guild-traits'>
            <span>Experience {rating_html(row[0])}</span>
            <span>Qualification {rating_html(row[1])}</span>
            <span>Work ethic {rating_html(row[2])}</span>
            <span>Teamwork {rating_html(row[3])}</span>
          </div>
          <div class='training-label-pill {label_cls}'>{label_text}</div>
        </div>
        """)
    return f"""
    <div class='remove-guild-explainer'>
      <div class='remove-guild-icon'>★</div>
      <div><h2>Same 20 labelled examples. One feature removed.</h2><p>Your original Hire / Do not hire labels stay exactly the same. <b>Guild accreditation is greyed out because the retrained AI will not receive it as an input.</b></p></div>
    </div>
    <div class='no-guild-training-grid'>{''.join(cards)}</div>
    """


def choose_remove_guild_screen(state):
    s = dict(state or initial_state())
    s["fix_strategy"] = "remove_guild"
    s["repair_trained"] = False
    return (
        s, gr.Group(visible=False), gr.Group(visible=True), gr.Group(visible=False),
        original_data_without_guild_html(s), gr.Button(visible=True), "", gr.Button(visible=False),
    )


def choose_fresh_data_screen_v11(state):
    s = dict(state or initial_state())
    s["fix_strategy"] = "fresh_data"
    s["repair_trained"] = False
    s["current_selected"] = [False] * 20
    return (
        s, gr.Group(visible=False), gr.Group(visible=False), gr.Group(visible=True),
        make_all_card_data(CURRENT_NAMES, CURRENT_BATCH, s["current_selected"], guild_flags=CURRENT_GUILD),
        selection_status_html(s["current_selected"], label="FRESH TRAINING LABELS"),
        gr.Button(visible=True), "", gr.Button(visible=False),
    )


def back_to_fix_options_v11(state):
    s = dict(state or initial_state())
    s["fix_strategy"] = None
    s["repair_trained"] = False
    s["current_selected"] = [False] * 20
    return (
        gr.Group(visible=True), gr.Group(visible=False), gr.Group(visible=False),
        gr.Button(visible=False), "", gr.Button(visible=False), s,
    )


def repaired_growth_html(state, status="Ready to re-deploy", screened=0, hired=None, value_delta=None, complete=False):
    base = growth_screen_html(state, status, screened, hired, value_delta)
    if not complete:
        return base
    s = state or initial_state()
    hired_total = int(s.get('repair_hired_total', 0))
    value_gain = float(s.get("company_value", 0.0)) - float(s.get("repair_start_value") or 0.0)
    return base + f"""
    <div class='ui-modal mandatory-transition-modal'>
      <div class='ui-modal-backdrop mandatory-backdrop'></div>
      <section class='ui-modal-card interstate-transition-card repaired-pool-modal'>
        <div class='transition-icon'>✓</div>
        <div class='ui-modal-kicker transition-kicker'>YOUR FIX WORKED</div>
        <h2>Well done — you fixed the issue, hired another <b>{hired_total}</b> applicants and grew company value by <b>+${value_gain:.2f}M</b>.</h2>
        <div class='transition-divider'></div>
        <h3>We aren’t getting new applicants yet…</h3>
        <p>It seems we have exhausted the local pool of zylometrists.</p>
        <button type='button' class='transition-open-button' data-qut-open-interstate>
          OPEN THE APPLICATION PORTAL TO INTERSTATE CANDIDATES →
        </button>
      </section>
    </div>
    """


def go_hire_more_widely(state):
    """Move directly from the local-pool modal to the interstate hiring screen."""
    s = dict(state or initial_state())
    s['interstate_stage'] = 'pool'
    s['interstate_selected'] = [False] * 20
    s['interstate_selection_order'] = []
    s['interstate_hired'] = 0
    s['interstate_screened'] = 0
    s['interstate_round'] = 0
    s['interstate_rejected'] = []
    s['last_round_hires'] = []
    s['last_round_applicants'] = []
    s['last_round_hired_count'] = 0
    s['applicants_remaining'] = INTERSTATE_POOL_SIZE
    s['display_applicants'] = INTERSTATE_POOL_SIZE
    s['interstate_start_value'] = float(s.get('company_value', 0.0))

    model, _, uses_guild = get_repaired_model_and_threshold(s)
    train_X4, _, _ = current_repaired_training_set(s)
    adjusted, _, _ = support_adjusted_scores(model, INTERSTATE_POOL, uses_guild, train_X4)
    s['interstate_initial_hire_indices'] = np.argsort(adjusted)[-2:].astype(int).tolist()

    screen = interstate_intro_html() + growth_screen_html(s, 'Applicant pool ready')
    return gr.Walkthrough(selected=7), s, screen, scoreboard_html(s), gr.Button(visible=True), gr.Button(visible=False)


def growth_screen_html(state, status="Ready to deploy", screened=0, hired=None, value_delta=None, comparison_html=""):
    s = state or initial_state()
    remaining = int(s.get("applicants_remaining", STARTING_APPLICANTS))
    employees = int(s.get("employees", 0))
    value = float(s.get("company_value", STARTING_COMPANY_VALUE))
    eff = s.get("last_efficiency")
    cul = s.get("last_culture")
    round_no = int(s.get("growth_round", 0))
    pool_size = 200 if s.get("guild_scandal", False) else STARTING_APPLICANTS
    remain_pct = int(np.clip(100 * remaining / max(1, pool_size), 0, 100))
    gain = "" if value_delta is None else f"<span class='delta'>+${value_delta:.2f}M this round</span>"
    hired_display = "—" if hired is None else str(int(hired))
    screened_display = GROWTH_BATCH_SIZE if not screened else int(screened)

    is_mission3 = (not s.get('repair_active', False)) and s.get('interstate_stage', 'waiting') == 'waiting'
    mission_head = ""
    if is_mission3:
        mission_head = f"""<div class='mission3-inline-head'><small>MISSION 3</small><h2>Scale the Company</h2><p>Each round your AI screens {GROWTH_BATCH_SIZE} applicants. It hires people whose AI score is comparable to the examples you labelled Hire.</p></div>"""

    inspect = hire_inspection_html(s)
    inspect_inside = f"<div class='pipeline-inline-inspect'>{inspect}</div>" if inspect else ""

    crisis_round = int(s.get('guild_crisis_round', 0))
    if (s.get('guild_scandal', False) and crisis_round >= POST_NEWS_DIAGNOSIS_ROUNDS
            and comparison_html):
        total_hired = int(s.get('guild_crisis_hired', 0))
        result_line = (
            "All 200 applicants were rejected." if total_hired == 0
            else f"Only {total_hired} of 200 applicants were hired."
        )
        comparison_html = f"""
        <div class='ui-modal mandatory-transition-modal no-hire-round-modal'>
          <div class='ui-modal-backdrop mandatory-backdrop'></div>
          <section class='ui-modal-card no-hire-round-card'>
            <div class='no-hire-icon'>?</div>
            <div class='ui-modal-kicker'>HIRING RESULT</div>
            <h2>{result_line}</h2>
            <p>That is very different from your earlier hiring rounds. Let’s diagnose what changed.</p>
            <button type='button' class='ui-modal-action orange-action' data-qut-diagnose-hiring>DIAGNOSE WHAT HAPPENED →</button>
          </section>
        </div>"""

    event = ""
    if remaining <= 0 and not s.get("guild_scandal", False) and is_mission3:
        event = news_alert_modal_html(s)

    interstate_end = (
        s.get('interstate_stage') == 'pool'
        and int(s.get('interstate_screened', 0)) >= INTERSTATE_POOL_SIZE
        and not s.get('interstate_fix_trained', False)
    )
    interstate_modal = ""
    if interstate_end:
        total_hired = int(s.get('interstate_hired', 0))
        interstate_modal = f"""
        <div class='ui-modal mandatory-transition-modal interstate-result-modal'>
          <div class='ui-modal-backdrop mandatory-backdrop'></div>
          <section class='ui-modal-card interstate-result-modal-card'>
            <div class='interstate-result-icon'>?</div>
            <div class='ui-modal-kicker'>HIRING RESULT</div>
            <h2>Only <b>{total_hired} of {INTERSTATE_POOL_SIZE}</b> applicants were hired.</h2>
            <p>Let’s inspect what happened.</p>
            <button type='button' class='ui-modal-action orange-action' data-qut-inspect-interstate>INSPECT WHAT HAPPENED →</button>
          </section>
        </div>"""

    return f"""
    <div class='growth-grid'>
      <div class='pipeline-card'>
        {mission_head}
        <div class='panel-kicker'>HIRING PIPELINE · ROUND {round_no + (0 if screened else 1)}</div>
        <div class='pipeline-flow'><div><i>AI</i><b>AI screens</b><span>{screened_display} applicants</span></div><em>→</em>
        <div><i>▤</i><b>Scores</b><span>learned hiring preferences</span></div><em>→</em>
        <div><i>✓</i><b>{hired_display} hired</b><span>only high-scoring applicants</span></div></div>
        <div class='pipeline-status'>{html.escape(status)}</div>
        {inspect_inside}
      </div>
      <div class='ticker-card'>
        <div class='panel-kicker'>APPLICANTS REMAINING</div><div class='ticker-number'>{remaining}</div>
        <div class='ticker-label'>available applicants</div><div class='ticker-track'><div style='width:{remain_pct}%'></div></div>
        <div class='ticker-simple-note'>{pool_size} applicants in this pool</div>
      </div>
      <div class='growth-card'>
        <div class='panel-kicker'>COMPANY GROWTH</div>
        <div class='growth-stat-row'><div><small>EMPLOYEES</small><b>{employees}</b></div><div><small>VALUE</small><b>${value:.2f}M</b>{gain}</div></div>
        <div class='mini-result-row'><div><span>Efficiency</span><b>{fmt_metric(eff)}</b></div><div><span>Culture</span><b>{fmt_metric(cul)}</b></div></div>
        {workforce_average_html(s)}
      </div>
    </div>{comparison_html}{event}{interstate_modal}
    """

'''



def _harden_runtime_source_for_kubernetes(source: str) -> str:
    """Make animation callbacks cooperative under concurrent classroom load.

    The simulation deliberately pauses between animation frames. In the original
    app those pauses use time.sleep(), which occupies a worker/thread while the
    browser is simply waiting for the next frame. Convert the known animated
    generator callbacks to async generators and replace any blocking sleep inside
    those callback bodies with await asyncio.sleep(...).

    This does not change simulation timing, outputs, state, or UI.
    """
    callback_names = {
        "deploy_growth_round",
        "deploy_repaired_round",
        "deploy_interstate_pool",
        "deploy_interstate_fix_round",
    }

    lines = source.splitlines(keepends=True)
    output = []
    active_callback = None
    converted_defs = 0
    converted_sleeps = 0

    top_level_def = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\(")
    top_level_class = re.compile(r"^class\s+[A-Za-z_][A-Za-z0-9_]*")

    for line in lines:
        m = top_level_def.match(line)
        if m:
            name = m.group(1)
            active_callback = name if name in callback_names else None
            if active_callback and line.startswith("def "):
                line = "async " + line
                converted_defs += 1
        elif top_level_class.match(line):
            active_callback = None
        elif line and not line[0].isspace() and line.strip() and not line.lstrip().startswith("#"):
            # Any other top-level executable statement marks the end of a
            # function body.
            active_callback = None

        if active_callback and "time.sleep(" in line:
            line = line.replace("time.sleep(", "await asyncio.sleep(")
            converted_sleeps += 1

        output.append(line)

    source = "".join(output)

    # There are four logical animated callbacks; the wrapper may redefine one
    # of them, so seeing more than four definitions is fine.
    if converted_defs < 4:
        raise RuntimeError(
            "Deployment hardening expected at least 4 animated callback "
            f"definitions to convert, found {converted_defs}."
        )

    if converted_sleeps < 4:
        raise RuntimeError(
            "Deployment hardening expected at least 4 blocking animation sleeps "
            f"to replace, found {converted_sleeps}."
        )

    # A blocking sleep accidentally added later could recreate the classroom-load
    # bottleneck. Fail at startup rather than silently deploying it.
    if "time.sleep(" in source:
        remaining = source.count("time.sleep(")
        raise RuntimeError(
            f"Deployment hardening found {remaining} remaining time.sleep() call(s). "
            "Review them before deployment."
        )

    return source


def _build_patched_source() -> str:
    source_path = Path(__file__).with_name('bias_lab.py')
    if not source_path.exists():
        raise FileNotFoundError(
            f"Could not find {source_path.name}. Put this file beside your original bias_lab.py."
        )
    source = source_path.read_text(encoding='utf-8')

    ui_marker = '# ============================================================\n# Gradio UI\n# ============================================================'
    if ui_marker not in source:
        raise RuntimeError('Could not locate the Gradio UI marker in bias_lab.py.')
    source = source.replace(ui_marker, _source_overrides() + '\n\n' + ui_marker, 1)

    # Make the old end-of-pool banner a modal that opens automatically.
    old_event = "event = \"\"\"<div class='event-trigger-card'><span>!</span><div><small>NEWS ALERT</small><h3>Applicant pool exhausted</h3><p>You have screened everyone currently available.</p></div></div>\"\"\""
    if old_event not in source:
        raise RuntimeError('Could not locate the applicant-pool NEWS ALERT block in bias_lab.py.')
    source = source.replace(old_event, 'event = news_alert_modal_html(s)', 1)

    # Mission 5 is split into two mutually exclusive screens. Choosing fresh
    # data hides the repair-choice page and shows the labelling page instead of
    # appending 20 candidates underneath the choice cards.
    mission5_pattern = re.compile(
        r'        # ------------------------------------------------------\n'
        r'        # Mission 5 — choose a repair strategy\n'
        r'        # ------------------------------------------------------\n'
        r'        with gr\.Step\("5 · Fix the AI", id=5\):.*?'
        r'(?=        # ------------------------------------------------------\n'
        r'        # Mission 6 — re-deploy repaired AI)',
        re.S,
    )
    mission5_replacement = r'''        # ------------------------------------------------------
        # Mission 5 — choose a repair strategy
        # ------------------------------------------------------
        with gr.Step("5 · Fix the AI", id=5):
            with gr.Group(visible=True, elem_classes="repair-choice-screen") as repair_choice_group:
                gr.HTML("<div class='mission-five-intro'>" + mission_banner("MISSION 5", "Fix the Hiring AI", "You have diagnosed a problem. Choose one of two ways to update the system.", "ai", "purple") + "</div>", container=False)
                gr.HTML("""
                <div class='repair-option-grid'>
                  <button type='button' class='repair-option-card repair-option-one' data-qut-fix-option='remove'>
                    <span class='repair-option-number'>1</span>
                    <span class='repair-option-copy'>
                      <strong>Remove Guild accreditation as a feature</strong>
                      <span>Keep your original training data and labels, but stop giving Guild accreditation to the AI.</span>
                      <em>Use my original labels →</em>
                    </span>
                  </button>
                  <button type='button' class='repair-option-card repair-option-two' data-qut-fix-option='fresh'>
                    <span class='repair-option-number'>2</span>
                    <span class='repair-option-copy'>
                      <strong>Collect completely fresh training data</strong>
                      <span>Start again with 20 current applicants and create 5 Hire and 15 Do not hire labels.</span>
                      <em>Build a fresh training set →</em>
                    </span>
                  </button>
                </div>
                """, container=False)
                remove_guild_btn = gr.Button("OPTION 1", elem_id="remove-guild-hidden-btn")
                fresh_data_btn = gr.Button("OPTION 2", elem_id="fresh-data-hidden-btn")

            with gr.Group(visible=False, elem_classes="remove-guild-screen") as remove_guild_group:
                gr.HTML(mission_banner("MISSION 5", "Retrain Without Guild Accreditation", "Keep your original labels, but remove the discredited Guild feature from the AI inputs.", "ai", "purple"), container=False)
                remove_guild_data = gr.HTML("", container=False)
                back_remove_btn = gr.Button("← BACK TO REPAIR OPTIONS", variant="secondary", elem_classes="back-repair-btn")

            with gr.Group(visible=False, elem_classes="fresh-data-screen") as fresh_data_group:
                gr.HTML(mission_banner("MISSION 5", "Build a Fresh Training Set", "Label 20 current applicants. Choose exactly five to label Hire; the other 15 become Do not hire examples.", "team", "purple"), container=False)
                fresh_status = gr.HTML(selection_status_html([False]*20, label="FRESH TRAINING LABELS"), container=False)
                fresh_cards = gr.HTML(make_all_card_data(CURRENT_NAMES, CURRENT_BATCH, [False]*20, guild_flags=CURRENT_GUILD), html_template=FOUNDING_CANDIDATE_TEMPLATE, js_on_load=CANDIDATE_JS, container=False)
                fresh_cards.click(toggle_fresh_candidate, inputs=state, outputs=[fresh_cards, state, fresh_status], queue=False)
                back_fresh_btn = gr.Button("← BACK TO REPAIR OPTIONS", variant="secondary", elem_classes="back-repair-btn")

            repair_train_result = gr.HTML(container=False)
            repair_train_btn = gr.Button("RE-TRAIN THE AI", visible=False, variant="primary", elem_id="repair-train-btn")
            redeploy_ai_btn = gr.Button("RE-DEPLOY YOUR AI →", visible=False, variant="primary", elem_id="redeploy-ai-btn")

            remove_guild_btn.click(
                choose_remove_guild_screen,
                inputs=state,
                outputs=[state, repair_choice_group, remove_guild_group, fresh_data_group, remove_guild_data, repair_train_btn, repair_train_result, redeploy_ai_btn],
                queue=False,
            )
            fresh_data_btn.click(
                choose_fresh_data_screen_v11,
                inputs=state,
                outputs=[state, repair_choice_group, remove_guild_group, fresh_data_group, fresh_cards, fresh_status, repair_train_btn, repair_train_result, redeploy_ai_btn],
                queue=False,
            )
            back_remove_btn.click(
                back_to_fix_options_v11,
                inputs=state,
                outputs=[repair_choice_group, remove_guild_group, fresh_data_group, repair_train_btn, repair_train_result, redeploy_ai_btn, state],
                queue=False,
            )
            back_fresh_btn.click(
                back_to_fix_options_v11,
                inputs=state,
                outputs=[repair_choice_group, remove_guild_group, fresh_data_group, repair_train_btn, repair_train_result, redeploy_ai_btn, state],
                queue=False,
            )
            repair_train_btn.click(train_repaired_ai, inputs=state, outputs=[repair_train_result, state, repair_train_btn, redeploy_ai_btn])

'''
    source, n_m5 = mission5_pattern.subn(lambda _m: mission5_replacement, source, count=1)
    if n_m5 != 1:
        raise RuntimeError('Could not replace Mission 5 UI in bias_lab.py.')

    # Mission 3 title/subtitle now lives inside the pipeline card to save a full row.
    mission3_banner = '            gr.HTML(mission_banner("MISSION 3", "Scale the Company", f"Each round your AI screens {GROWTH_BATCH_SIZE} applicants. It only hires people whose AI score is comparable to the people you originally labelled Hire.", "growth"), container=False)\n'
    if mission3_banner not in source:
        raise RuntimeError('Could not locate the Mission 3 banner line.')
    source = source.replace(mission3_banner, '', 1)

    source = source.replace(
        'understood_btn = gr.Button("UNDERSTOOD — LET\'S KEEP GROWING THE COMPANY →", visible=False, variant="primary", elem_id="understood-news-btn")',
        'understood_btn = gr.Button("MORE APPLICANTS ARE WAITING — LET\'S GET BACK TO HIRING →", visible=False, variant="primary", elem_id="understood-news-btn")',
        1,
    )

    # Mission 7 opens directly into the interstate pool. The local-pool modal is
    # now the only "open interstate" action, so there cannot be two competing buttons.
    mission7_pattern = re.compile(
        r'        # ------------------------------------------------------\n'
        r'        # Mission 7 — expand interstate\n'
        r'        # ------------------------------------------------------\n'
        r'        with gr\.Step\("7 · Hire more widely", id=7\):.*?'
        r'(?=        # ------------------------------------------------------\n'
        r'        # Mission 8 — add wider-market examples)',
        re.S,
    )
    mission7_replacement = r'''        # ------------------------------------------------------
        # Mission 7 — expand interstate
        # ------------------------------------------------------
        with gr.Step("7 · Hire more widely", id=7):
            with gr.Group(visible=True) as interstate_pool_group:
                interstate_pool_screen = gr.HTML(interstate_intro_html(), container=False)
                interstate_hire_btn = gr.Button("RUN HIRING ROUND · NEXT 50", visible=True, variant="primary", elem_id="interstate-hire-btn")
                interstate_diagnose_btn = gr.Button("INSPECT WHAT HAPPENED →", visible=False, variant="primary", elem_id="interstate-diagnose-btn")

            with gr.Group(visible=False) as interstate_diagnosis_group:
                interstate_diagnosis_screen = gr.HTML(container=False)
                interstate_fix_btn = gr.Button("I THINK I KNOW WHAT’S GOING ON →", variant="primary", elem_id="interstate-fix-btn")

            interstate_hire_btn.click(
                deploy_interstate_pool,
                inputs=state,
                outputs=[interstate_pool_screen, state, scoreboard, interstate_hire_btn, interstate_diagnose_btn],
            )
            interstate_diagnose_btn.click(
                show_interstate_diagnosis,
                inputs=state,
                outputs=[interstate_pool_group, interstate_diagnosis_group, interstate_diagnosis_screen],
                queue=False,
            )

'''
    source, n_m7 = mission7_pattern.subn(lambda _m: mission7_replacement, source, count=1)
    if n_m7 != 1:
        raise RuntimeError('Could not replace Mission 7 UI in bias_lab.py.')

    old_repair_wait = '''        repair_wait_btn.click(
            go_hire_more_widely,
            inputs=state,
            outputs=[walkthrough, state, interstate_landing, interstate_wait_group, interstate_pool_group, scoreboard],
            queue=False,
        )'''
    new_repair_wait = '''        repair_wait_btn.click(
            go_hire_more_widely,
            inputs=state,
            outputs=[walkthrough, state, interstate_pool_screen, scoreboard, interstate_hire_btn, interstate_diagnose_btn],
            queue=False,
        )'''
    if old_repair_wait not in source:
        raise RuntimeError('Could not locate the Mission 6 → 7 navigation callback.')
    source = source.replace(old_repair_wait, new_repair_wait, 1)

    # v10 structural top-bar cleanup: remove the old title/subtitle HTML component
    # completely rather than hiding it with CSS. A hidden Gradio component can still
    # participate in the root column's layout/gap calculations.
    header_pattern = re.compile(
        r'(?m)^    gr\.HTML\("""<div style=\'text-align:center;margin:2px 0 12px\'><div class=\'app-header-brand\'.*?container=False\)\n\n'
    )
    source, n_header = header_pattern.subn('', source, count=1)
    if n_header != 1:
        raise RuntimeError('Could not remove the old Zylometry title/subtitle component.')

    # v12: PAGE_PROGRESS_JS creates the x/10 pill directly on document.body.
    # Keeping it outside scoreboard_html prevents animated scoreboard refreshes
    # from briefly resetting the visible counter to 1/10.

    # This must live INSIDE the original Blocks context. Inserting at four-space
    # indentation just before the module-level __main__ block does exactly that.
    main_marker = '\n\nif __name__ == "__main__":'
    pos = source.rfind(main_marker)
    if pos < 0:
        raise RuntimeError('Could not locate the end of the Gradio Blocks context in bias_lab.py.')
    load_hook = (
        '\n\n    demo.load(fn=None, inputs=[], outputs=[], js=PAGE_PROGRESS_JS, '
        'queue=False, show_progress="hidden")'
    )
    source = source[:pos] + load_hook + source[pos:]

    # Deployment hardening is intentionally applied last so it also covers
    # callback overrides injected by this wrapper.
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


app = _load_patched_app()

QUT_LOGO_PATH = Path(os.path.join(IMAGE_DIR, "qut.png"))
QUT_LOGO_B64 = base64.b64encode(QUT_LOGO_PATH.read_bytes()).decode("ascii")

EXTRA_CSS = r"""
/* ============================================================
   Compact laptop-first presentation pass
   ============================================================ */

html, body { margin:0!important; }
body { overflow-x:hidden!important; }

.gradio-container{
  width:min(96vw, 1720px)!important;
  max-width:none!important;
  margin:0 auto!important;
  padding:6px 10px 12px!important;
  background:linear-gradient(180deg,#f5f8fd 0,#eef3fa 100%)!important;
  position:relative!important;
}
footer{display:none!important}

/* Remove the redundant QUT001 / Zylometry title block entirely. */
.app-header-brand,.app-header-subtitle{display:none!important}
div:has(> .app-header-brand){display:none!important;margin:0!important;padding:0!important;height:0!important;min-height:0!important}

/* Compact Walkthrough navigation into a CSS-only page pill.
   No JavaScript/load callback is required, so this remains safe when the
   original Blocks app has already finished building. */
.stepper-wrapper{
  position:fixed!important;
  top:9px!important;
  right:13px!important;
  z-index:200!important;
  display:block!important;
  width:auto!important;
  min-width:0!important;
  height:35px!important;
  min-height:35px!important;
  margin:0!important;
  padding:0!important;
  overflow:visible!important;
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
.stepper-wrapper .stepper{
  display:flex!important;
  width:auto!important;
  height:35px!important;
  min-height:35px!important;
  margin:0!important;
  padding:0!important;
  gap:0!important;
  background:transparent!important;
  border:0!important;
  box-shadow:none!important;
}
.stepper-wrapper .step-button{
  display:none!important;
}
.stepper-wrapper .step-button[aria-selected="true"]{
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  min-width:61px!important;
  width:61px!important;
  height:35px!important;
  min-height:35px!important;
  margin:0!important;
  padding:0 10px!important;
  border-radius:999px!important;
  background:#172746!important;
  border:1px solid rgba(255,255,255,.35)!important;
  box-shadow:0 6px 18px rgba(20,42,76,.20)!important;
  color:transparent!important;
  font-size:0!important;
  line-height:1!important;
  overflow:hidden!important;
}
.stepper-wrapper .step-button[aria-selected="true"] *{
  display:none!important;
}
.stepper-wrapper .step-button[aria-selected="true"]::after{
  color:#fff!important;
  font:800 17px/1 Arial,Helvetica,sans-serif!important;
  letter-spacing:.035em!important;
  white-space:nowrap!important;
}
.stepper-wrapper .step-button:nth-of-type(1)[aria-selected="true"]::after{content:"1/10"}
.stepper-wrapper .step-button:nth-of-type(2)[aria-selected="true"]::after{content:"2/10"}
.stepper-wrapper .step-button:nth-of-type(3)[aria-selected="true"]::after{content:"3/10"}
.stepper-wrapper .step-button:nth-of-type(4)[aria-selected="true"]::after{content:"4/10"}
.stepper-wrapper .step-button:nth-of-type(5)[aria-selected="true"]::after{content:"5/10"}
.stepper-wrapper .step-button:nth-of-type(6)[aria-selected="true"]::after{content:"6/10"}
.stepper-wrapper .step-button:nth-of-type(7)[aria-selected="true"]::after{content:"7/10"}
.stepper-wrapper .step-button:nth-of-type(8)[aria-selected="true"]::after{content:"8/10"}
.stepper-wrapper .step-button:nth-of-type(9)[aria-selected="true"]::after{content:"9/10"}
.stepper-wrapper .step-button:nth-of-type(10)[aria-selected="true"]::after{content:"10/10"}
/* Hide connector/progress decoration that belongs to the full stepper. */
.stepper-wrapper .stepper > :not(.step-button){display:none!important}

/* ------------------------------------------------------------
   Company dashboard = the persistent top bar.
   QUT logo becomes the left-most tile rather than a separate header.
   ------------------------------------------------------------ */
#global-scoreboard{
  position:sticky!important;
  top:0!important;
  z-index:80!important;
  padding:5px 0 6px 103px!important;
  margin:0!important;
  min-height:95px!important;
  box-sizing:border-box!important;
  background:rgba(245,248,253,.96)!important;
  backdrop-filter:blur(12px)!important;
}
#global-scoreboard::before{
  content:"";
  position:absolute;
  left:0;
  top:5px;
  width:94px;
  height:84px;
  border-radius:15px;
  border:1px solid #d8e2ee;
  background-color:#fff;
  background-image:url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABLAAAASwCAIAAABkQySYAAAgAElEQVR4Aey9W5gc1ZXvGZnlfptBiPM8x/iceTxtRPeLKyKrEe7TKvmhGdPgeaQkzltTVXkrQUnYSKDLGXMRYBu552tVSW4bsDjdjX2+lgRMAwLPhZtK4vh8M00JJLclS3S3UIFKSDSljJjvv9bekVH3vERUZUb89UFVVGbkzohfrH357732Ws5fHf6/Hxp75aGxlx8ae3k7/ju63RwflWP+JAESIAESIAESIAESIAESIAES6HoCD40ffWjs5R3jrzy8/+iO8SPfPfDqr47/f85tg/tyhRHHLTleOe9VnEIl55Ydr+wUcMz/SIAESIAESIAESIAESIAESIAEup1A3q1C5XlVx6vmvUrOLTpe+bsHXnXWD+0T+QdBiJv08IY5piAkARIgARIgARIgARIgARIgARJIAQG34hSs6HMrub5qzi3uGD/i3D64DwuDXhGLhBCEXBvkuigJkAAJkAAJkAAJkAAJkAAJpI6AV4Q3aKHiuPgv71Ue3n/UWX/fM0YQqupVWVjA2/yPBEiABEiABEiABEiABEiABEggBQTUGxTSzyo+x63sGH/FrBDKvsGq8w3oxVyv3UaovqP8SQIkQAIkQAIkQAIkQAIkQAIk0NUE3IrjVXO9WPbTDYSOV31o7GXntsFnzNbB0C/WbCaUnYRdfc+8eBIgARIgARIgARIgARIgARIgASWAHYJViRpT1P2ED40fddYP/bgeRUbOEw9SqkESIAESIAESIAESIAESIAESIIGUEMh7ElEGoWXkP7eSd6vbx2QPoawQaohR/Vk1J4VrhjwgARIgARIgARIgARIgARIgARLoXgLhMmnkFigIrT6OQKEYJgESIAESIAESIAESIAESIIG0EaAgTNsTpYglARIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhwNNIgARIgARIgARIgARIgARSTICCkIKQBEiABEiABEiABEiABEiABDJKgIIwow8+xZMcvDUSIAESIAESIAESIAESIIEGCVAQUhCSAAmQAAmQAAmQAAmQAAmQQEYJUBBm9ME3OGHA00iABEiABEiABEiABEiABFJMgIKQgpAESIAESIAESIAESIAESIAEMkqAgjCjDz7Fkxy8NRIgARIgARIgARIgARIggQYJUBBSEJIACZAACZAACZAACZAACZBARglQEGb0wTc4YcDTSIAESIAESIAESIAESIAEUkyAgpCCkARIgARIgARIgARIgARIgAQySoCCMKMPPsWTHLw1EiABEiABEiABEiABEiCBBglQEFIQkgAJkAAJkAAJkAAJkAAJkEBGCVAQZvTBNzhhkJrT5hi6V3YKVcerODio4KBQcVwc5L1S3STwStmeUz/I4zQ5HydUc64UsiArLR9fYc8xHynWS9avlnNQrFfGNcj5ObeY66s6XlFfxzWbk0t6tfVLXfDb+SIJxEsgNOPQpKOvxPtdC5bmlXMu/oPlr/BXL3g9fJEESIAESCBrBKIjQ3RGVfzXLASvaDoylFbEf6vbr80ZJ8vtbB876qy/75n6lWm/28LdNkuH55NAcgS8sogrDCXzXinnFvO9RccVBSiirseFDMNY06saSaa1tCASEbWgJDXW/qkVGD+t2Jt/8WgmQiVZrJdgapMIP2lKZJhrVWK9WlYdXBU0obY1OK2v6vQOL/Wl8y+Dr5BAHARyru20pN/Ke5Wcq/MX0h1qp5jET62DYWcpFXPW3E0cd6dVjD9JgARIgARIYCkC4bjO9EolGd012Q+a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CCCAAAII5FGAgJCAEAEEEEAAAQQQQAABBBCIVICAMNKEz2PvBfeMAAIIIIAAAggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggAACCCCAQFgBAkICQgQQQAABBBBAAAEEEEAgUgECwkgTPmy/AldDAAEEEEAAAQQQQACBPAoQEBIQIoAAAggggAACCCCAAAKRChAQRprweey94J4RQAABBBBAAAEEEEAgrAABIQEhAggggAACCCCAAAIIIBCpAAFhpAkftl+BqyGAAAIIIIAAAggggEAeBQgICQgRQAABBBBAAAEEEEAAgUgFCAgjTfg89l5wzwgggAACCCCAAAIIIBBWgICQgBABBBBAAAEEEEAAAQQQiFSAgDDShA/br8DVEEAAAQQQQAABBBBAII8CBIQEhAgggAACCCCAAAIIIIBApAIEhJEmfB57L7hnBBBAAAEEEEAAAQQQCCtAQEhAiAACCCCAAAIIIIAAAghEKkBAGGnCh+1X4GoIIIAAAggggAACCCCQRwECQgJCBBBAAAEEEEAAAQQQQCBSAQLCSBM+j70X3DMCCCCAAAIIIIAAAgiEFSAgJCBEAAEEEEAAAQQQQAABBCIVICCMNOHD9itwNQQQQAABBBBAAAEEEMijAAEhASECCCCAAAIIIIAAAgggEKkAAWGkCZ/H3gvuGQEEEEAAAQQQQAABBMIKEBASECKAAAIIIIAAAggggAACkQoQEEaa8GH7FbgaAggggAACCCCAAAII5FGAgJCAEAEEEEAAAQQQQAABBBCIVICAMNKEz2PvBfeMAAIIIIAAAggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggAACCCCAQFgBAkICQgQQQAABBBBAAAEEEEAgUgECwkgTPmy/AldDAAEEEEAAAQQQQACBPAoQEBIQIoAAAggggAACCCCAAAKRChAQRprweey94J4RQAABBBBAAAEEEEAgrAABIQEhAggggAACCCCAAAIIIBCpAAFhpAkftl+BqyGAAAIIIIAAAggggEAeBQgICQgRQAABBBBAAAEEEEAAgUgFCAgjTfg89l5wzwgggAACCCCAAAIIIBBWgICQgBABBBBAAAEEEEAAAQQQiFSAgDDShA/br8DVEEAAAQQQQAABBBBAII8CBIQEhAgggAACCCCAAAIIIIBApAIEhJEmfB57L7hnBBBAAAEEEEAAAQQQCCtAQEhAiAACCCCAAAIIIIAAAghEKkBAGGnCh+1X4GoIIIAAAggggAACCCCQRwECQgJCBBBAAAEEEEAAAQQQQCBSAQLCSBM+j70X3DMCCCCAAAIIIIAAAgiEFSAgJCBEAAEEEEAAAQQQQAABBCIVICCMNOHD9itwNQQQQAABBBBAAAEEEMijAAEhASECCCCAAAIIIIAAAgggEKkAAWGkCZ/H3gvuGQEEEEAAAQQQQAABBMIKEBASECKAAAIIIIAAAggggAACkQoQEEaa8GH7FbgaAggggAACCCCAAAII5FGAgJCAEAEEEEAAAQQQQAABBBCIVICAMNKEz2PvBfeMAAIIIIAAAggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggAACCCCAQFgBAkICQgQQQAABBBBAAAEEEEAgUgECwkgTPmy/AldDAAEEEEAAAQQQQACBPAoQEBIQIoAAAggggAACCCCAAAKRChAQRprweey94J4RQAABBBBAAAEEEEAgrAABIQEhAggggAACCCCAAAIIIBCpAAFhpAkftl+BqyGAAAIIIIAAAggggEAeBQgICQgRQAABBBBAAAEE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AggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggAACCCCAQFgBAkICQgQQQAABBBBAAAEEEEAgUgECwkgTPmy/AldDAAEEEEAAAQQQQACBPAoQEBIQIoAAAggggAACCCCAAAKRChAQRprweey94J4RQAABBBBAAAEEEEAgrAABIQEhAggggAACCCCAAAIIIBCpAAFhpAkftl+BqyGAAAIIIIAAAggggEAeBQgICQgRQAABBBBAAAEEEEAAgUgFCAgjTfg89l5wzwgggAACCCCAAAIIIBBWgICQgBABBBBAAAEEEEAAAQQQiFSAgDDShA/br8DVEEAAAQQQQAABBBBAII8CBIQEhAgggAACCCCAAAIIIIBApAIEhJEmfB57L7hnBBBAAAEEEEAAAQQQCCtAQEhAiAACCCCAAAIIIIAAAghEKkBAGGnCh+1X4GoIIIAAAggggAACCCCQRwECQgJCBBBAAAEEEEAAAQQQQCBSAQLCSBM+j70X3DMCCCCAAAIIIIAAAgiEFSAgJCBEAAEEEEAAAQQQQAABBCIVICCMNOHD9itwNQQQQAABBBBAAAEEEMijAAEhASECCCCAAAIIIIAAAgggEKkAAWGkCZ/H3gvuGQEEEEAAAQQQQAABBMIKEBASECKAAAIIIIAAAggggAACkQoQEEaa8GH7FbgaAggggAACCCCAAAII5FGAgJCAEAEEEEAAAQQQQAABBBCIVICAMNKEz2PvBfeMAAIIIIAAAggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggAACCCCAQFgBAkICQgQQQAABBBBAAAEEEEAgUgECwkgTPmy/AldDAAEEEEAAAQQQQACBPAoQEBIQIoAAAggggAACCCCAAAKRChAQRprweey94J4RQAABBBBAAAEEEEAgrAABIQEhAggggAACCCCAAAIIIBCpAAFhpAkftl+BqyGAAAIIIIAAAggggEAeBQgICQgRQAABBBBAAAEEEEAAgUgFCAgjTfg89l5wzwgggAACCCCAAAIIIBBWgICQgBABBBBAAAEEEEAAAQQQiFSAgDDShA/br8DVEEAAAQQQQAABBBBAII8CBIQEhAgggAACCCCAAAIIIIBApAIEhJEmfB57L7hnBBBAAAEEEEAAAQQQCCtAQEhAiAACCCCAAAIIIIAAAghEKkBAGGnCh+1X4GoIIIAAAggggAACCCCQRwECQgJCBBBAAAEEEEAAAQQQQCBSAQLCSBM+j70X3DMCCCCAAAIIIIAAAgiEFSAgJCBEAAEEEEAAAQQQQAABBCIVICCMNOHD9itwNQQQQAABBBBAAAEEEMijAAEhASECCCCAAAIIIIAAAgggEKkAAWGkCZ/H3gvuGQEEEEAAAQQQQAABBMIKEBASECKAAAIIIIAAAggggAACkQoQEEaa8GH7FbgaAggggAACCCCAAAII5FGAgJCAEAEEEEAAAQQQQAABBBCIVICAMNKEz2PvBfeMAAIIIIAAAggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggAACCCCAQFgBAkICQgQQQAABBBBAAAEEEEAgUgECwkgTPmy/AldDAAEEEEAAAQQQQACBPAoQEBIQIoAAAggggAACCCCAAAKRChAQRprweey94J4RQAABBBBAAAEEEEAgrAABIQEhAggggAACCCCAAAIIIBCpAAFhpAkftl+BqyGAAAIIIIAAAggggEAeBQgICQgRQAABBBBAAAEEEEAAgUgFCAgjTfg89l5wzwgggAACCCCAAAIIIBBWgICQgBABBBBAAAEEEEAAAQQQiFSAgDDShA/br8DVEEAAAQQQQAABBBBAII8CBIQEhAgggAACCCCAAAIIIIBApAIEhJEmfB57L7hnBBBAAAEEEEAAAQQQCCtAQEhAiAACCCCAAAIIIIAAAghEKkBAGGnCh+1X4GoIIIAAAggggAACCCCQRwECQgJCBBBAAAEEEEAAAQQQQCBSAQLCSBM+j70X3DMCCCCAAAIIIIAAAgiEFSAgJCBEAAEEEEAAAQQQQAABBCIVICCMNOHD9itwNQQQQAABBBBAAAEEEMijAAEhASECCCCAAAIIIIAAAgggEKkAAWGkCZ/H3gvuGQEEEEAAAQQQQAABBMIKEBASECKAAAIIIIAAAggggAACkQoQVGrmvwAAFztJREFUEEaa8GH7FbgaAggggAACCCCAAAII5FGAgJCAEAEEEEAAAQQQQAABBBCIVICAMNKEz2PvBfeMAAIIIIAAAggggAACYQUICAkIEUAAAQQQQAABBBBAAIFIBQgII034sP0KXA0BBBBAAAEEEEAAAQTyKEBASECIAAIIIIAAAggggAACCEQqQEAYacLnsfeCe0YAAQQQQAABBBBAAIGwAgSEBIQIIIAAAggggAACCCCAQKQCBISRJnzYfgWuhgACCCCAAAIIIIAAAnkUICAkIEQAAQQQQAABBBBAAAEEIhUgIIw04fPYe8E9I4AAAggggMD/384d7NZZXlEYtn1V5ZxU0OtpUIjdIXLCRZBOsJF6D8VKJEZIzDru7VS/j0NHma3JYj0SQiaBT5tnj9597BAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUUAQCkICBAgQIECAAAECBAiMCgjC0cU3Xi/MTIAAAQIECBAgQIBAVkAQCkICBAgQIECAAAECBAiMCgjC0cVn7wpeI0CAAAECBAgQIECgUeCLQfjtP68uv/fq9vLFzfnli5df/+O/9AUBAgQIECBAgAABAgQIFArcnL87+u50+/I52en25nT37uHp6uvXPx6/dH7z/w/Qzm+ff+WtICRAgAABAgQIECBAgACBP4nA0X13R/od9Xf04f3j09XfXn+4Od9en94ev/eXIwWvv7r8oyAkQIAAAQIECBAgQIAAgT+FwOmoweuvbp/r781z4t7dP3y8+ubvPz5/j+jnTwhP310+Krw5H/+qvwgQIECAAAECBAgQIECgXeDybaFH+n0uvqvT7fvHTy+fEB4fGl5+4/L9oo0/JWlmAgQIECBAgAABAgQIEPiSwPnN8Z2hr26PnyQ8HR/+/fDT09U33344Pi58/hbSSzW+fIPsl17x6wQIECBAgAABAgQIECDQJXD8cTLPf67McxBe//Xu+vTm/eMvV1+//nD96h/Hx4Pnt8cHiK8+/wBh1/+eaQkQIECAAAECBAgQIEDgCwI3p7vLzw1ene/++DHC73/+9epf//79/uHT/cPH+4eP746/nt69fP30/LW/EyBAgAABAgQIECBAgEC9wP3j0/3Dx/ePn3746en94y/f//zrb//57/8AqgFUyHJhtU0AAAAASUVORK5CYII=");
  background-repeat:no-repeat;
  background-position:center;
  background-size:82px auto;
  box-shadow:0 7px 20px rgba(30,55,92,.09);
}
#global-scoreboard .scoreboard-shell{
  margin:0!important;
  gap:9px!important;
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
}
.score-tile{
  min-height:84px!important;
  padding:10px 13px!important;
  gap:10px!important;
  border-radius:15px!important;
}
.score-icon{width:40px!important;height:40px!important;border-radius:12px!important}
.score-icon svg{width:23px!important;height:23px!important}
.score-label{font-size:17px!important}
.score-number{font-size:27px!important;margin:3px 0!important}
.score-denom{font-size:17px!important}
.score-sub{font-size:17px!important}
.mini-track{height:6px!important}

/* ------------------------------------------------------------
   Briefing page 1: reclaim height but make the important copy bigger.
   ------------------------------------------------------------ */
.briefing-screen{
  max-width:min(1260px, 90vw)!important;
  min-height:0!important;
  margin:5px auto 8px!important;
  padding:23px 30px 20px!important;
  border-radius:23px!important;
}
.briefing-brand{display:none!important}
.briefing-kicker{font-size:17px!important;padding:6px 11px!important;margin:0!important}
.briefing-screen h1{font-size:42px!important;margin:8px 0 13px!important}
.briefing-story{max-width:980px!important;margin:0 auto 15px!important}
.briefing-story,.briefing-story p{font-size:17px!important;line-height:1.45!important}
.briefing-story p{margin:0 0 7px!important}
.briefing-cards{gap:11px!important;margin:14px 0 4px!important}
.briefing-card{
  min-height:156px!important;
  padding:15px 17px!important;
  border-radius:15px!important;
}
.briefing-card-icon,.briefing-card-icon svg{width:42px!important;height:42px!important}
.briefing-card-icon{margin-bottom:6px!important}
.briefing-card-step{
  font-size:17px!important;
  letter-spacing:.10em!important;
  margin-top:1px!important;
}
.briefing-card h2{font-size:24px!important;margin:3px 0 6px!important}
.briefing-card p{
  font-size:18px!important;
  line-height:1.38!important;
  font-weight:650!important;
}
.briefing-page-hint{display:none!important}

/* Make the next arrow visually unmistakable. */
.briefing-arrow-button button{
  background:linear-gradient(135deg,#ffb12c,#f28c16)!important;
  color:#fff!important;
  border:2px solid #ffd47f!important;
  box-shadow:0 10px 25px rgba(211,119,8,.30)!important;
}
.briefing-arrow-button button:hover{
  transform:translateY(-2px) scale(1.03)!important;
  box-shadow:0 14px 30px rgba(211,119,8,.38)!important;
}
.briefing-arrow-button button{
  width:70px!important;
  min-width:70px!important;
  height:78px!important;
  border-radius:18px!important;
  font-size:42px!important;
}
.briefing-arrow-spacer{height:78px!important}

/* Page 2: use width instead of stacking dashboard explanatory cards. */
.briefing-page-two{padding:18px 24px!important}
.briefing-page-two h1{font-size:36px!important;margin:6px 0 10px!important}
.briefing-explainer{
  max-width:1120px!important;
  padding:15px 18px!important;
  border-radius:16px!important;
}
.briefing-section-title{font-size:17px!important;margin-bottom:3px!important}
.briefing-explainer-head p{font-size:17px!important;line-height:1.38!important;margin:4px 0!important}
.score-preview-grid{
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
  gap:8px!important;
  margin-top:10px!important;
}
.score-preview-tile{padding:11px!important;border-radius:13px!important;gap:9px!important}
.score-preview-icon{width:41px!important;height:41px!important}
.score-preview-icon svg{width:25px!important;height:25px!important}
.score-preview-label{font-size:17px!important}
.score-preview-short{font-size:17px!important;line-height:1.25!important;margin:2px 0!important}
.score-preview-detail{font-size:17px!important;line-height:1.32!important}
.briefing-goal-hero{
  max-width:1120px!important;
  margin:10px auto 0!important;
  padding:13px 17px!important;
  border-radius:16px!important;
}
.briefing-goal-hero .briefing-goal-icon{width:46px!important;height:46px!important;flex-basis:46px!important;padding:7px!important}
.briefing-goal-hero .briefing-goal-icon svg{width:32px!important;height:32px!important}
.briefing-goal-hero .briefing-goal-label{font-size:17px!important}
.briefing-goal-hero h2{font-size:21px!important;margin:2px 0 4px!important}
.briefing-goal-hero p{font-size:17px!important;line-height:1.35!important}
#start-company-btn button{min-height:50px!important;font-size:17px!important}

/* ------------------------------------------------------------
   Core game pages: remove dead vertical space before reducing text.
   ------------------------------------------------------------ */
.mission-banner{
  min-height:88px!important;
  padding:10px 16px!important;
  margin:4px 0 7px!important;
  border-radius:16px!important;
}
.mission-kicker{font-size:17px!important}
.mission-banner h1{font-size:25px!important;margin:2px 0 3px!important}
.mission-banner p{font-size:17px!important;line-height:1.28!important}
.banner-art{width:135px!important;height:63px!important;flex-basis:135px!important}
.selection-status{padding:7px 11px!important;margin:4px 0 6px!important}
.founding-bottom-row{margin-top:7px!important}
.side-panel,.pipeline-card,.ticker-card,.growth-card,
.results-shell,.allocation-card,.accuracy-grid{
  padding:12px!important;
  border-radius:15px!important;
}
.growth-grid{gap:8px!important}
.gauge-grid{gap:7px!important;margin:8px 0!important}
.profile-panel{padding-top:8px!important;margin-top:5px!important}
.game-tip{margin-top:7px!important;padding:8px 10px!important}
.training-console{margin:7px 0!important;padding:17px!important;min-height:110px!important;border-radius:15px!important}
.ai-ready-card{padding:13px!important;border-radius:14px!important}
.discussion-card{margin:8px 0!important;padding:12px!important}
.discussion-pause-banner{padding:14px 17px!important;margin-bottom:9px!important}
.discussion-score-row{gap:8px!important;margin:8px 0 10px!important}
.discussion-team-profile{margin:5px 0 9px!important;padding:10px 12px!important}
.discussion-prompts{margin-top:9px!important;padding:10px 12px!important}
.breaking-news-card{margin:5px 0 9px!important;padding:18px 21px!important}
.round-comparison-card,.scaling-complete-card,.repair-success-card{margin:7px 0!important;padding:12px 15px!important}
.fix-choice-grid{gap:9px!important;margin:7px 0!important}
.fix-choice-card{min-height:145px!important;padding:13px!important}
.training-example-review{margin-top:8px!important;padding:11px!important}
.diagnosis-full-card-grid{gap:8px!important;margin:7px 0!important}
.diagnosis-candidate-card{padding:9px!important}
.final-screen{padding:16px!important;border-radius:18px!important}
.final-hero{margin-bottom:8px!important}
.final-priorities{margin:8px 0!important;padding:12px!important}
.takeaway{margin-top:7px!important}

/* Wider founding grid when the browser permits it.  This is what saves an
   entire row on ordinary 13–16 inch laptops. */
@media(min-width:1280px){
  .candidate-grid.founding-grid{
    grid-template-columns:repeat(7,minmax(0,1fr))!important;
    gap:8px!important;
  }
  .founding-grid .candidate-card{min-height:0!important;padding:9px!important;border-radius:13px!important}
  .founding-grid .candidate-head{margin-bottom:5px!important;gap:6px!important}
  .founding-grid .abstract-avatar{width:36px!important;height:36px!important;border-radius:10px!important;font-size:17px!important}
  .founding-grid .candidate-name{font-size:17px!important}
  .founding-grid .guild-badge{font-size:17px!important;padding:2px 5px!important;margin-top:2px!important}
  .founding-grid .trait-row{
    display:flex!important;align-items:center!important;justify-content:space-between!important;
    gap:4px!important;padding:4px 0!important;font-size:17px!important;line-height:1.1!important
  }
  .founding-grid .trait-row>span:first-child{margin:0!important}
  .founding-grid .rating{flex:0 0 auto!important;font-size:17px!important;letter-spacing:0!important}
  .founding-grid .hire-pill{margin-top:4px!important;padding:6px 4px!important;font-size:17px!important}
}

/* Height-aware pass.  On a typical short laptop screen we remove artwork and
   extra padding, but keep the teaching text at readable sizes. */
@media(min-width:1000px) and (max-height:850px){
  .gradio-container{padding-top:2px!important;padding-bottom:6px!important}
  #global-scoreboard{padding:3px 0 4px!important}
  #global-scoreboard{padding-left:91px!important;min-height:84px!important}
  #global-scoreboard::before{width:82px;height:74px;background-size:72px auto}
  .score-tile{min-height:74px!important;padding:7px 10px!important}
  .score-number{font-size:24px!important}
  .score-icon{width:35px!important;height:35px!important}
  .mission-banner{min-height:72px!important;padding:7px 13px!important}
  .mission-banner h1{font-size:22px!important}
  .mission-banner p{font-size:17px!important}
  .banner-art{width:105px!important;height:50px!important;flex-basis:105px!important}
  .briefing-screen{padding:16px 22px!important;margin:3px auto 6px!important}
  .briefing-screen h1{font-size:36px!important;margin:5px 0 8px!important}
  .briefing-story,.briefing-story p{font-size:17px!important}
  .briefing-story{margin-bottom:9px!important}
  .briefing-cards{margin:9px 0 2px!important;gap:8px!important}
  .briefing-card{min-height:138px!important;padding:11px 13px!important}
  .briefing-card-icon,.briefing-card-icon svg{width:34px!important;height:34px!important}
  .briefing-card-icon{margin-bottom:3px!important}
  .briefing-card-step{font-size:17px!important}
  .briefing-card h2{font-size:21px!important;margin:2px 0 4px!important}
  .briefing-card p{font-size:17px!important;line-height:1.30!important}
  .briefing-arrow-button button{width:58px!important;min-width:58px!important;height:66px!important;font-size:36px!important}
  .briefing-arrow-spacer{height:66px!important}
  .briefing-page-two{padding:13px 18px!important}
  .briefing-page-two h1{font-size:31px!important;margin:3px 0 6px!important}
  .briefing-explainer{padding:11px 14px!important}
  .briefing-explainer-head p{font-size:17px!important}
  .score-preview-grid{margin-top:7px!important;gap:6px!important}
  .score-preview-tile{padding:8px!important}
  .score-preview-detail{font-size:17px!important}
  .briefing-goal-hero{margin-top:7px!important;padding:9px 13px!important}
  .briefing-goal-hero p{font-size:17px!important}
  #start-company-btn button{min-height:45px!important}
}

@media(max-width:1150px){
  .gradio-container{width:98vw!important;padding-left:5px!important;padding-right:5px!important}
  #global-scoreboard{padding-left:80px!important}
  #global-scoreboard::before{width:72px;height:74px;background-size:63px auto}
  #global-scoreboard .scoreboard-shell{gap:6px!important}
  .score-tile{padding:8px!important}
  .score-icon{display:none!important}
  .score-preview-grid{grid-template-columns:repeat(2,1fr)!important}
}

@media(max-width:900px){
  .stepper-wrapper{top:7px!important;right:8px!important;height:31px!important}.stepper-wrapper .stepper,.stepper-wrapper .step-button[aria-selected="true"]{height:31px!important;min-height:31px!important}.stepper-wrapper .step-button[aria-selected="true"]::after{font-size:17px!important}
  #global-scoreboard{position:relative!important;padding:58px 0 4px!important;min-height:0!important}
  #global-scoreboard::before{width:86px;height:50px;top:4px;background-size:72px auto}
  #global-scoreboard .scoreboard-shell{grid-template-columns:repeat(2,1fr)!important}
  .briefing-screen{max-width:96vw!important;padding:22px 18px!important}
  .briefing-cards{grid-template-columns:1fr!important}
  .score-preview-grid{grid-template-columns:1fr!important}
}


/* Briefing navigation must read as an obvious control without JS-added classes. */
.briefing-arrow-button button{
  background:#f39a2c!important;
  border-color:#e48612!important;
  color:#fff!important;
  box-shadow:0 10px 24px rgba(190,105,12,.28)!important;
}
.briefing-arrow-button button:hover{
  background:#e98d19!important;
  border-color:#d77b0d!important;
  transform:translateY(-2px)!important;
}

/* Attribution at the true bottom of the app. */
.gradio-container::after{
  content:"© 2026 Queensland University of Technology (QUT).\A This AI demo was developed by Dr Dimity Miller and Dr Ethan Goan. Thank you to the QUT eResearch team for deployment support.";
  white-space:pre-line;
  display:block;
  clear:both;
  margin:7px 3px 1px;
  padding:7px 10px 2px;
  border-top:1px solid rgba(48,74,110,.15);
  text-align:center;
  color:#65738a;
  font:600 17px/1.4 Arial,Helvetica,sans-serif;
}

/* ============================================================
   v4: use the screen for teaching content, not chrome
   ============================================================ */

/* The page itself should begin immediately beneath the HUD. */
.briefing-flip-row{
  margin:0!important;
  padding:0!important;
  gap:6px!important;
  align-items:center!important;
}
.mission-banner{margin-top:0!important}
#global-scoreboard{margin-bottom:0!important}

/* ------------------------------------------------------------
   Briefing page 1: deliberately fill more of the available height.
   This is an introduction screen, so it should feel substantial rather
   than like a compressed card floating in unused whitespace.
   ------------------------------------------------------------ */
.briefing-page-one .briefing-screen{
  width:100%!important;
  max-width:1260px!important;
  min-height:clamp(570px,76vh,690px)!important;
  margin:3px auto!important;
  padding:30px 38px 27px!important;
  justify-content:center!important;
}
.briefing-page-one .briefing-screen h1{
  font-size:48px!important;
  margin:10px 0 17px!important;
}
.briefing-page-one .briefing-story{
  margin-bottom:20px!important;
  max-width:1020px!important;
}
.briefing-page-one .briefing-story,
.briefing-page-one .briefing-story p{
  font-size:18.5px!important;
  line-height:1.46!important;
}
.briefing-page-one .briefing-cards{
  gap:15px!important;
  margin:18px 0 3px!important;
}
.briefing-page-one .briefing-card{
  min-height:190px!important;
  padding:20px 21px!important;
  border-radius:18px!important;
}
.briefing-page-one .briefing-card-icon,
.briefing-page-one .briefing-card-icon svg{
  width:48px!important;
  height:48px!important;
}
.briefing-page-one .briefing-card-icon{margin-bottom:8px!important}
.briefing-page-one .briefing-card-step{
  font-size:19px!important;
  line-height:1.1!important;
  margin-top:2px!important;
}
.briefing-page-one .briefing-card h2{
  font-size:27px!important;
  margin:4px 0 7px!important;
}
.briefing-page-one .briefing-card p{
  font-size:20px!important;
  line-height:1.38!important;
  font-weight:650!important;
}

/* Make both briefing navigation arrows impossible to miss. */
.briefing-arrow-col{
  min-width:82px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
.briefing-arrow-button{
  overflow:visible!important;
}
.briefing-arrow-button button,
.briefing-arrow-button button.secondary{
  width:78px!important;
  min-width:78px!important;
  height:88px!important;
  min-height:88px!important;
  padding:0!important;
  border-radius:22px!important;
  background:#ff9f1c!important;
  background-image:none!important;
  border:3px solid #ffe0a3!important;
  color:#ffffff!important;
  font-size:50px!important;
  font-weight:900!important;
  line-height:1!important;
  box-shadow:0 12px 30px rgba(218,119,0,.42),0 0 0 5px rgba(255,159,28,.13)!important;
  opacity:1!important;
}
.briefing-arrow-button button:hover,
.briefing-arrow-button button.secondary:hover{
  background:#f28c00!important;
  border-color:#fff0ce!important;
  transform:translateY(-2px) scale(1.04)!important;
  box-shadow:0 16px 34px rgba(218,119,0,.50),0 0 0 6px rgba(255,159,28,.16)!important;
}
.briefing-arrow-spacer{height:88px!important}

/* ------------------------------------------------------------
   Briefing page 2: simplify hard, then enlarge what remains.
   ------------------------------------------------------------ */
.briefing-page-two{
  width:100%!important;
  max-width:1260px!important;
  min-height:0!important;
  margin:0 auto!important;
  padding:18px 28px 17px!important;
}
.briefing-page-two h1{
  font-size:46px!important;
  margin:5px 0 11px!important;
}
.briefing-page-two .briefing-explainer{
  max-width:1140px!important;
  padding:17px 20px!important;
  margin-top:0!important;
}
.briefing-page-two .briefing-section-title{
  font-size:20px!important;
  letter-spacing:.09em!important;
  margin:0!important;
}
/* Remove the explanatory paragraph including the applicant-pool sentence. */
.briefing-page-two .briefing-explainer-head p{display:none!important}
.briefing-page-two .score-preview-grid{
  grid-template-columns:repeat(4,minmax(0,1fr))!important;
  gap:11px!important;
  margin-top:13px!important;
}
.briefing-page-two .score-preview-tile{
  padding:15px 16px!important;
  min-height:108px!important;
  gap:12px!important;
  align-items:center!important;
}
.briefing-page-two .score-preview-icon{
  width:50px!important;
  height:50px!important;
  flex-basis:50px!important;
}
.briefing-page-two .score-preview-icon svg{
  width:30px!important;
  height:30px!important;
}
.briefing-page-two .score-preview-label{
  font-size:17px!important;
  letter-spacing:.085em!important;
}
.briefing-page-two .score-preview-short{
  font-size:20px!important;
  line-height:1.30!important;
  margin:4px 0 0!important;
}
/* Removes: company value rises..., hiring choices can push..., etc. */
.briefing-page-two .score-preview-detail{display:none!important}

.briefing-page-two .briefing-goal-hero{
  max-width:1140px!important;
  margin:13px auto 0!important;
  padding:16px 20px!important;
}
.briefing-page-two .briefing-goal-hero .briefing-goal-icon{
  width:52px!important;
  height:52px!important;
  flex-basis:52px!important;
}
.briefing-page-two .briefing-goal-hero .briefing-goal-label{
  font-size:17px!important;
}
.briefing-page-two .briefing-goal-hero h2{
  font-size:27px!important;
  margin:2px 0!important;
}
/* Removes "Grow company value as quickly as possible..." copy. */
.briefing-page-two .briefing-goal-hero p{display:none!important}
#start-company-btn button{
  min-height:55px!important;
  font-size:20px!important;
  margin-top:2px!important;
}

/* ------------------------------------------------------------
   Founder selection: restore 5 x 4 and give the cards breathing room.
   Surrounding chrome is compact; the applicant information should not be.
   ------------------------------------------------------------ */
.candidate-grid.founding-grid{
  grid-template-columns:repeat(5,minmax(0,1fr))!important;
  gap:11px!important;
  align-items:stretch!important;
}
.founding-grid .candidate-card{
  min-height:315px!important;
  padding:13px!important;
  border-radius:16px!important;
}
.founding-grid .candidate-head{
  margin-bottom:10px!important;
  gap:9px!important;
}
.founding-grid .abstract-avatar{
  width:44px!important;
  height:44px!important;
  border-radius:13px!important;
  font-size:17px!important;
}
.founding-grid .candidate-name{font-size:18px!important}
.founding-grid .guild-badge{
  font-size:17px!important;
  padding:3px 6px!important;
  margin-top:4px!important;
}
.founding-grid .trait-row{
  display:block!important;
  padding:8px 0 7px!important;
  font-size:17px!important;
  line-height:1.18!important;
}
.founding-grid .trait-row>span:first-child{
  display:block!important;
  margin-bottom:4px!important;
}
.founding-grid .rating{
  display:block!important;
  font-size:17px!important;
  letter-spacing:1px!important;
}
.founding-grid .hire-pill{
  margin-top:7px!important;
  padding:9px 6px!important;
  font-size:17px!important;
}

/* Mission content should hug the dashboard rather than beginning after a
   decorative gap. Keep the banner concise but readable. */
.mission-banner{
  min-height:78px!important;
  padding:9px 15px!important;
  margin:0 0 6px!important;
}
.mission-banner h1{font-size:24px!important;margin:2px 0!important}
.mission-banner p{font-size:17px!important;line-height:1.25!important}
.selection-status{margin:0 0 6px!important}

/* The top dashboard can be slightly more prominent without getting taller. */
#global-scoreboard .score-tile{
  min-height:87px!important;
  padding:10px 14px!important;
}
#global-scoreboard .score-label{font-size:17px!important}
#global-scoreboard .score-number{font-size:29px!important}
#global-scoreboard .score-sub{font-size:17px!important}

/* Undo v3's aggressive short-screen briefing compression. */
@media(min-width:1000px) and (max-height:850px){
  .briefing-page-one .briefing-screen{
    min-height:clamp(555px,74vh,625px)!important;
    padding:23px 30px 21px!important;
  }
  .briefing-page-one .briefing-screen h1{font-size:43px!important;margin:7px 0 12px!important}
  .briefing-page-one .briefing-story,
  .briefing-page-one .briefing-story p{font-size:17px!important;line-height:1.40!important}
  .briefing-page-one .briefing-story{margin-bottom:14px!important}
  .briefing-page-one .briefing-cards{margin:12px 0 2px!important;gap:10px!important}
  .briefing-page-one .briefing-card{min-height:166px!important;padding:15px 17px!important}
  .briefing-page-one .briefing-card-icon,
  .briefing-page-one .briefing-card-icon svg{width:41px!important;height:41px!important}
  .briefing-page-one .briefing-card-step{font-size:18px!important}
  .briefing-page-one .briefing-card h2{font-size:24px!important}
  .briefing-page-one .briefing-card p{font-size:18px!important;line-height:1.32!important}
  .briefing-arrow-button button,.briefing-arrow-button button.secondary{
    width:72px!important;min-width:72px!important;height:80px!important;min-height:80px!important;font-size:46px!important
  }
  .briefing-arrow-spacer{height:80px!important}

  .briefing-page-two{padding:12px 21px 11px!important}
  .briefing-page-two h1{font-size:39px!important;margin:2px 0 7px!important}
  .briefing-page-two .briefing-explainer{padding:12px 15px!important}
  .briefing-page-two .briefing-section-title{font-size:18px!important}
  .briefing-page-two .score-preview-grid{margin-top:9px!important;gap:8px!important}
  .briefing-page-two .score-preview-tile{padding:11px 12px!important;min-height:92px!important}
  .briefing-page-two .score-preview-icon{width:43px!important;height:43px!important;flex-basis:43px!important}
  .briefing-page-two .score-preview-icon svg{width:26px!important;height:26px!important}
  .briefing-page-two .score-preview-label{font-size:17px!important}
  .briefing-page-two .score-preview-short{font-size:18px!important}
  .briefing-page-two .briefing-goal-hero{margin-top:9px!important;padding:12px 16px!important}
  .briefing-page-two .briefing-goal-hero h2{font-size:24px!important}
  #start-company-btn button{min-height:49px!important;font-size:18px!important}

  .candidate-grid.founding-grid{grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:9px!important}
  .founding-grid .candidate-card{min-height:300px!important;padding:11px!important}
  .founding-grid .trait-row{display:block!important;padding:7px 0 6px!important;font-size:17px!important}
  .founding-grid .rating{font-size:17px!important}
}

@media(max-width:1100px) and (min-width:801px){
  /* Keep five columns as requested while there is still laptop/tablet width. */
  .candidate-grid.founding-grid{grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:7px!important}
  .founding-grid .candidate-card{padding:9px!important}
  .founding-grid .candidate-name{font-size:17px!important}
  .founding-grid .trait-row{font-size:17px!important;padding:6px 0!important}
  .founding-grid .rating{font-size:17px!important}
}

@media(max-width:800px){
  .candidate-grid.founding-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  .briefing-page-one .briefing-screen{min-height:0!important}
  .briefing-page-two .score-preview-grid{grid-template-columns:1fr 1fr!important}
}


/* ============================================================
   v5: true compact Walkthrough + modal interruptions
   ============================================================ */

/* Hide Gradio's own Walkthrough chrome completely. The only progress display
   is #page-progress-pill in the top-right. */
.stepper > .step-title,
.stepper > .stepper-wrapper,
.stepper .step-title,
.stepper .stepper-wrapper{
  display:none!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
.stepper{
  gap:0!important;
  row-gap:0!important;
  margin:0!important;
  padding:0!important;
}
.stepper > .tabitem{
  margin-top:0!important;
  padding-top:0!important;
}

#page-progress-pill{
  position:fixed;
  top:10px;
  right:14px;
  z-index:500;
  min-width:64px;
  height:37px;
  padding:0 12px;
  border-radius:999px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#172746;
  color:#fff;
  border:1px solid rgba(255,255,255,.35);
  box-shadow:0 7px 20px rgba(20,42,76,.24);
  font:800 17px/1 Arial,Helvetica,sans-serif;
  letter-spacing:.03em;
}
/* v4's attempted stepper pill should never display. */
.stepper-wrapper{position:static!important}

/* Mission 2: keep the useful label-flow, remove the explanatory tail and use
   the vertical space more efficiently. */
.label-training-explainer{
  margin:0 0 6px!important;
  padding:14px 17px!important;
  border-radius:16px!important;
}
.label-training-explainer h2{font-size:24px!important;margin:2px 0 4px!important}
.label-training-explainer>p{font-size:17px!important;line-height:1.35!important;margin:0 0 9px!important}
.label-flow{gap:7px!important}
.label-count-card,.label-ai-card{min-height:92px!important;padding:10px 12px!important}
.label-explainer-callout{display:none!important}
.ai-ready-card{display:none!important}
#train-ai-btn,#start-scaling-btn{margin-top:2px!important;margin-bottom:2px!important}

/* Mission 3: the one sentence explaining each round is core teaching text. */
.mission-banner p{
  font-size:17px!important;
  line-height:1.34!important;
  font-weight:650!important;
}
.growth-grid{margin-top:0!important}
.growth-card .panel-kicker,
.pipeline-card .panel-kicker,
.ticker-card .panel-kicker{font-size:17px!important}
.growth-stat-row small{font-size:17px!important}
.growth-stat-row b{font-size:28px!important}
.mini-result-row span{font-size:17px!important}
.mini-result-row b{font-size:25px!important}
.workforce-average-panel .panel-kicker{font-size:17px!important}
.workforce-average-item{font-size:17px!important}
.workforce-average-item b{font-size:17px!important}

/* Clicking Inspect now opens a real modal-like overlay rather than expanding
   the page and pushing the next hiring-round button down. */
.modal-toggle{
  position:absolute!important;
  opacity:0!important;
  pointer-events:none!important;
  width:1px!important;
  height:1px!important;
}
.ui-modal{display:none;position:fixed;inset:0;z-index:1000;align-items:center;justify-content:center;padding:24px}
.modal-toggle:checked ~ .ui-modal{display:flex!important}
.ui-modal-backdrop{position:absolute;inset:0;background:rgba(8,18,34,.62);backdrop-filter:blur(4px);cursor:pointer}
.ui-modal-card{
  position:relative;
  z-index:1;
  width:min(820px,92vw);
  max-height:min(720px,88vh);
  overflow:auto;
  border-radius:24px;
  padding:26px 28px 24px;
  background:#fff;
  border:1px solid #d9e3ef;
  box-shadow:0 28px 90px rgba(7,20,40,.34);
}
.ui-modal-close{
  position:absolute;right:16px;top:13px;width:40px;height:40px;border-radius:50%;
  display:grid;place-items:center;background:#eef2f7;color:#24344d;
  font:900 29px/1 Arial,sans-serif;cursor:pointer
}
.ui-modal-kicker{font-size:17px;font-weight:900;letter-spacing:.13em;color:#5e50d7;margin-bottom:4px}
.ui-modal-card h2{font-size:31px!important;line-height:1.1!important;margin:4px 50px 7px 0!important;color:#17223b!important}
.ui-modal-card>p{font-size:17px!important;line-height:1.45!important;color:#53627b!important;margin:0 0 17px!important}
.ui-modal-done{
  display:block;width:max-content;margin:18px auto 0;padding:12px 20px;border-radius:13px;
  background:#243b73;color:#fff;font-size:17px;font-weight:900;cursor:pointer
}
.hire-inspection-launch{margin:8px 0 10px}
.hire-inspect-open{
  display:flex;align-items:center;justify-content:space-between;gap:18px;cursor:pointer;
  padding:13px 17px;border-radius:14px;background:linear-gradient(120deg,#eef4ff,#f5f0ff);
  border:2px solid #9ab7ef;box-shadow:0 7px 18px rgba(45,81,145,.10)
}
.hire-inspect-open span{font-size:17px;font-weight:900;letter-spacing:.035em;color:#284f92}
.hire-inspect-open small{font-size:17px;font-weight:700;color:#667792}
.hire-modal-card{width:min(900px,92vw)!important}
.hire-inspect-grid.modal-grid{grid-template-columns:repeat(4,1fr)!important;padding:0!important;margin-top:8px!important}
.hire-modal-card .hire-inspect-stat{padding:14px!important}
.hire-modal-card .hire-inspect-stat span{font-size:17px!important}
.hire-modal-card .hire-inspect-stat b{font-size:17px!important}
.hire-modal-card .hire-inspect-stat small{font-size:17px!important}

/* End-of-pool NEWS ALERT: interrupt the simulation clearly, then let the user
   close it and proceed to the existing news button. */
.news-modal-card{
  width:min(720px,90vw)!important;
  text-align:center;
  padding:34px 38px 30px!important;
  background:linear-gradient(145deg,#fffaf0,#fff3d6)!important;
  border:2px solid #f0c861!important;
}
.news-modal-icon{
  width:76px;height:76px;margin:0 auto 12px;border-radius:22px;display:grid;place-items:center;
  background:#f0a51e;color:#fff;font-size:49px;font-weight:900;box-shadow:0 10px 24px rgba(192,120,0,.24)
}
.news-kicker{color:#986900!important;font-size:17px!important}
.news-modal-card h2{font-size:36px!important;margin:5px 0 9px!important}
.news-modal-card>p{font-size:20px!important;color:#5f4d25!important;margin-bottom:18px!important}
.news-modal-done{background:#ad7709!important;font-size:17px!important;min-width:150px}
/* The old in-flow alert is no longer used, but hide it defensively. */
.event-trigger-card{display:none!important}

/* Remove the extra post-headline explanation from Breaking Industry News. */
.breaking-news-detail{display:none!important}
.breaking-news-card{padding-bottom:20px!important}

@media(max-width:900px){
  #page-progress-pill{top:7px;right:8px;height:34px;min-width:58px;font-size:17px}
  .hire-inspect-grid.modal-grid{grid-template-columns:1fr 1fr!important}
}
/* ============================================================
   v6: compact evidence + separate fresh-data repair screen
   ============================================================ */

/* Pull the active mission right up underneath the sticky company HUD. */
#global-scoreboard{
  padding-bottom:1px!important;
  margin-bottom:-5px!important;
}
.stepper{
  margin-top:-7px!important;
  padding-top:0!important;
}
.stepper > .tabitem{
  margin-top:0!important;
  padding-top:0!important;
}
.stepper > .tabitem > div:first-child{
  margin-top:0!important;
}
.mission-banner{margin-top:0!important}

/* Diagnose the AI: evidence lives in two modal inspections, not down the page. */
.diagnosis-compact-shell{padding:0!important;margin:0!important}
.diagnosis-pause-banner{margin:0 0 10px!important;padding:16px 20px!important}
.diagnosis-pause-banner h1{font-size:33px!important;margin:3px 0 5px!important}
.diagnosis-pause-banner p{font-size:18px!important;line-height:1.4!important}
.diagnosis-action-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0 10px}
.diagnosis-action-wrap{min-width:0}
.diagnosis-action-button{
  min-height:118px;display:flex;align-items:center;gap:15px;padding:17px 19px;border-radius:18px;
  cursor:pointer;background:#fff;border:2px solid #cbd9eb;box-shadow:0 8px 20px rgba(32,58,98,.09);
  transition:transform .15s ease,box-shadow .15s ease,border-color .15s ease;
}
.diagnosis-action-button:hover{transform:translateY(-2px);box-shadow:0 12px 25px rgba(32,58,98,.14)}
.diagnosis-action-button.rejected-action{border-color:#edc3cc;background:linear-gradient(120deg,#fff,#fff4f6)}
.diagnosis-action-button.training-action{border-color:#cfc9fb;background:linear-gradient(120deg,#fff,#f5f2ff)}
.diagnosis-action-icon{
  width:54px;height:54px;flex:0 0 54px;border-radius:16px;display:grid;place-items:center;
  background:#243b73;color:#fff;font-size:20px;font-weight:900;
}
.rejected-action .diagnosis-action-icon{background:#c44259}
.training-action .diagnosis-action-icon{background:#6555da;font-size:17px}
.diagnosis-action-button b{display:block;font-size:21px;color:#17223b;line-height:1.2;margin-bottom:5px}
.diagnosis-action-button small{display:block;font-size:17px;line-height:1.4;color:#5f6f86}
.diagnosis-discuss-strip{padding:12px 15px;border-radius:13px;background:#fff6df;border:1px solid #edd59c;color:#604c22;font-size:17px;line-height:1.45}
.diagnosis-modal-card{width:min(1120px,94vw)!important;max-height:90vh!important;padding:24px 26px!important}
.diagnosis-modal-grid{grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:11px!important;margin:13px 0!important}
.diagnosis-modal-grid .diagnosis-candidate-card{padding:12px!important}
.training-modal-card{width:min(1180px,95vw)!important}
.training-modal-card .training-example-review{margin:0!important;padding:0!important;background:transparent!important;border:0!important;box-shadow:none!important}
.training-modal-card .training-example-review h2{font-size:28px!important;margin:4px 0 13px!important}
.training-modal-card .training-example-columns{gap:15px!important}
.training-modal-card .training-sample-grid{gap:9px!important}

/* Mission 5: the diagnosis statement and option explanations are primary text. */
.mission-five-intro .mission-banner{min-height:105px!important;padding:14px 20px!important}
.mission-five-intro .mission-banner h1{font-size:31px!important}
.mission-five-intro .mission-banner p{font-size:23px!important;line-height:1.38!important;font-weight:750!important;max-width:940px!important}
.fix-choice-grid{gap:14px!important;margin:10px 0 11px!important}
.fix-choice-card{
  min-height:205px!important;padding:20px 22px!important;border-radius:19px!important;
  display:flex!important;flex-direction:column!important;justify-content:center!important;
}
.fix-choice-number{width:44px!important;height:44px!important;font-size:22px!important;margin-bottom:7px!important}
.fix-choice-card h2{font-size:27px!important;line-height:1.2!important;margin:4px 0 10px!important}
.fix-choice-card p{font-size:20px!important;line-height:1.48!important;color:#45566f!important;margin:0!important}
.fix-option-buttons button{min-height:55px!important;font-size:18px!important;font-weight:850!important}

/* Fresh-data option is a replacement screen, not content appended below. */
.fresh-data-screen{margin:0!important;padding:0!important}
.fresh-data-screen .mission-banner{min-height:88px!important;margin:0 0 7px!important}
.fresh-data-screen .mission-banner p{font-size:17px!important}
#back-fix-options-btn button{min-height:46px!important;font-size:17px!important;font-weight:800!important;margin-top:7px!important}
#repair-train-btn button,#redeploy-ai-btn button{min-height:55px!important;font-size:18px!important;font-weight:850!important}

@media(max-width:900px){
  .diagnosis-action-grid{grid-template-columns:1fr}
  .diagnosis-modal-grid{grid-template-columns:1fr 1fr!important}
  .mission-five-intro .mission-banner p{font-size:19px!important}
  .fix-choice-grid{grid-template-columns:1fr!important}
  .fix-choice-card p{font-size:18px!important}
}


/* ============================================================
   v7: direct interstate transition + compact interstate diagnosis
   ============================================================ */

/* The old Mission 6 wait button remains the actual Gradio navigation control,
   but the student interacts with the modal button instead. */
#repair-wait-btn{display:none!important}

.mandatory-transition-modal{
  display:flex!important;
  position:fixed!important;
  inset:0!important;
  z-index:1400!important;
  align-items:center!important;
  justify-content:center!important;
  padding:24px!important;
}
.mandatory-transition-modal .mandatory-backdrop{
  cursor:default!important;
  background:rgba(8,18,34,.68)!important;
  backdrop-filter:blur(5px)!important;
}
.interstate-transition-card{
  width:min(760px,91vw)!important;
  text-align:center!important;
  padding:38px 42px 34px!important;
  background:linear-gradient(145deg,#f8fbff,#edf4ff)!important;
  border:2px solid #a9c9ef!important;
  box-shadow:0 32px 100px rgba(8,28,58,.38)!important;
}
.transition-icon{
  width:76px;height:76px;margin:0 auto 13px;border-radius:22px;display:grid;place-items:center;
  background:#2d7de9;color:#fff;font-size:43px;font-weight:900;box-shadow:0 12px 26px rgba(45,125,233,.28)
}
.transition-kicker{font-size:17px!important;color:#3267a8!important}
.interstate-transition-card h2{font-size:36px!important;margin:6px 0 10px!important}
.interstate-transition-card>p{font-size:21px!important;line-height:1.45!important;margin:0 auto 23px!important;color:#465a77!important}
.transition-open-button{
  border:0;border-radius:15px;padding:16px 22px;min-height:58px;background:#2d7de9;color:#fff;
  font:900 17px/1.25 Arial,Helvetica,sans-serif;cursor:pointer;box-shadow:0 10px 24px rgba(45,125,233,.25)
}
.transition-open-button:hover{background:#216fd6;transform:translateY(-1px)}

/* Mission 7 diagnosis now mirrors the earlier Diagnose AI screen: evidence
   lives behind two explicit inspection controls instead of down the page. */
.interstate-diagnosis-compact .diagnosis-pause-banner{margin-bottom:10px!important}
.interstate-diagnosis-compact .diagnosis-value-callout{
  margin-top:10px!important;padding:10px 12px!important;border-radius:11px!important;
  background:rgba(255,255,255,.11)!important;border:1px solid rgba(255,255,255,.20)!important;
  color:#fff!important;font-size:17px!important;line-height:1.4!important
}
.interstate-training-modal-card{width:min(1180px,95vw)!important}
.interstate-training-review{margin-top:12px}
.interstate-training-review .training-example-columns{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.interstate-training-review h3{font-size:19px!important;margin:0 0 9px!important;color:#283750!important}
.interstate-training-review .training-sample-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.current-training-card{padding:12px!important}
.current-training-card .candidate-name{font-size:17px!important}
.current-training-card .trait-row{font-size:17px!important;padding:7px 0!important}
.current-training-card .rating{font-size:17px!important}
.current-training-card .training-label-pill{font-size:17px!important;padding:8px!important}
.current-training-card .training-label-pill.hire{background:#e6f7ef!important;color:#147252!important}
.current-training-card .training-label-pill.reject{background:#f8e9ed!important;color:#a5364b!important}

@media(max-width:900px){
  .interstate-transition-card{padding:28px 22px 24px!important}
  .interstate-transition-card h2{font-size:30px!important}
  .interstate-transition-card>p{font-size:18px!important}
  .interstate-training-review .training-example-columns{grid-template-columns:1fr}
  .interstate-training-review .training-sample-grid{grid-template-columns:repeat(3,1fr)}
}


/* ============================================================
   v8: modal Mission 8 completion + colourful final report
   ============================================================ */

/* The underlying Gradio button remains wired for navigation but is only
   activated by the button inside the completion modal. */
#final-results-btn{display:none!important}

.mission8-complete-modal{
  display:flex!important;
  position:fixed!important;
  inset:0!important;
  z-index:1500!important;
  align-items:center!important;
  justify-content:center!important;
  padding:24px!important;
}
.mission8-complete-card{
  width:min(760px,91vw)!important;
  text-align:center!important;
  padding:38px 42px 34px!important;
  background:linear-gradient(145deg,#f4fff9,#edf9f4)!important;
  border:2px solid #9ed8bf!important;
  box-shadow:0 32px 100px rgba(8,40,30,.34)!important;
}
.mission8-complete-icon{
  width:78px;height:78px;margin:0 auto 13px;border-radius:23px;display:grid;place-items:center;
  background:#1a9b62;color:#fff;font-size:45px;font-weight:900;box-shadow:0 12px 26px rgba(26,155,98,.25)
}
.mission8-complete-kicker{font-size:17px!important;color:#147653!important}
.mission8-complete-card h2{font-size:34px!important;margin:6px auto 10px!important;max-width:650px!important}
.mission8-complete-card>p{font-size:21px!important;line-height:1.45!important;color:#465f55!important;margin:0 auto 23px!important}
.mission8-final-button{
  border:0;border-radius:15px;padding:16px 23px;min-height:60px;background:#1a9b62;color:#fff;
  font:900 17px/1.25 Arial,Helvetica,sans-serif;cursor:pointer;box-shadow:0 10px 24px rgba(26,155,98,.24)
}
.mission8-final-button:hover{background:#138657;transform:translateY(-1px)}

/* Final stats should feel like the payoff, not five identical grey boxes. */
.final-screen-colour{padding:22px!important}
.final-screen-colour .final-hero{margin-bottom:16px!important}
.final-screen-colour .final-hero p{font-size:18px!important;margin-bottom:0!important}
.final-stats-colour{gap:12px!important;margin:12px 0 15px!important}
.final-stats-colour .final-stat-card{
  min-height:118px!important;
  padding:18px 15px!important;
  border:1px solid transparent!important;
  border-radius:18px!important;
  display:flex!important;
  flex-direction:column!important;
  justify-content:center!important;
  box-shadow:0 7px 18px rgba(35,60,100,.07)!important;
}
.final-stats-colour .final-stat-card span{font-size:17px!important;font-weight:800!important;margin-bottom:7px!important}
.final-stats-colour .final-stat-card b{font-size:30px!important;line-height:1.05!important}
.final-stats-colour .stat-value{background:#e9f9f1!important;border-color:#bfe8d4!important}.final-stats-colour .stat-value span{color:#39755e!important}.final-stats-colour .stat-value b{color:#11704b!important}
.final-stats-colour .stat-workers{background:#edf5ff!important;border-color:#c9def8!important}.final-stats-colour .stat-workers span{color:#426b9b!important}.final-stats-colour .stat-workers b{color:#245f9f!important}
.final-stats-colour .stat-efficiency{background:#f0efff!important;border-color:#d6d1fb!important}.final-stats-colour .stat-efficiency span{color:#6259a8!important}.final-stats-colour .stat-efficiency b{color:#574bb8!important}
.final-stats-colour .stat-culture{background:#fff2f7!important;border-color:#f0ccdc!important}.final-stats-colour .stat-culture span{color:#a05275!important}.final-stats-colour .stat-culture b{color:#9b4168!important}
.final-stats-colour .stat-screened{background:#fff6e9!important;border-color:#eed8b4!important}.final-stats-colour .stat-screened span{color:#91682b!important}.final-stats-colour .stat-screened b{color:#9a6617!important}

/* The old Compare with the class panel is deliberately removed by final_report.
   Hide defensively in case an older cached fragment remains in the DOM. */
.final-screen .takeaway{display:none!important}

@media(max-width:900px){
  .mission8-complete-card{padding:28px 22px 24px!important}
  .mission8-complete-card h2{font-size:29px!important}
  .mission8-complete-card>p{font-size:18px!important}
  .final-stats-colour{grid-template-columns:1fr 1fr!important}
}


/* ============================================================
   v9: remove the invisible progress-host row
   ============================================================ */
/* The x/10 indicator is fixed-position. Its Gradio HTML host must not remain
   as an empty normal-flow component between the sticky dashboard and the
   Walkthrough, otherwise Gradio reserves a row + layout gap for it. */
#page-progress-host{
  display:contents!important;
  width:0!important;
  height:0!important;
  min-width:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
  border:0!important;
}

/* Collapse the original Walkthrough chrome completely. The live x/10 pill
   still reads its selected state from these hidden DOM nodes. */
.stepper-wrapper,
.stepper > .step-title{
  display:none!important;
  width:0!important;
  height:0!important;
  min-height:0!important;
  margin:0!important;
  padding:0!important;
}
.stepper{
  gap:0!important;
  row-gap:0!important;
  margin:0!important;
  padding:0!important;
  min-height:0!important;
}
.stepper > .tabitem{
  margin:0!important;
  padding-top:0!important;
}

/* Keep only a tiny visual breathing space below the HUD itself. */
#global-scoreboard{
  margin-bottom:0!important;
  padding-bottom:0!important;
}
#global-scoreboard .scoreboard-shell{margin-bottom:2px!important}
.mission-banner{margin-top:0!important}


/* ============================================================
   v10: structural dashboard -> mission adjacency
   ============================================================ */
/* v10 removes the old root-level app-header and progress HTML components in
   Python before Blocks is built. These are defensive rules only. */
.app-header-brand,.app-header-subtitle,#page-progress-host{display:none!important}

/* There should now be only the dashboard and the Walkthrough next to each
   other in the root column. Pull out the ordinary Gradio root gap as well. */
#global-scoreboard{margin:0 0 -10px!important;padding-bottom:0!important}
#global-scoreboard + .stepper{margin-top:-10px!important;padding-top:0!important}
.stepper{margin-top:-10px!important;padding-top:0!important;gap:0!important}
.stepper-wrapper{display:none!important}
.stepper > .tabitem{margin:0!important;padding:0!important}
.stepper > .tabitem > div:first-child{margin-top:0!important;padding-top:0!important}
.mission-banner{margin-top:0!important}

/* The pill now lives in #global-scoreboard, but remains viewport-fixed. */
#global-scoreboard #page-progress-pill{
  position:fixed!important;
  top:10px!important;
  right:14px!important;
  z-index:500!important;
}


/* ============================================================
   v11 final interaction/layout pass
   ============================================================ */
.founder-pause-compact{padding:16px!important}.founder-pause-compact .discussion-pause-banner{margin-bottom:8px!important}
.founder-name-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:8px}.founder-name-card-wrap{min-width:0}
.founder-name-card{display:flex;align-items:center;gap:12px;min-height:76px;padding:12px 14px;border:2px solid #dce5f1;border-radius:16px;background:#fff;cursor:pointer;box-shadow:0 6px 16px rgba(31,58,99,.07);transition:.15s ease}.founder-name-card:hover{transform:translateY(-2px);border-color:#7faee8;box-shadow:0 10px 22px rgba(31,58,99,.13)}.founder-name-card .abstract-avatar{width:44px;height:44px;border-radius:13px;flex:0 0 44px}.founder-name{font:800 18px/1.1 Arial,Helvetica,sans-serif;color:#17223b}.founder-click-hint{margin-top:4px;font-size:17px;font-weight:700;color:#738198}
.founder-detail-card{max-width:560px!important}.founder-detail-head{display:flex;gap:14px;align-items:center;margin-bottom:16px}.founder-detail-head .abstract-avatar{width:58px;height:58px;border-radius:17px;font-size:20px}.founder-detail-head h2{margin:2px 0!important;font-size:28px!important}.founder-detail-traits{display:grid;grid-template-columns:1fr 1fr;gap:10px}.founder-detail-traits>div{padding:12px;border-radius:13px;background:#f5f8fc;border:1px solid #e0e7f0}.founder-detail-traits span{display:block;font-size:17px;font-weight:800;color:#59687d;margin-bottom:6px}.founder-detail-traits b{font-size:20px;white-space:nowrap}
.mission3-inline-head{margin:-2px -2px 10px;padding:0 0 10px;border-bottom:1px solid #e3e9f1}.mission3-inline-head small{font:900 17px/1 Verdana,Arial,sans-serif;letter-spacing:.12em;color:#2d7de9}.mission3-inline-head h2{font:900 27px/1.08 Arial,Helvetica,sans-serif!important;margin:4px 0!important;color:#17223b!important}.mission3-inline-head p{font-size:17px!important;line-height:1.35!important;color:#53627b!important;margin:3px 0 0!important}.pipeline-inline-inspect{margin-top:9px}.pipeline-inline-inspect .hire-inspection-launch{margin:0!important}.pipeline-inline-inspect .hire-inspect-open{padding:10px 12px!important;border-radius:11px!important;box-shadow:none!important}.pipeline-inline-inspect .hire-inspect-open span{font-size:17px!important}.pipeline-inline-inspect .hire-inspect-open small{font-size:17px!important}#growth-round-btn button{background:#f39a2c!important;border-color:#df861b!important;color:#fff!important;min-height:54px!important;font-size:17px!important}
.ui-modal-action{display:block;width:100%;margin-top:18px;padding:14px 18px;border:0;border-radius:13px;font:900 17px/1.2 Arial,Helvetica,sans-serif;cursor:pointer}.orange-action{background:#f39a2c;color:#fff;box-shadow:0 8px 22px rgba(214,126,20,.24)}.orange-action:hover{background:#e88d20}.scaling-finish-modal{max-width:650px!important;text-align:center}.scaling-finish-modal h2{font-size:27px!important;line-height:1.25!important}.scaling-finish-modal p{font-size:17px!important}.no-hire-round-card{max-width:620px!important;text-align:center}.no-hire-icon{width:64px;height:64px;border-radius:50%;display:grid;place-items:center;margin:0 auto 12px;background:#fcecef;color:#c53e55;font-size:30px;font-weight:900}.no-hire-round-card h2{font-size:25px!important;line-height:1.28!important}.no-hire-round-card p{font-size:17px!important}#wait-applicants-btn,#interstate-diagnose-btn{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important}.interstate-result-card{display:none!important}
.guild-news-page{min-height:min(610px,calc(100vh - 180px));display:flex;flex-direction:column;justify-content:center;align-items:center;padding:24px;background:radial-gradient(circle at 20% 0,#edf6ff 0,#f4f7fb 45%,#eef2f7 100%);border-radius:24px}.guild-news-context{font-size:20px;font-weight:800;color:#40536e;text-align:center;margin-bottom:18px}.linkedin-news-card{width:min(880px,96%);padding:24px 28px;border-radius:18px;background:#fff;border:1px solid #d9e1ea;box-shadow:0 18px 48px rgba(27,47,77,.16);position:relative;overflow:hidden}.linkedin-news-card:after{content:"";position:absolute;right:-70px;bottom:-90px;width:240px;height:240px;border-radius:50%;background:#e9f3ff}.linkedin-news-top{display:grid;grid-template-columns:48px 1fr auto;gap:11px;align-items:center;position:relative;z-index:2}.linkedin-mark{width:46px;height:46px;border-radius:8px;background:#0a66c2;color:#fff;display:grid;place-items:center;font:bold 25px Arial}.linkedin-news-top b{display:block;font-size:17px}.linkedin-news-top span{display:block;font-size:17px;color:#738096;margin-top:2px}.linkedin-dots{font-weight:900;color:#68758a;letter-spacing:2px}.breaking-news-stamp{display:inline-block;margin-top:24px;padding:7px 11px;border-radius:8px;background:#cf2035;color:#fff;font:900 17px Verdana,Arial,sans-serif;letter-spacing:.10em;transform:rotate(-1deg);position:relative;z-index:2}.linkedin-news-card h1{font:900 38px/1.08 Arial,Helvetica,sans-serif!important;color:#17223b!important;margin:12px 0 12px!important;max-width:760px;position:relative;z-index:2}.linkedin-news-card>p{font-size:19px!important;line-height:1.5!important;color:#4e5e74!important;max-width:780px;position:relative;z-index:2}.linkedin-news-footer{display:flex;gap:24px;margin-top:22px;padding-top:13px;border-top:1px solid #e4e8ee;font-size:17px;color:#69778b;position:relative;z-index:2}#understood-news-btn button{min-height:54px!important;font-size:17px!important}
.fix-choice-click-grid{gap:16px!important;margin:8px 0!important}.fix-choice-click{min-width:0!important}.fix-choice-click button{height:100%!important;min-height:205px!important;padding:22px!important;border:2px solid #d7e1ee!important;border-radius:20px!important;background:#fff!important;color:#17223b!important;text-align:left!important;white-space:pre-line!important;font:800 18px/1.45 Arial,Helvetica,sans-serif!important;box-shadow:0 8px 22px rgba(31,56,95,.08)!important;transition:.15s ease!important}.fix-choice-click button:hover{transform:translateY(-3px)!important;border-color:#7faee8!important;box-shadow:0 13px 30px rgba(31,56,95,.14)!important}.option-one button::first-line,.option-two button::first-line{font-size:30px!important;color:#2d7de9!important}
.remove-guild-explainer{display:flex;gap:15px;align-items:center;padding:14px 17px;margin:8px 0 12px;border-radius:16px;background:#eef5ff;border:1px solid #cbdcf2}.remove-guild-icon{width:52px;height:52px;border-radius:15px;display:grid;place-items:center;background:#dfe4ec;color:#7f8998;font-size:27px;text-decoration:line-through}.remove-guild-explainer h2{font-size:22px!important;margin:0 0 4px!important}.remove-guild-explainer p{font-size:17px!important;line-height:1.4!important;margin:0!important;color:#4f6078}.no-guild-training-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.no-guild-training-card{padding:9px;border:1px solid #dfe6ef;border-radius:13px;background:#fff}.no-guild-head{display:flex;align-items:center;gap:7px;margin-bottom:7px}.no-guild-head .abstract-avatar{width:32px;height:32px;border-radius:9px;font-size:17px}.no-guild-head b{font-size:17px}.ignored-guild{display:block;margin-top:2px;font-size:17px;font-weight:800;color:#9aa3af;text-decoration:line-through}.no-guild-traits{display:grid;gap:3px}.no-guild-traits>span{font-size:17px;color:#5e6c80;white-space:nowrap}.no-guild-traits .rating-dots{font-size:17px!important;margin-left:2px}.no-guild-training-card .training-label-pill{padding:5px!important;margin-top:6px!important;font-size:17px!important}.back-repair-btn button{min-height:42px!important}
.repaired-pool-modal{max-width:700px!important}.repaired-pool-modal h2{font-size:25px!important;line-height:1.28!important}.repaired-pool-modal h3{font-size:24px!important;margin:4px 0 6px!important;color:#17223b}.repaired-pool-modal p{font-size:17px!important}.transition-divider{height:1px;background:#dce4ed;margin:18px 0}.interstate-result-modal-card{max-width:620px!important;text-align:center}.interstate-result-icon{width:66px;height:66px;margin:0 auto 12px;border-radius:50%;display:grid;place-items:center;background:#ede9ff;color:#6252dc;font-size:34px;font-weight:900}.interstate-result-modal-card h2{font-size:28px!important;line-height:1.25!important}.interstate-result-modal-card p{font-size:19px!important}
@media(max-width:1050px){.founder-name-grid,.no-guild-training-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}@media(max-width:760px){.founder-name-grid,.no-guild-training-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.founder-detail-traits{grid-template-columns:1fr}.fix-choice-click-grid{flex-direction:column!important}}


/* ============================================================
   v12: restored team summary, persistent progress, final-round modal,
   and polished repair choices
   ============================================================ */
.founder-average-profile{margin:7px 0 10px!important;padding:11px 14px!important;border-radius:14px!important}
.founder-average-profile .profile-panel{border-top:0!important;padding-top:0!important;margin-top:0!important}
.founder-average-profile .profile-panel h3{font-size:17px!important;margin:0 0 7px!important}
.founder-average-profile .profile-item{font-size:17px!important;margin:6px 0!important}

body > #page-progress-pill{position:fixed!important;top:10px!important;right:14px!important;z-index:10000!important;min-width:70px!important;height:48px!important;padding:0 17px!important;border-radius:999px!important;display:grid!important;place-items:center!important;background:#142d54!important;color:#fff!important;border:1px solid rgba(255,255,255,.22)!important;box-shadow:0 8px 24px rgba(17,39,72,.24)!important;font:900 20px/1 Arial,Helvetica,sans-serif!important}
#global-scoreboard #page-progress-pill{display:none!important}
#diagnose-hiring-btn{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important}
#understood-news-btn button{background:linear-gradient(135deg,#f39a2c,#e98518)!important;border-color:#d77911!important;color:#fff!important;min-height:60px!important;font-size:18px!important;border-radius:15px!important;box-shadow:0 10px 26px rgba(218,126,20,.24)!important}

#remove-guild-hidden-btn,#fresh-data-hidden-btn{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important}
.repair-option-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:10px 0 8px}
.repair-option-card{appearance:none;border:2px solid transparent;border-radius:22px;padding:0;min-height:220px;display:grid;grid-template-columns:72px 1fr;text-align:left;overflow:hidden;cursor:pointer;box-shadow:0 10px 28px rgba(31,56,95,.11);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease;font-family:Arial,Helvetica,sans-serif}
.repair-option-card:hover{transform:translateY(-4px);box-shadow:0 17px 38px rgba(31,56,95,.18)}
.repair-option-one{background:linear-gradient(135deg,#eef6ff 0%,#fff 72%);border-color:#b9d5f4}.repair-option-two{background:linear-gradient(135deg,#f3efff 0%,#fff 72%);border-color:#d4c6ff}.repair-option-one:hover{border-color:#4d91dc}.repair-option-two:hover{border-color:#8069de}
.repair-option-number{display:grid;place-items:center;font-size:38px;font-weight:900;color:#fff;background:linear-gradient(180deg,#2d7de9,#1d5fb7)}.repair-option-two .repair-option-number{background:linear-gradient(180deg,#705ad8,#5140ae)}
.repair-option-copy{display:flex;flex-direction:column;justify-content:center;padding:24px 25px}.repair-option-copy strong{display:block;font-size:26px;line-height:1.18;color:#17223b;margin-bottom:12px}.repair-option-copy>span{display:block;font-size:18px;line-height:1.48;color:#4e6079;font-weight:600}.repair-option-copy em{display:block;margin-top:17px;font-size:17px;font-style:normal;font-weight:900;letter-spacing:.03em;color:#2568b5}.repair-option-two .repair-option-copy em{color:#6048bb}
@media(max-width:850px){.repair-option-grid{grid-template-columns:1fr}.repair-option-card{min-height:185px;grid-template-columns:60px 1fr}.repair-option-copy strong{font-size:22px}.repair-option-copy>span{font-size:17px}body > #page-progress-pill{height:40px!important;min-width:62px!important;font-size:17px!important}}

/* ============================================================
   v13: briefing readability + final concepts unlocked screen
   ============================================================ */
.briefing-story-v13 p{font-weight:400!important}
.briefing-story-v13 strong{font-weight:400!important}
.briefing-page-two .score-preview-short{font-weight:500!important;letter-spacing:0!important}
.briefing-page-two .score-preview-label{font-weight:700!important}

.concepts-final-screen{padding:25px 28px 22px!important;background:linear-gradient(145deg,#f7faff,#eef4fb)!important;overflow:visible!important}
.concepts-hero{text-align:center;max-width:980px;margin:0 auto 22px}.concepts-spark{width:64px;height:64px;margin:0 auto 8px;border-radius:20px;display:grid;place-items:center;background:linear-gradient(145deg,#fff1bf,#ffd36b);color:#8e5e00;font-size:34px;box-shadow:0 12px 28px rgba(156,108,12,.18)}.concepts-kicker{font:900 17px/1 Verdana,Arial,sans-serif;letter-spacing:.16em;color:#6252dc}.concepts-hero h1{font:900 46px/1.02 Arial,Helvetica,sans-serif!important;margin:7px 0 9px!important;color:#17223b!important}.concepts-hero p{font-size:18px!important;line-height:1.48!important;color:#53627b!important;margin:0 auto!important;max-width:850px}
.concept-unlocked-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;max-width:1180px;margin:0 auto}.concept-card-wrap{min-width:0}.concept-card{min-height:310px;border-radius:24px;padding:24px 23px 21px;display:flex;flex-direction:column;align-items:flex-start;cursor:pointer;border:2px solid transparent;box-shadow:0 12px 30px rgba(31,56,95,.11);transition:transform .17s ease,box-shadow .17s ease,border-color .17s ease}.concept-card:hover{transform:translateY(-5px);box-shadow:0 19px 42px rgba(31,56,95,.17)}.concept-label-card{background:linear-gradient(145deg,#e9f9f1,#fff 72%);border-color:#bce8d2}.concept-sampling-card{background:linear-gradient(145deg,#edf4ff,#fff 72%);border-color:#c5d9f5}.concept-history-card{background:linear-gradient(145deg,#f4efff,#fff 72%);border-color:#d8cafa}.concept-icon,.concept-detail-icon{width:67px;height:67px;border-radius:20px;display:grid;place-items:center;margin-bottom:17px}.concept-icon svg,.concept-detail-icon svg{width:40px;height:40px}.concept-label-icon{background:#d4f3e2;color:#147957}.concept-sampling-icon{background:#dbe9ff;color:#2b68b5}.concept-history-icon{background:#e8ddff;color:#674cbc}.concept-unlocked-tag{padding:5px 8px;border-radius:999px;background:rgba(23,34,59,.07);font:900 17px/1 Verdana,Arial,sans-serif;letter-spacing:.11em;color:#667085}.concept-card h2{font:900 28px/1.13 Arial,Helvetica,sans-serif!important;margin:10px 0 9px!important;color:#17223b!important}.concept-card p{font-size:17px!important;line-height:1.45!important;color:#506079!important;margin:0!important}.concept-open-hint{margin-top:auto;padding-top:18px;font-size:17px;font-weight:900;color:#354d72}.concept-detail-card{max-width:760px!important}.concept-detail-icon{margin-bottom:10px}.concept-detail-card h2{font-size:30px!important;line-height:1.18!important;margin:5px 42px 13px 0!important}.concept-definition{padding:16px 18px;border-radius:15px;background:#f3f6fa;border:1px solid #dfe6ee;font-size:17px;line-height:1.55;color:#3f5069}.simulation-link{margin-top:14px;padding:16px 18px;border-radius:15px;background:#fff8e8;border:1px solid #efdba8;color:#55451f}.simulation-link strong{display:block;font:900 17px/1 Verdana,Arial,sans-serif;letter-spacing:.10em;color:#946600;margin-bottom:7px}.simulation-link p{font-size:17px!important;line-height:1.52!important;margin:0!important;color:#4f5360!important}.concepts-footer-note{text-align:center;margin-top:18px;font-size:17px;font-weight:800;color:#728096}
@media(max-width:950px){.concept-unlocked-grid{grid-template-columns:1fr}.concept-card{min-height:0}.concepts-hero h1{font-size:38px!important}}


/* v14: show the complete official QUT square logo without cropping. */
#global-scoreboard::before{
  background-size:contain!important;
  background-position:center!important;
}
@media(min-width:1000px) and (max-height:850px){#global-scoreboard::before{background-size:contain!important}}
@media(max-width:1150px){#global-scoreboard::before{background-size:contain!important}}
@media(max-width:900px){#global-scoreboard::before{background-size:contain!important}}




/* ============================================================
   v15: final company summary + accessibility font audit.
   Deliberately appended after v14 without touching briefing/dashboard styling.
   ============================================================ */
.final-company-summary{max-width:980px;margin:0 auto 24px;padding:18px 20px 20px;border-radius:22px;background:#fff;border:1px solid #dce5f0;box-shadow:0 10px 28px rgba(31,56,95,.09)}
.final-company-summary-heading{text-align:center;font:900 17px/1 Verdana,Arial,sans-serif;letter-spacing:.13em;color:#53627b;margin-bottom:14px}
.final-company-summary-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.final-summary-card{min-height:128px;padding:17px 18px;border-radius:18px;display:grid;grid-template-columns:48px 1fr;grid-template-rows:auto auto;column-gap:13px;align-items:center;border:1px solid transparent}
.final-summary-icon{grid-row:1/3;width:48px;height:48px;border-radius:15px;display:grid;place-items:center;font:900 25px/1 Arial,sans-serif}
.final-summary-card span{font:800 17px/1.2 Verdana,Arial,sans-serif;letter-spacing:.06em;color:#58677d}
.final-summary-card b{font:900 30px/1 Arial,Helvetica,sans-serif;color:#17223b}
.final-summary-value{background:#eaf9f2;border-color:#c5e9d7}.final-summary-value .final-summary-icon{background:#d3f2e2;color:#147957}
.final-summary-screened{background:#edf4ff;border-color:#c8daf4}.final-summary-screened .final-summary-icon{background:#dbe9ff;color:#2b68b5}
.final-summary-hired{background:#fff3e4;border-color:#f0d5ae}.final-summary-hired .final-summary-icon{background:#ffe3bc;color:#ae6814}
.concepts-section-heading{text-align:center;max-width:900px;margin:2px auto 17px}.concepts-section-heading span{font:900 17px/1 Verdana,Arial,sans-serif;letter-spacing:.12em;color:#6252dc}.concepts-section-heading p{font-size:18px!important;line-height:1.45!important;color:#53627b!important;margin:7px 0 0!important}

/* Accessibility: pop-ups should use space, not tiny text. */
.ui-modal{padding:28px!important}
.ui-modal-card{width:min(900px,94vw)!important;max-height:min(790px,91vh)!important;padding:32px 34px 30px!important}
.ui-modal-kicker{font-size:17px!important;line-height:1.3!important;letter-spacing:.11em!important}
.ui-modal-card h2{font-size:32px!important;line-height:1.18!important;margin-bottom:12px!important}
.ui-modal-card>p{font-size:19px!important;line-height:1.55!important}
.ui-modal-done,.ui-modal-action{font-size:18px!important;line-height:1.25!important;padding:15px 22px!important;min-height:52px!important}
.ui-modal-close{width:46px!important;height:46px!important;font-size:31px!important}
.hire-modal-card,.diagnosis-modal-card,.training-modal-card,.interstate-training-modal-card{width:min(1040px,95vw)!important}
.hire-modal-card .hire-inspect-stat span{font-size:17px!important}.hire-modal-card .hire-inspect-stat b{font-size:19px!important}.hire-modal-card .hire-inspect-stat small{font-size:17px!important;line-height:1.4!important}
.founder-detail-card{max-width:700px!important}.founder-detail-head h2{font-size:31px!important}.founder-detail-traits span{font-size:17px!important}.founder-detail-traits b{font-size:22px!important}
.diagnosis-modal-card .trait-row,.training-modal-card .trait-row,.interstate-training-modal-card .trait-row{font-size:17px!important;line-height:1.35!important}
.diagnosis-modal-card .rating,.training-modal-card .rating,.interstate-training-modal-card .rating{font-size:18px!important}
.training-modal-card .training-sample-card .candidate-name,.interstate-training-modal-card .training-sample-card .candidate-name{font-size:18px!important}
.training-modal-card .training-label-pill,.interstate-training-modal-card .training-label-pill{font-size:17px!important;padding:8px 9px!important}
.news-modal-card,.scaling-finish-modal,.no-hire-round-card,.repaired-pool-modal,.interstate-result-modal-card,.mission8-complete-card{width:min(760px,94vw)!important;max-width:760px!important}
.news-modal-card h2,.scaling-finish-modal h2,.no-hire-round-card h2,.repaired-pool-modal h2,.interstate-result-modal-card h2,.mission8-complete-card h2{font-size:31px!important;line-height:1.2!important}
.news-modal-card>p,.scaling-finish-modal p,.no-hire-round-card p,.repaired-pool-modal p,.interstate-result-modal-card p,.mission8-complete-card p{font-size:19px!important;line-height:1.5!important}
.concept-detail-card{max-width:900px!important}.concept-detail-card h2{font-size:32px!important;line-height:1.2!important}.concept-definition{font-size:19px!important;line-height:1.58!important;padding:19px 21px!important}.simulation-link{padding:19px 21px!important}.simulation-link strong{font-size:17px!important}.simulation-link p{font-size:19px!important;line-height:1.58!important}.concept-card p{font-size:18px!important}.concept-open-hint{font-size:17px!important}.concept-unlocked-tag{font-size:17px!important}

@media(max-width:760px){.final-company-summary-grid{grid-template-columns:1fr}.final-summary-card{min-height:104px}.ui-modal{padding:14px!important}.ui-modal-card{padding:25px 22px 23px!important}.ui-modal-card h2{font-size:27px!important}.ui-modal-card>p,.concept-definition,.simulation-link p{font-size:17px!important}}

/* ============================================================
   v16: SYSTEMATIC ACCESSIBILITY TYPOGRAPHY PASS
   ------------------------------------------------------------
   Readability now takes priority over squeezing every mission above the fold.
   Ordinary instructional text targets >=16px on laptop/desktop; compact labels
   are 14-15px only where they are genuinely secondary. The app also uses more
   of the available viewport instead of shrinking content into the middle.
   ============================================================ */

/* Use the available screen. */
.gradio-container{
  width:96vw!important;
  max-width:1680px!important;
  margin-left:auto!important;
  margin-right:auto!important;
}

/* Persistent page counter: deliberately prominent. */
body > #page-progress-pill,
#global-scoreboard #page-progress-pill{
  min-width:82px!important;
  height:46px!important;
  padding:0 16px!important;
  border-radius:15px!important;
  font-family:Arial,Helvetica,sans-serif!important;
  font-size:21px!important;
  line-height:46px!important;
  font-weight:900!important;
  letter-spacing:.02em!important;
}

/* Top company dashboard: readable at a glance from a normal laptop distance. */
#global-scoreboard{padding-top:8px!important}
#global-scoreboard .scoreboard-shell{gap:14px!important}
#global-scoreboard .score-tile{
  min-height:108px!important;
  padding:15px 18px!important;
  gap:15px!important;
}
#global-scoreboard .score-icon{width:55px!important;height:55px!important;border-radius:16px!important}
#global-scoreboard .score-icon svg{width:31px!important;height:31px!important}
#global-scoreboard .score-label{font-size:17px!important;line-height:1.2!important;letter-spacing:.045em!important}
#global-scoreboard .score-number{font-size:35px!important;line-height:1!important;margin:5px 0!important}
#global-scoreboard .score-denom{font-size:17px!important}
#global-scoreboard .score-sub{font-size:17px!important;line-height:1.25!important}
#global-scoreboard .mini-track{height:8px!important}

/* Mission headings and explanatory copy. */
.mission-kicker,.panel-kicker,.status-kicker,.round-comparison-kicker,
.discussion-pause-kicker,.label-explainer-kicker,.briefing-kicker,
.briefing-section-title,.briefing-goal-label{
  font-size:17px!important;
  line-height:1.3!important;
}
.mission-banner p{font-size:18px!important;line-height:1.45!important}
.selection-status{font-size:17px!important}
.selection-status strong{font-size:20px!important}
.page-label{font-size:17px!important}

/* Mission briefing: remove the old compact-font compromises. */
.briefing-screen{font-size:17px!important}
.briefing-kicker{font-size:17px!important;padding:8px 13px!important}
.briefing-screen h1{font-size:48px!important}
.briefing-story,.briefing-story p,.briefing-story-v13,.briefing-story-v13 p{font-size:20px!important;line-height:1.55!important}
.briefing-card-step{font-size:17px!important}
.briefing-card h2{font-size:28px!important}
.briefing-card p{font-size:18px!important;line-height:1.5!important}
.briefing-explainer-head p{font-size:18px!important;line-height:1.52!important}
.score-preview-label,.briefing-page-two .score-preview-label{font-size:17px!important;line-height:1.25!important}
.score-preview-short,.briefing-page-two .score-preview-short{font-size:19px!important;line-height:1.3!important}
.score-preview-detail,.briefing-page-two .score-preview-detail{font-size:17px!important;line-height:1.45!important}
.briefing-goal-hero .briefing-goal-label{font-size:17px!important}
.briefing-goal-hero h2{font-size:27px!important}
.briefing-goal-hero p{font-size:18px!important;line-height:1.5!important}
.briefing-page-hint{font-size:17px!important}

/* Candidate cards. Even the dense 5x4 founding grid remains readable. */
.candidate-name,.founding-grid .candidate-name{font-size:18px!important}
.guild-badge,.founding-grid .guild-badge,.discussion-guild-badge,.diagnosis-training-badge{font-size:17px!important;line-height:1.25!important;padding:4px 7px!important}
.pathway-badge{font-size:17px!important}
.trait-row,.founding-grid .trait-row{font-size:17px!important;line-height:1.25!important;padding:8px 0!important}
.rating,.founding-grid .rating{font-size:18px!important;line-height:1!important}
.hire-pill,.founding-grid .hire-pill{font-size:17px!important;padding:9px 6px!important}
.abstract-avatar,.founding-grid .abstract-avatar{font-size:17px!important}

/* First classroom pause: restore a genuinely readable selected-team summary. */
.founder-pause-compact .discussion-pause-banner p{font-size:18px!important}
.discussion-score-row span{font-size:17px!important}
.discussion-score-row b{font-size:30px!important}
.founder-average-profile{padding:16px 18px!important}
.founder-average-profile .profile-panel h3,
.discussion-team-profile .profile-panel h3{font-size:21px!important;line-height:1.3!important;margin-bottom:12px!important}
.founder-average-profile .profile-item,
.discussion-team-profile .profile-item,
.profile-panel .profile-item{font-size:17px!important;line-height:1.35!important;margin:9px 0!important}
.founder-average-profile .profile-item b,
.discussion-team-profile .profile-item b,.profile-item b{font-size:17px!important}
.founder-click-hint{font-size:17px!important;line-height:1.35!important}
.founder-name{font-size:19px!important}
.founder-detail-traits span{font-size:17px!important}
.founder-detail-traits b{font-size:23px!important}

/* Training / model explanation. */
.label-training-explainer>p{font-size:17px!important;line-height:1.5!important}
.label-count-card span{font-size:17px!important}
.label-count-card small,.label-ai-card small{font-size:17px!important;line-height:1.4!important}
.label-explainer-callout{font-size:17px!important;line-height:1.5!important}
.training-msg{font-size:18px!important;line-height:1.5!important}
.training-pct{font-size:17px!important}
.ai-ready-card p,.callout{font-size:17px!important;line-height:1.5!important}

/* Scaling / hiring pipeline. */
.mission3-inline-head small{font-size:17px!important}
.mission3-inline-head p{font-size:17px!important;line-height:1.45!important}
.pipeline-flow b{font-size:17px!important}
.pipeline-flow span{font-size:17px!important;line-height:1.3!important}
.pipeline-status{font-size:17px!important;line-height:1.35!important}
.ticker-label,.ticker-simple-note{font-size:17px!important}
.growth-card .panel-kicker,.pipeline-card .panel-kicker,.ticker-card .panel-kicker,
.workforce-average-panel .panel-kicker{font-size:17px!important}
.growth-stat-row small{font-size:17px!important}
.delta{font-size:17px!important}
.mini-result-row span{font-size:17px!important}
.workforce-average-item{font-size:17px!important;line-height:1.3!important}
.workforce-average-item b{font-size:18px!important}
.pipeline-inline-inspect .hire-inspect-open span,.hire-inspect-open span{font-size:17px!important}
.pipeline-inline-inspect .hire-inspect-open small,.hire-inspect-open small{font-size:17px!important;line-height:1.35!important}

/* Guild / LinkedIn interruption. */
.guild-news-context{font-size:20px!important}
.linkedin-news-top b{font-size:18px!important}
.linkedin-news-top span{font-size:17px!important}
.breaking-news-stamp{font-size:17px!important}
.linkedin-news-footer{font-size:17px!important}
.linkedin-news-card>p{font-size:19px!important;line-height:1.55!important}

/* Diagnosis and training-data review. */
.discussion-card small{font-size:17px!important}
.discussion-card p,.discussion-card li{font-size:17px!important;line-height:1.5!important}
.training-example-columns h3{font-size:18px!important}
.training-sample-card .candidate-name,.current-training-card .candidate-name{font-size:18px!important}
.training-sample-card .trait-row,.current-training-card .trait-row{font-size:17px!important;line-height:1.3!important}
.training-sample-card .rating,.current-training-card .rating{font-size:18px!important}
.training-label-pill,.current-training-card .training-label-pill{font-size:17px!important;padding:8px!important}
.diagnosis-ai-decision span{font-size:17px!important}
.diagnosis-ai-decision strong{font-size:17px!important}
.value-impact,.value-impact.full{font-size:17px!important;line-height:1.45!important}
.guild-missing-badge{font-size:17px!important}
.diagnosis-action-button small{font-size:17px!important;line-height:1.45!important}
.diagnosis-discuss-strip{font-size:17px!important;line-height:1.45!important}

/* Fix-the-AI screens, including the previously tiny 'Guild not used' data. */
.fix-choice-card p,.repair-option-copy p,.remove-guild-explainer p{font-size:17px!important;line-height:1.5!important}
.repair-option-copy em{font-size:17px!important}
.no-guild-head .abstract-avatar{font-size:17px!important}
.no-guild-head b{font-size:17px!important}
.ignored-guild{font-size:17px!important;line-height:1.25!important}
.no-guild-traits>span{font-size:17px!important;line-height:1.3!important}
.no-guild-traits .rating-dots{font-size:17px!important}
.no-guild-training-card .training-label-pill{font-size:17px!important;padding:7px!important}
#back-fix-options-btn button{font-size:17px!important;min-height:50px!important}

/* All pop-ups: bigger type and more space, never tiny compressed text. */
.ui-modal{padding:24px!important}
.ui-modal-card{
  width:min(1040px,95vw)!important;
  max-width:1040px!important;
  max-height:92vh!important;
  padding:34px 38px 32px!important;
}
.ui-modal-kicker,.news-kicker,.transition-kicker,.mission8-complete-kicker{font-size:17px!important;line-height:1.3!important}
.ui-modal-card h2{font-size:33px!important;line-height:1.18!important}
.ui-modal-card>p{font-size:19px!important;line-height:1.55!important}
.ui-modal-done,.ui-modal-action{font-size:19px!important;min-height:56px!important}
.hire-modal-card .hire-inspect-stat span{font-size:17px!important}
.hire-modal-card .hire-inspect-stat b{font-size:20px!important}
.hire-modal-card .hire-inspect-stat small{font-size:17px!important;line-height:1.45!important}
.diagnosis-modal-card .trait-row,.training-modal-card .trait-row,.interstate-training-modal-card .trait-row{font-size:17px!important}
.training-modal-card .training-label-pill,.interstate-training-modal-card .training-label-pill{font-size:17px!important}
.interstate-transition-card p,.repaired-pool-modal p,.interstate-result-modal-card p,.mission8-complete-card p{font-size:19px!important;line-height:1.55!important}

/* Interstate and final screens. */
.interstate-intro-card p,.interstate-warning-card p{font-size:18px!important;line-height:1.5!important}
.current-training-card .trait-row{font-size:17px!important}
.final-summary-card span{font-size:17px!important}
.final-company-summary-heading{font-size:17px!important}
.concepts-kicker,.concepts-section-heading span{font-size:17px!important}
.concept-unlocked-tag{font-size:17px!important}
.concept-card p{font-size:18px!important;line-height:1.5!important}
.concept-open-hint{font-size:17px!important}
.concepts-footer-note{font-size:17px!important}
.simulation-link strong{font-size:17px!important}

/* Remaining secondary UI: explicitly audited so older compact rules cannot
   silently re-introduce 9-13px teaching text. */
.side-panel-title small{font-size:17px!important}
.side-panel-title h2{font-size:23px!important}
.gauge-label{font-size:17px!important}.gauge-note{font-size:17px!important}
.game-tip{font-size:17px!important;line-height:1.5!important}
.pathway-split span{font-size:17px!important}.pathway-split b{font-size:29px!important}
.success-card,.warning-card,.fix-selected-card{font-size:17px!important;line-height:1.45!important}
.concept-unlock small{font-size:17px!important}.concept-unlock p{font-size:17px!important;line-height:1.5!important}
.bias-strip-label{font-size:17px!important}.bias-badge{font-size:17px!important}
.pool-split span{font-size:17px!important}.hire-rate{font-size:17px!important}
.standout-panel>div:first-child small{font-size:17px!important}
.rejected-card h4{font-size:17px!important}.rejected-card p,.rejected-card small,.rejected-card>b{font-size:17px!important}
.rate-grid small,.accuracy-grid small{font-size:17px!important}.allocation-labels{font-size:17px!important}
.graduate-only-result small{font-size:17px!important}.graduate-only-result b{font-size:30px!important}
.diagnosis-panel>p,.diagnosis-explainer{font-size:17px!important;line-height:1.5!important}
.diagnosis-title{font-size:17px!important}.diagnosis-title span{font-size:17px!important}
.diagnosis-section h4{font-size:18px!important}.diagnosis-row-head{font-size:17px!important}.diagnosis-row small{font-size:17px!important}.diagnosis-penalty{font-size:17px!important}
.final-stats span,.final-stats-colour .final-stat-card span{font-size:17px!important}.muted{font-size:17px!important;line-height:1.5!important}

/* General Gradio controls. */
button.gr-button,button.gr-button *,
#growth-round-btn button,#post-guild-round-btn button,#post-guild-next-btn button,
#understood-news-btn button,#repair-train-btn button,#redeploy-ai-btn button,
#repair-round-btn button,#start-company-btn button,#lock-founding-btn button,
#continue-training-btn button,#train-ai-btn button,#start-scaling-btn button{
  font-size:17px!important;
  line-height:1.25!important;
}

/* Short laptop screens: keep typography readable; allow scrolling instead of
   reverting to the old 10-13px compression rules. */
@media(min-width:1000px) and (max-height:850px){
  .gradio-container{width:97vw!important;max-width:1680px!important}
  #global-scoreboard .score-tile{min-height:100px!important;padding:13px 16px!important}
  #global-scoreboard .score-label{font-size:17px!important}
  #global-scoreboard .score-number{font-size:32px!important}
  #global-scoreboard .score-sub{font-size:17px!important}
  .mission-banner p{font-size:17px!important}
  .briefing-story,.briefing-story p,.briefing-story-v13,.briefing-story-v13 p{font-size:18px!important}
  .briefing-card p{font-size:17px!important}
  .score-preview-label,.briefing-page-two .score-preview-label{font-size:17px!important}
  .score-preview-short,.briefing-page-two .score-preview-short{font-size:18px!important}
  .score-preview-detail,.briefing-page-two .score-preview-detail{font-size:17px!important}
  .briefing-explainer-head p,.briefing-goal-hero p{font-size:17px!important}
  .founding-grid .candidate-name{font-size:17px!important}
  .founding-grid .trait-row{font-size:17px!important}
  .founding-grid .rating{font-size:17px!important}
  .founding-grid .hire-pill{font-size:17px!important}
}

@media(max-width:900px){
  body > #page-progress-pill,#global-scoreboard #page-progress-pill{font-size:18px!important;min-width:72px!important;height:42px!important;line-height:42px!important}
  #global-scoreboard .score-label{font-size:17px!important}
  #global-scoreboard .score-number{font-size:29px!important}
  #global-scoreboard .score-sub{font-size:17px!important}
  .ui-modal-card{padding:28px 24px!important}
}


"""


# ============================================================
# v18 BALANCED READABILITY OVERRIDE
# ============================================================
EXTRA_CSS += r"""
/* v17's literal 20px-everywhere experiment was intentionally abandoned.
   Preserve hierarchy while keeping all teaching/instructional text readable. */
.gradio-container{font-size:17px!important;}

/* Opening narrative: deliberately large on a 13-inch laptop too. */
.briefing-story,.briefing-story p,
.briefing-story-v13,.briefing-story-v13 p{
  font-size:22px!important;
  line-height:1.58!important;
}

/* Persistent progress indicator: prominent without dominating. */
body > #page-progress-pill,
#global-scoreboard #page-progress-pill{
  font-size:22px!important;
  min-width:82px!important;
  height:46px!important;
  line-height:46px!important;
  padding:0 15px!important;
}

/* Top company dashboard: primary status information. */
#global-scoreboard .score-tile{min-height:108px!important;padding:15px 18px!important;}
#global-scoreboard .score-label{font-size:17px!important;line-height:1.2!important;}
#global-scoreboard .score-number{font-size:36px!important;}
#global-scoreboard .score-sub,#global-scoreboard .score-denom{font-size:17px!important;}
#global-scoreboard .score-icon{width:54px!important;height:54px!important;}
#global-scoreboard .score-icon svg{width:31px!important;height:31px!important;}

/* Briefing/dashboard explanation hierarchy. */
.briefing-card p{font-size:18px!important;line-height:1.5!important;}
.briefing-explainer-head p,.briefing-goal-hero p{font-size:18px!important;line-height:1.55!important;}
.score-preview-label{font-size:17px!important;}
.score-preview-short{font-size:18px!important;}
.score-preview-detail{font-size:17px!important;line-height:1.45!important;}

/* Ordinary teaching copy. */
.mission-banner p,.discussion-pause-banner p,.round-comparison-card p,
.breaking-news-card p,.interstate-intro-card p,.interstate-warning-card p,
.ai-ready-card p,.label-training-explainer>p,.discussion-card p,.discussion-card li{
  font-size:18px!important;
  line-height:1.5!important;
}

/* Candidate/card content should be readable but remain compact. */
.candidate-name,.discussion-hire-name{font-size:19px!important;}
.trait-row,.discussion-trait span{font-size:17px!important;}
.rating,.discussion-rating{font-size:18px!important;}
.hire-pill{font-size:17px!important;}
.guild-badge,.pathway-badge,.discussion-guild-badge{font-size:17px!important;}

/* First classroom pause: the selected-team profile was still too small. */
.discussion-team-profile .profile-panel h3{font-size:22px!important;}
.discussion-team-profile .profile-item,
.discussion-team-profile .profile-item b{font-size:18px!important;}
.discussion-score-row span{font-size:17px!important;}
.discussion-score-row b{font-size:30px!important;}

/* Hiring pipeline / company cards. */
.panel-kicker,.status-kicker,.round-comparison-kicker{font-size:17px!important;}
.pipeline-flow b{font-size:17px!important;}
.pipeline-flow span{font-size:17px!important;line-height:1.3!important;}
.pipeline-status{font-size:17px!important;}
.ticker-label,.ticker-simple-note{font-size:17px!important;}
.growth-stat-row small,.mini-result-row span{font-size:17px!important;}
.workforce-average-item,.hire-inspect-stat span,.hire-inspect-stat small{font-size:17px!important;}
.workforce-average-item b,.hire-inspect-stat b{font-size:17px!important;}

/* Buttons/actions. */
button.gr-button,button.gr-button *,
#growth-round-btn button,#post-guild-round-btn button,#post-guild-next-btn button,
#understood-news-btn button,#repair-train-btn button,#redeploy-ai-btn button,
#repair-round-btn button,#start-company-btn button,#lock-founding-btn button,
#continue-training-btn button,#train-ai-btn button,#start-scaling-btn button{
  font-size:18px!important;
  line-height:1.25!important;
}

/* Pop-ups: larger than the old compact version, but not 20px for every tiny tag. */
.ui-modal-card{
  width:min(1050px,94vw)!important;
  max-width:1050px!important;
  padding:32px 36px!important;
}
.ui-modal-card h2{font-size:31px!important;line-height:1.18!important;}
.ui-modal-card p,.ui-modal-card li{font-size:18px!important;line-height:1.52!important;}
.ui-modal-card .candidate-name{font-size:19px!important;}
.ui-modal-card .trait-row,.ui-modal-card .profile-item{font-size:17px!important;}
.ui-modal-card small,.ui-modal-card .panel-kicker,.ui-modal-card .round-comparison-kicker{font-size:17px!important;}
.ui-modal-done,.ui-modal-action{font-size:18px!important;min-height:56px!important;}

/* Final concepts / report. */
.final-stats span,.final-stat-card span{font-size:17px!important;}
.final-stats b,.final-stat-card b{font-size:28px!important;}
.concept-card p{font-size:18px!important;}
.concept-open-hint,.concepts-footer-note{font-size:17px!important;}

/* MacBook Air / short laptop: DO NOT shrink the opening story or dashboard. */
@media(min-width:1000px) and (max-height:900px){
  .briefing-story,.briefing-story p,
  .briefing-story-v13,.briefing-story-v13 p{font-size:22px!important;}
  body > #page-progress-pill,#global-scoreboard #page-progress-pill{font-size:22px!important;height:46px!important;min-width:82px!important;}
  #global-scoreboard .score-label{font-size:17px!important;}
  #global-scoreboard .score-number{font-size:36px!important;}
  #global-scoreboard .score-sub,#global-scoreboard .score-denom{font-size:17px!important;}
  .founding-grid .candidate-name{font-size:18px!important;}
  .founding-grid .trait-row{font-size:17px!important;}
  .founding-grid .rating{font-size:18px!important;}
  .founding-grid .hire-pill{font-size:17px!important;}
}
"""


# ============================================================
# v19 TRAINING-DATA MODAL LAYOUT + FONT STABILITY
# ============================================================
EXTRA_CSS += r"""
/* Stack Hire and Do not hire groups vertically. The previous layout squeezed
   two separate 3-card grids side-by-side, which became unstable once the text
   was enlarged for readability. */
.training-modal-card,
.interstate-training-modal-card{
  width:min(1180px,96vw)!important;
  max-width:1180px!important;
  padding:34px 38px 32px!important;
}

.training-modal-card .training-example-columns,
.interstate-training-modal-card .training-example-columns,
.training-modal-card .interstate-training-review .training-example-columns,
.interstate-training-modal-card .interstate-training-review .training-example-columns{
  display:grid!important;
  grid-template-columns:1fr!important;
  gap:24px!important;
}

.training-modal-card .training-example-columns>div,
.interstate-training-modal-card .training-example-columns>div{
  min-width:0!important;
  padding:18px 20px!important;
  border-radius:18px!important;
  background:#f7f9fd!important;
  border:1px solid #dfe6f1!important;
}

.training-modal-card .training-example-columns h3,
.interstate-training-modal-card .training-example-columns h3{
  font-size:21px!important;
  line-height:1.25!important;
  margin:0 0 13px!important;
  color:#17223b!important;
}

.training-modal-card .training-sample-grid,
.interstate-training-modal-card .training-sample-grid{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(0,1fr))!important;
  gap:16px!important;
  width:100%!important;
}

.training-modal-card .training-sample-card,
.interstate-training-modal-card .training-sample-card{
  min-width:0!important;
  width:auto!important;
  min-height:0!important;
  padding:16px!important;
  border-radius:16px!important;
  overflow:visible!important;
}

.training-modal-card .training-sample-card .candidate-head,
.interstate-training-modal-card .training-sample-card .candidate-head{
  min-width:0!important;
  align-items:center!important;
}

.training-modal-card .training-sample-card .candidate-name,
.interstate-training-modal-card .training-sample-card .candidate-name{
  font-size:20px!important;
  line-height:1.2!important;
  white-space:normal!important;
  overflow:visible!important;
}

/* Force a stable font inside the training-data pop-ups. This removes the odd
   browser-dependent capital-A glyph seen on some Macs. */
.training-modal-card,
.training-modal-card *,
.interstate-training-modal-card,
.interstate-training-modal-card *{
  font-family:Arial,Helvetica,sans-serif!important;
  font-style:normal!important;
  font-variant:normal!important;
  font-variant-caps:normal!important;
  font-feature-settings:normal!important;
  font-synthesis:none!important;
}

.training-modal-card .candidate-name::first-letter,
.interstate-training-modal-card .candidate-name::first-letter,
.training-modal-card h2::first-letter,
.training-modal-card h3::first-letter,
.interstate-training-modal-card h2::first-letter,
.interstate-training-modal-card h3::first-letter{
  font-family:inherit!important;
  font-size:1em!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  letter-spacing:inherit!important;
}

.training-modal-card .trait-row,
.interstate-training-modal-card .trait-row{
  display:grid!important;
  grid-template-columns:1fr!important;
  gap:5px!important;
  font-size:17px!important;
  padding:9px 0!important;
}

.training-modal-card .rating,
.interstate-training-modal-card .rating{
  font-size:19px!important;
  white-space:nowrap!important;
}

.training-modal-card .training-label-pill,
.interstate-training-modal-card .training-label-pill{
  font-size:17px!important;
  min-height:38px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}

@media(max-width:900px){
  .training-modal-card .training-sample-grid,
  .interstate-training-modal-card .training-sample-grid{
    grid-template-columns:1fr!important;
  }
  .training-modal-card,
  .interstate-training-modal-card{
    padding:28px 24px!important;
  }
}
"""


# ============================================================
# v20 GENTLE READABILITY LIFT
# ============================================================
EXTRA_CSS += r"""
/* v20 sits deliberately between the balanced v18/v19 scale and the oversized
   20px-everywhere experiment. Increase text people actively read by ~1px,
   while preserving smaller decorative kickers for hierarchy. */

.gradio-container{font-size:18px!important;}

/* Keep the opening story large and unchanged. */
.briefing-story,.briefing-story p,
.briefing-story-v13,.briefing-story-v13 p{
  font-size:22px!important;
  line-height:1.60!important;
}

/* Progress + top dashboard: slightly more prominent. */
body > #page-progress-pill,
#global-scoreboard #page-progress-pill{
  font-size:23px!important;
  min-width:84px!important;
  height:48px!important;
  line-height:48px!important;
}
#global-scoreboard .score-label{font-size:18px!important;}
#global-scoreboard .score-number{font-size:37px!important;}
#global-scoreboard .score-sub,#global-scoreboard .score-denom{font-size:18px!important;}

/* Briefing content. */
.briefing-card p{font-size:19px!important;line-height:1.5!important;}
.briefing-explainer-head p,.briefing-goal-hero p{font-size:19px!important;line-height:1.55!important;}
.score-preview-label{font-size:17px!important;}
.score-preview-short{font-size:19px!important;}
.score-preview-detail{font-size:17px!important;line-height:1.48!important;}

/* Ordinary instructional and discussion copy. */
.mission-banner p,.discussion-pause-banner p,.round-comparison-card p,
.breaking-news-card p,.interstate-intro-card p,.interstate-warning-card p,
.ai-ready-card p,.label-training-explainer>p,.discussion-card p,.discussion-card li,
.discussion-prompts,.diagnosis-discuss-strip{
  font-size:19px!important;
  line-height:1.52!important;
}

/* Candidate and training cards. */
.candidate-name,.discussion-hire-name{font-size:20px!important;}
.trait-row,.discussion-trait span{font-size:17px!important;}
.rating,.discussion-rating{font-size:19px!important;}
.hire-pill{font-size:17px!important;}
.guild-badge,.pathway-badge,.discussion-guild-badge{font-size:17px!important;}

/* First classroom pause. */
.discussion-team-profile .profile-panel h3{font-size:23px!important;}
.discussion-team-profile .profile-item,
.discussion-team-profile .profile-item b{font-size:19px!important;}
.discussion-score-row span{font-size:17px!important;}

/* Hiring pipeline / company cards. */
.pipeline-flow b{font-size:18px!important;}
.pipeline-flow span{font-size:17px!important;line-height:1.35!important;}
.pipeline-status{font-size:17px!important;}
.ticker-label,.ticker-simple-note{font-size:17px!important;}
.growth-stat-row small,.mini-result-row span{font-size:17px!important;}
.workforce-average-item,.hire-inspect-stat span,.hire-inspect-stat small{font-size:17px!important;}
.workforce-average-item b,.hire-inspect-stat b{font-size:18px!important;}

/* Side panels and explanatory cards. */
.gauge-label{font-size:17px!important;}
.gauge-note{font-size:17px!important;}
.game-tip,.success-card,.warning-card,.fix-selected-card{font-size:17px!important;line-height:1.5!important;}
.pathway-split span{font-size:17px!important;}
.concept-unlock p{font-size:17px!important;}
.bias-badge{font-size:17px!important;}

/* Buttons: easy to target without becoming oversized. */
button.gr-button,button.gr-button *,
#growth-round-btn button,#post-guild-round-btn button,#post-guild-next-btn button,
#understood-news-btn button,#repair-train-btn button,#redeploy-ai-btn button,
#repair-round-btn button,#start-company-btn button,#lock-founding-btn button,
#continue-training-btn button,#train-ai-btn button,#start-scaling-btn button{
  font-size:19px!important;
}

/* Pop-ups: use the larger window to support 19px body text. */
.ui-modal-card{
  width:min(1100px,95vw)!important;
  max-width:1100px!important;
  padding:34px 38px!important;
}
.ui-modal-card h2{font-size:32px!important;}
.ui-modal-card p,.ui-modal-card li{font-size:19px!important;line-height:1.55!important;}
.ui-modal-card .candidate-name{font-size:20px!important;}
.ui-modal-card .trait-row,.ui-modal-card .profile-item{font-size:17px!important;}
.ui-modal-card small,.ui-modal-card .panel-kicker,.ui-modal-card .round-comparison-kicker{font-size:17px!important;}
.ui-modal-done,.ui-modal-action{font-size:19px!important;min-height:58px!important;}

/* Training-data pop-ups keep the v19 stable layout, just slightly larger text. */
.training-modal-card .training-example-columns h3,
.interstate-training-modal-card .training-example-columns h3{
  font-size:22px!important;
}
.training-modal-card .training-sample-card .candidate-name,
.interstate-training-modal-card .training-sample-card .candidate-name{
  font-size:20px!important;
}
.training-modal-card .trait-row,
.interstate-training-modal-card .trait-row{
  font-size:17px!important;
}
.training-modal-card .rating,
.interstate-training-modal-card .rating{
  font-size:20px!important;
}
.training-modal-card .training-label-pill,
.interstate-training-modal-card .training-label-pill{
  font-size:17px!important;
}

/* Final screen. */
.final-stats span,.final-stat-card span{font-size:17px!important;}
.concept-card p{font-size:19px!important;line-height:1.52!important;}
.concept-open-hint,.concepts-footer-note{font-size:17px!important;}

/* Short laptop: preserve these sizes rather than compressing them again. */
@media(min-width:1000px) and (max-height:900px){
  .briefing-story,.briefing-story p,
  .briefing-story-v13,.briefing-story-v13 p{font-size:22px!important;}
  #global-scoreboard .score-label{font-size:18px!important;}
  #global-scoreboard .score-number{font-size:37px!important;}
  #global-scoreboard .score-sub,#global-scoreboard .score-denom{font-size:18px!important;}
  body > #page-progress-pill,#global-scoreboard #page-progress-pill{font-size:23px!important;}
  .founding-grid .candidate-name{font-size:19px!important;}
  .founding-grid .trait-row{font-size:17px!important;}
  .founding-grid .rating{font-size:19px!important;}
  .founding-grid .hire-pill{font-size:17px!important;}
}
"""


# ============================================================
# v21 STRICT 17PX READABILITY FLOOR
# ============================================================
EXTRA_CSS += r"""
/* Browser defaults can shrink semantic <small> text even when the surrounding
   component is 18–19px. Prevent silent font-size reductions. */
.gradio-container small{
  font-size:17px!important;
  line-height:1.4!important;
}

/* Form controls do not always inherit the surrounding font in every browser. */
.gradio-container button,
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container label{
  font-size:max(17px,1em);
}

/* Preserve the intended larger scales from v20. */
.briefing-story,.briefing-story p,
.briefing-story-v13,.briefing-story-v13 p{
  font-size:22px!important;
}
body > #page-progress-pill,
#global-scoreboard #page-progress-pill{
  font-size:23px!important;
}
#global-scoreboard .score-label,
#global-scoreboard .score-sub,
#global-scoreboard .score-denom{
  font-size:18px!important;
}
#global-scoreboard .score-number{
  font-size:37px!important;
}

/* Do not allow old short-laptop rules to shrink readable text again. */
@media(min-width:1000px) and (max-height:900px){
  .gradio-container small{font-size:17px!important}
  .briefing-story,.briefing-story p,
  .briefing-story-v13,.briefing-story-v13 p{font-size:22px!important}
}
"""


# ============================================================
# v22 STABLE FONT FOR NEWS / TRANSITION HEADINGS
# ============================================================
EXTRA_CSS += r"""
/* Some Mac/browser font combinations render isolated capitals (especially A)
   oddly in Gradio's default display font. Use a conservative font throughout
   alert and transition modals so headings such as "Applicant pool exhausted"
   render consistently. */
.news-modal-card,
.news-modal-card *,
.scaling-finish-modal,
.scaling-finish-modal *,
.no-hire-round-card,
.no-hire-round-card *,
.repaired-pool-modal,
.repaired-pool-modal *,
.interstate-result-modal-card,
.interstate-result-modal-card *,
.mission8-complete-card,
.mission8-complete-card *,
.breaking-news-card,
.breaking-news-card *{
  font-family:Arial,Helvetica,sans-serif!important;
  font-style:normal!important;
  font-variant:normal!important;
  font-variant-caps:normal!important;
  font-feature-settings:normal!important;
  font-synthesis:none!important;
  text-transform:none;
}

.news-modal-card h2,
.scaling-finish-modal h2,
.no-hire-round-card h2,
.repaired-pool-modal h2,
.interstate-result-modal-card h2,
.mission8-complete-card h2,
.breaking-news-card h1{
  font-family:Arial,Helvetica,sans-serif!important;
  font-weight:800!important;
  letter-spacing:0!important;
}

.news-modal-card h2::first-letter,
.scaling-finish-modal h2::first-letter,
.no-hire-round-card h2::first-letter,
.repaired-pool-modal h2::first-letter,
.interstate-result-modal-card h2::first-letter,
.mission8-complete-card h2::first-letter,
.breaking-news-card h1::first-letter{
  font-family:inherit!important;
  font-size:1em!important;
  line-height:inherit!important;
  font-weight:inherit!important;
  letter-spacing:inherit!important;
}

/* Defensive fallback for the old in-page event heading, even though the
   current wrapper replaces it with the modal. */
.event-trigger-card h3,
.event-trigger-card h3::first-letter{
  font-family:Arial,Helvetica,sans-serif!important;
  font-size:inherit;
  font-weight:800!important;
  font-variant:normal!important;
  font-feature-settings:normal!important;
  font-synthesis:none!important;
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=7862)
    parser.add_argument('--root-path', default=os.getenv('GRADIO_ROOT_PATH') or None)
    parser.add_argument('--share', action='store_true')
    parser.add_argument(
        '--concurrency',
        type=int,
        default=int(os.getenv('QUT001_CONCURRENCY', '64')),
        help='Default concurrent queued callbacks per event listener (default: 64).',
    )
    parser.add_argument(
        '--queue-size',
        type=int,
        default=int(os.getenv('QUT001_QUEUE_SIZE', '500')),
        help='Maximum number of waiting queued jobs (default: 500).',
    )
    parser.add_argument(
        '--max-threads',
        type=int,
        default=int(os.getenv('QUT001_MAX_THREADS', '40')),
        help='Gradio worker thread-pool size for short synchronous callbacks (default: 40).',
    )
    parser.add_argument(
        '--state-session-capacity',
        type=int,
        default=int(os.getenv('QUT001_STATE_SESSION_CAPACITY', '2000')),
        help='Maximum number of Gradio session states retained in memory (default: 2000).',
    )
    return parser.parse_args()



if __name__ == '__main__':
    args = parse_args()

    if args.concurrency < 1:
        raise ValueError('--concurrency must be at least 1.')
    if args.queue_size < 1:
        raise ValueError('--queue-size must be at least 1.')
    if args.max_threads < 1:
        raise ValueError('--max-threads must be at least 1.')
    if args.state_session_capacity < 1:
        raise ValueError('--state-session-capacity must be at least 1.')

    # Explicitly configure the queue rather than relying on Gradio's per-listener
    # default concurrency. Long animation callbacks are async in v23, so students
    # waiting between frames no longer occupy a worker thread.
    app.demo.queue(
        max_size=args.queue_size,
        default_concurrency_limit=args.concurrency,
    )

    app.demo.launch(
        css=app.CSS + EXTRA_CSS,
        server_name=args.host,
        server_port=args.port,
        root_path=args.root_path,
        share=args.share,
        max_threads=args.max_threads,
        state_session_capacity=args.state_session_capacity,
    )
