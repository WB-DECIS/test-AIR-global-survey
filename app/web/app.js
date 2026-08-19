const STORAGE_KEY = "air-survey-review-v1";
const app = document.querySelector("#app");
const state = {
  manifest: null,
  tester: null,
  currentIndex: 0,
  responses: {},
  generalFeedback: {},
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function saveState() {
  sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      currentIndex: state.currentIndex,
      responses: state.responses,
      generalFeedback: state.generalFeedback,
      started: true,
    }),
  );
}

function restoreState() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
    if (!saved || saved.started !== true) {
      return false;
    }
    state.currentIndex = Number.isInteger(saved.currentIndex) ? saved.currentIndex : 0;
    state.responses = saved.responses || {};
    state.generalFeedback = saved.generalFeedback || {};
    return true;
  } catch (_error) {
    sessionStorage.removeItem(STORAGE_KEY);
    return false;
  }
}

async function getJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let body = null;
  try {
    body = await response.json();
  } catch (_error) {
    body = null;
  }
  if (!response.ok) {
    const message = body?.detail || "Something went wrong. Please try again.";
    throw new Error(message);
  }
  return body;
}

function renderGate(message = "") {
  app.innerHTML = `
    <section class="page page-narrow">
      <span class="kicker">Tester access</span>
      <h1>Global survey review</h1>
      <p class="lede">A quick, focused pass through the draft global survey. Your email is checked against the approved pilot list.</p>
      <form class="access-form" id="access-form">
        <label class="field-label" for="email">Approved tester email</label>
        <input class="field-input" id="email" name="email" type="email" autocomplete="email" required />
        <div class="action-row">
          <button class="primary-action" type="submit">Continue</button>
        </div>
        ${message ? `<p class="error-message" role="alert">${escapeHtml(message)}</p>` : ""}
      </form>
    </section>
  `;
  document.querySelector("#access-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    try {
      const formData = new FormData(form);
      const access = await getJson("api/access", {
        method: "POST",
        body: JSON.stringify({ email: formData.get("email") }),
      });
      state.tester = access.tester;
      state.manifest = await getJson("api/manifest");
      state.currentIndex = 0;
      state.responses = {};
      state.generalFeedback = {};
      sessionStorage.removeItem(STORAGE_KEY);
      renderIntro();
    } catch (error) {
      renderGate(error.message);
    }
  });
}

function renderIntro() {
  app.innerHTML = `
    <section class="page intro-layout">
      <div>
        <span class="kicker">You are testing the draft</span>
        <h1>Make every question earn its place.</h1>
        <p class="lede">The global survey is a short screening tool for national statistical offices. It is designed to show where an office may be ready to use AI and where deeper assessment or capacity support could help.</p>
        <p class="lede">You will review the wording, response options, and instructions. Your feedback will be recorded for survey improvement. You will not be asked to answer the survey for an NSO.</p>
        <div class="action-row">
          <button class="primary-action" id="start-review" type="button">Start review</button>
        </div>
      </div>
      <aside class="intro-note">
        <strong>About 10-20 minutes</strong>
        <p>Choose one quick judgment on each card. Notes are optional, so you can keep moving when you have nothing to add.</p>
      </aside>
    </section>
  `;
  document.querySelector("#start-review").addEventListener("click", () => {
    state.currentIndex = 0;
    state.responses = {};
    state.generalFeedback = {};
    saveState();
    renderReview();
  });
}

function renderSourceContent(point) {
  const options = point.options?.length
    ? `<div class="source-options"><ul>${point.options
        .map((option) => `<li>${escapeHtml(option)}</li>`)
        .join("")}</ul></div>`
    : "";
  const parts = point.parts?.length
    ? point.parts
        .map(
          (part) => `
            <div class="source-part">
              <h3>${escapeHtml(part.label)}</h3>
              <ul>${part.options
                .map((option) => `<li>${escapeHtml(option)}</li>`)
                .join("")}</ul>
            </div>
          `,
        )
        .join("")
    : "";
  const note = point.note
    ? `<p class="source-note">${escapeHtml(point.note)}</p>`
    : "";
  return `${options}${parts}${note}`;
}

function renderJudgments(point, response) {
  return state.manifest.judgment_options
    .map((judgment, index) => {
      const inputId = `judgment-${point.id}-${index}`;
      const checked = response?.judgment === judgment ? "checked" : "";
      return `
        <div class="judgment-option">
          <input id="${inputId}" name="judgment" type="radio" value="${escapeHtml(judgment)}" ${checked} />
          <label for="${inputId}">${escapeHtml(judgment)}</label>
        </div>
      `;
    })
    .join("");
}

function captureCurrentResponse() {
  const point = state.manifest.review_points[state.currentIndex];
  const selected = document.querySelector("input[name=judgment]:checked");
  if (!selected) {
    return false;
  }
  const comment = document.querySelector("#comment").value.trim();
  state.responses[point.id] = {
    id: point.id,
    section: point.section,
    type: point.type,
    judgment: selected.value,
    comment: comment || null,
  };
  return true;
}

function renderReview() {
  const point = state.manifest.review_points[state.currentIndex];
  const response = state.responses[point.id];
  const total = state.manifest.review_points.length;
  const progress = ((state.currentIndex + 1) / total) * 100;
  app.innerHTML = `
    <section class="page review-page">
      <div class="progress-line">
        <span>Review item ${state.currentIndex + 1} of ${total}</span>
        <span>${escapeHtml(point.section)}</span>
      </div>
      <div class="progress-track" aria-label="Review progress">
        <div class="progress-bar" style="width: ${progress}%"></div>
      </div>
      <article class="review-card" data-review-id="${escapeHtml(point.id)}">
        <div class="review-meta">
          <span class="review-id">${escapeHtml(point.id)}</span>
          <span>${escapeHtml(point.type)}</span>
        </div>
        <h2>${escapeHtml(point.title)}</h2>
        <p class="review-prompt">${escapeHtml(point.prompt)}</p>
        ${renderSourceContent(point)}
        <div class="feedback-block">
          <div class="feedback-heading">How is this review point?</div>
          <div class="judgment-grid" role="radiogroup" aria-label="Tester judgment">
            ${renderJudgments(point, response)}
          </div>
          <label class="comment-label" for="comment">Optional note</label>
          <textarea class="comment-input" id="comment" maxlength="2000" placeholder="Add a detail only if it would help revise this item.">${escapeHtml(response?.comment || "")}</textarea>
        </div>
        <div class="review-actions">
          <button class="secondary-action" id="back" type="button" ${state.currentIndex === 0 ? "disabled" : ""}>Back</button>
          <button class="primary-action" id="next" type="button" ${response?.judgment ? "" : "disabled"}>${state.currentIndex === total - 1 ? "Continue to final feedback" : "Next"}</button>
        </div>
      </article>
    </section>
  `;
  document.querySelectorAll("input[name=judgment]").forEach((input) => {
    input.addEventListener("change", () => {
      document.querySelector("#next").disabled = false;
      captureCurrentResponse();
      saveState();
    });
  });
  document.querySelector("#comment").addEventListener("input", () => {
    if (document.querySelector("input[name=judgment]:checked")) {
      captureCurrentResponse();
      saveState();
    }
  });
  document.querySelector("#back").addEventListener("click", () => {
    if (state.currentIndex > 0) {
      captureCurrentResponse();
      saveState();
      state.currentIndex -= 1;
      saveState();
      renderReview();
    }
  });
  document.querySelector("#next").addEventListener("click", () => {
    if (!captureCurrentResponse()) {
      return;
    }
    saveState();
    if (state.currentIndex === total - 1) {
      renderGeneralFeedback();
      return;
    }
    state.currentIndex += 1;
    saveState();
    renderReview();
  });
}

const GENERAL_PROMPTS = [
  ["missing_questions", "Were any important questions missing?", "What should the survey ask that it does not ask now?"],
  ["survey_length", "How was the length?", "Was the survey too long, too short, or about right?"],
  ["difficult_items", "Which items were difficult or ambiguous?", "Mention any wording or response options that were hard to interpret."],
  ["duplicative_items", "Did any items feel duplicative?", "Tell us which items seemed to measure the same thing."],
  ["translation_terms", "Which terms need plainer wording or translation guidance?", "Name terms that may be difficult across languages or contexts."],
  ["product_selection", "How was the Q8-Q11 product instruction?", "Could you use the same public data product for all four items?"],
];

function renderGeneralFeedback() {
  const promptFields = GENERAL_PROMPTS.map(
    ([key, label, help]) => `
      <div class="prompt-group">
        <label class="prompt-label" for="${key}">${label}</label>
        <p class="prompt-help">${help}</p>
        <textarea class="prompt-input" id="${key}" maxlength="3000">${escapeHtml(state.generalFeedback[key] || "")}</textarea>
      </div>
    `,
  ).join("");
  app.innerHTML = `
    <section class="page page-narrow">
      <span class="kicker">Final page</span>
      <h2>One last thing.</h2>
      <p class="lede">Everything below is optional. A few words are useful; a blank page is fine too.</p>
      <form class="prompt-stack" id="general-form">
        ${promptFields}
        <div class="prompt-group">
          <label class="prompt-label" for="overall_burden">Overall burden</label>
          <p class="prompt-help">How did the full review feel?</p>
          <select class="prompt-select" id="overall_burden">
            <option value="">Choose one</option>
            <option value="low" ${state.generalFeedback.overall_burden === "low" ? "selected" : ""}>Low</option>
            <option value="moderate" ${state.generalFeedback.overall_burden === "moderate" ? "selected" : ""}>Moderate</option>
            <option value="high" ${state.generalFeedback.overall_burden === "high" ? "selected" : ""}>High</option>
          </select>
        </div>
        <div class="prompt-group">
          <label class="prompt-label" for="other_comments">Anything else?</label>
          <textarea class="prompt-input" id="other_comments" maxlength="3000">${escapeHtml(state.generalFeedback.other_comments || "")}</textarea>
        </div>
        <div class="review-actions">
          <button class="secondary-action" id="back-to-review" type="button">Back to review</button>
          <button class="primary-action" id="submit-feedback" type="submit">Submit feedback</button>
        </div>
        <p class="submit-error" id="submit-error" role="alert" hidden></p>
      </form>
    </section>
  `;
  document.querySelectorAll("#general-form textarea, #overall_burden").forEach((field) => {
    field.addEventListener("input", () => {
      state.generalFeedback[field.id] = field.value;
      saveState();
    });
    field.addEventListener("change", () => {
      state.generalFeedback[field.id] = field.value;
      saveState();
    });
  });
  document.querySelector("#back-to-review").addEventListener("click", () => {
    renderReview();
  });
  document.querySelector("#general-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = document.querySelector("#submit-feedback");
    const error = document.querySelector("#submit-error");
    button.disabled = true;
    error.hidden = true;
    GENERAL_PROMPTS.forEach(([key]) => {
      state.generalFeedback[key] = document.querySelector(`#${key}`).value.trim() || null;
    });
    state.generalFeedback.overall_burden = document.querySelector("#overall_burden").value || null;
    state.generalFeedback.other_comments = document.querySelector("#other_comments").value.trim() || null;
    try {
      const result = await getJson("api/submissions", {
        method: "POST",
        body: JSON.stringify({
          submission_id: crypto.randomUUID(),
          review_points: state.manifest.review_points.map((point) => state.responses[point.id]),
          general_feedback: state.generalFeedback,
        }),
      });
      sessionStorage.removeItem(STORAGE_KEY);
      renderComplete(result.submission_id);
    } catch (submitError) {
      error.textContent = submitError.message;
      error.hidden = false;
      button.disabled = false;
      saveState();
    }
  });
}

function renderComplete(submissionId) {
  app.innerHTML = `
    <section class="page page-narrow">
      <div class="confirmation-mark" aria-hidden="true">OK</div>
      <span class="kicker">Thank you</span>
      <h2>Feedback recorded.</h2>
      <p class="lede">Your review has been saved for the survey team. Your reference is ${escapeHtml(submissionId)}.</p>
    </section>
  `;
}

async function bootstrap() {
  try {
    const session = await getJson("api/session");
    state.tester = session.tester;
    state.manifest = await getJson("api/manifest");
    if (restoreState()) {
      renderReview();
    } else {
      renderIntro();
    }
  } catch (_error) {
    renderGate();
  }
}

bootstrap();
