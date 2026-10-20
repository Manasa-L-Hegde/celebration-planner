/* Celebration & Event Planner front end.
 * All server text is inserted with textContent (never innerHTML) to prevent XSS. */
(function () {
  "use strict";

  const FIELDS = ["event_type", "title", "guest_count", "budget", "event_date", "city", "preferences"];
  const form = document.getElementById("plan-form");
  const layout = document.getElementById("main");
  const submitBtn = document.getElementById("submit-btn");
  const submitLabel = submitBtn.querySelector(".btn-label");
  const statusEl = document.getElementById("status");
  const summaryBox = document.getElementById("error-summary");
  const errorList = document.getElementById("error-list");
  const results = document.getElementById("results");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let currentPlan = null;
  let spy = null;

  const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
  const formatInr = (value) => inr.format(value);
  const dateFmt = new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" });

  /* ---------- small helpers ---------- */
  function el(tag, props, children) {
    const node = document.createElement(tag);
    Object.entries(props || {}).forEach(([key, value]) => {
      if (key === "text") node.textContent = value;
      else if (key === "class") node.className = value;
      else node.setAttribute(key, value);
    });
    (children || []).forEach((child) => node.appendChild(child));
    return node;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function parseDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d);
  }

  function todayIso() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  }

  /** Animate a number up to its final value. The final text is always set, even if animation is skipped. */
  function countUp(node, target, format) {
    node.textContent = format(target);
    if (reduceMotion || target === 0) return;
    const duration = 700;
    const start = performance.now();
    node.textContent = format(0);
    function tick(now) {
      const progress = Math.min(1, (now - start) / duration);
      node.textContent = format(Math.round(target * (1 - Math.pow(1 - progress, 3))));
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    setTimeout(() => { node.textContent = format(target); }, duration + 120);
  }

  /* ---------- theme ---------- */
  const themeBtn = document.getElementById("theme-btn");
  const themeIcon = document.getElementById("theme-icon");

  function currentTheme() {
    const forced = document.documentElement.getAttribute("data-theme");
    if (forced) return forced;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function syncThemeButton() {
    const dark = currentTheme() === "dark";
    themeBtn.setAttribute("aria-pressed", String(dark));
    themeIcon.textContent = dark ? "\u2600" : "\u263E";
  }

  themeBtn.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (err) { /* storage unavailable */ }
    syncThemeButton();
  });
  syncThemeButton();

  /* ---------- event type placeholders ---------- */
  function syncPlaceholders() {
    const chosen = form.querySelector("input[name=event_type]:checked");
    if (!chosen) return;
    document.getElementById("title").placeholder = chosen.dataset.placeholder || "";
    document.getElementById("preferences").placeholder = chosen.dataset.prefs || "";
  }
  form.querySelectorAll("input[name=event_type]").forEach((radio) => radio.addEventListener("change", syncPlaceholders));
  syncPlaceholders();

  /* ---------- quick sample presets ---------- */
  function futureDateIso(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  const PRESETS = {
    wedding: {
      type: "wedding",
      title: "Aarav and Diya's Royal Wedding",
      guest_count: 250,
      budget: 1500000,
      days: 60,
      city: "Bengaluru",
      preferences: "Royal vegetarian feast, outdoor mandap, marigold & jasmine floral styling, live Carnatic music",
    },
    birthday: {
      type: "birthday",
      title: "Riya's 10th Safari Birthday Adventure",
      guest_count: 45,
      budget: 65000,
      days: 20,
      city: "Mumbai",
      preferences: "Jungle theme cake, interactive party games, magician, kids snack boxes",
    },
    community: {
      type: "community",
      title: "Grand Diwali Cultural Utsav 2026",
      guest_count: 500,
      budget: 450000,
      days: 45,
      city: "Pune",
      preferences: "Open amphitheatre, community rangoli competition, cultural drama, step-free access",
    },
  };

  document.querySelectorAll(".preset-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const preset = PRESETS[btn.dataset.preset];
      if (!preset) return;
      const radio = form.querySelector(`input[name=event_type][value="${preset.type}"]`);
      if (radio) {
        radio.checked = true;
        syncPlaceholders();
      }
      document.getElementById("title").value = preset.title;
      document.getElementById("guest_count").value = preset.guest_count;
      document.getElementById("budget").value = preset.budget;
      document.getElementById("event_date").value = futureDateIso(preset.days);
      document.getElementById("city").value = preset.city;
      document.getElementById("preferences").value = preset.preferences;
      clearErrors();
      statusEl.textContent = `Loaded sample ${preset.type} plan. Ready to generate!`;
    });
  });

  /* ---------- errors ---------- */
  function fieldControl(name) {
    return document.getElementById(name);
  }

  function clearErrors() {
    summaryBox.hidden = true;
    clear(errorList);
    FIELDS.forEach((name) => {
      const msg = document.getElementById(name + "-error");
      if (msg) { msg.hidden = true; msg.textContent = ""; }
      const control = fieldControl(name);
      if (control) control.removeAttribute("aria-invalid");
    });
  }

  function showErrors(details) {
    clearErrors();
    details.forEach((detail) => {
      const name = FIELDS.includes(detail.field) ? detail.field : null;
      const item = el("li");
      if (name) {
        const label = document.querySelector(`label[for="${name}"]`);
        const link = el("a", { href: "#" + name, text: `${label ? label.textContent : name}: ${detail.message}` });
        link.addEventListener("click", (event) => {
          event.preventDefault();
          fieldControl(name).focus();
        });
        item.appendChild(link);
        const msg = document.getElementById(name + "-error");
        msg.textContent = detail.message;
        msg.hidden = false;
        fieldControl(name).setAttribute("aria-invalid", "true");
      } else {
        item.textContent = detail.message;
      }
      errorList.appendChild(item);
    });
    summaryBox.hidden = false;
    summaryBox.focus();
  }

  /* ---------- rendering ---------- */
  function renderOverview(plan) {
    document.getElementById("results-sub").textContent = plan.title;
    document.getElementById("summary").textContent = plan.insights.summary;
    const dl = document.getElementById("overview");
    clear(dl);
    const rows = [
      ["Event", plan.title, null, false],
      ["Date", dateFmt.format(parseDate(plan.event_date)) + ` (${plan.days_until} days to go)`, null, false],
      ["City", plan.city, null, false],
      ["Guests", String(plan.guest_count), null, false],
      ["Total budget", formatInr(plan.budget), plan.budget, true],
      ["Per guest", formatInr(plan.per_guest), plan.per_guest, true],
    ];
    rows.forEach(([term, text, number, hot]) => {
      const dd = el("dd", { text });
      if (number !== null) countUp(dd, number, formatInr);
      dl.appendChild(el("div", { class: hot ? "stat hot" : "stat" }, [el("dt", { text: term }), dd]));
    });
    document.getElementById("ai-note").textContent =
      plan.ai_source === "gemini"
        ? "\u2726 Ideas and extra checklist items were generated by Gemini."
        : "Showing built-in suggestions because the AI service is not available right now.";
  }

  function renderWarnings(plan) {
    const box = document.getElementById("warnings");
    clear(box);
    plan.warnings.forEach((w) => box.appendChild(el("p", { text: w })));
    box.hidden = plan.warnings.length === 0;
  }

  function renderBudget(plan) {
    const body = document.querySelector("#budget-table tbody");
    clear(body);
    const bars = [];
    plan.budget_lines.forEach((line) => {
      const fill = el("span");
      fill.dataset.percent = String(line.percent);
      bars.push(fill);
      const amount = el("td", { class: "num" });
      countUp(amount, line.amount, formatInr);
      body.appendChild(el("tr", { class: line.category === "Contingency" ? "alt" : "" }, [
        el("td", {}, [el("span", { text: line.category }), el("span", { class: "bar", "aria-hidden": "true" }, [fill])]),
        el("td", { class: "num", text: line.percent + "%" }),
        amount,
      ]));
    });
    const total = plan.budget_lines.reduce((sum, l) => sum + l.amount, 0);
    const totalCell = el("td", { class: "num" });
    countUp(totalCell, total, formatInr);
    body.appendChild(el("tr", {}, [el("th", { scope: "row", text: "Total" }), el("td", { class: "num", text: "100%" }), totalCell]));
    return bars;
  }

  function growBars(bars) {
    const apply = () => bars.forEach((bar) => { bar.style.width = bar.dataset.percent + "%"; });
    if (reduceMotion) apply();
    else requestAnimationFrame(() => requestAnimationFrame(apply));
  }

  function whenLabel(milestone) {
    if (milestone.days_from_today === 0) return "Today";
    return dateFmt.format(parseDate(milestone.due_date));
  }

  function renderTimeline(plan) {
    const list = document.getElementById("timeline");
    clear(list);
    plan.milestones.forEach((m) => {
      const isEventDay = m.category === "Event day";
      let badge = null;
      if (isEventDay) badge = "Big day";
      else if (m.category !== "After event" && m.days_from_today === 0) badge = "Due now";
      else if (m.category !== "After event" && m.days_from_today <= 7) badge = "This week";

      const what = el("span", {}, [el("span", { text: m.task }), el("span", { class: "meta", text: " (" + m.category + ")" })]);
      if (badge) what.appendChild(el("span", { class: "badge", text: badge }));
      const cls = isEventDay ? "event-day" : badge ? "soon" : "";
      list.appendChild(el("li", { class: cls }, [el("span", { class: "when", text: whenLabel(m) }), what]));
    });
  }

  function updateProgress() {
    const boxes = document.querySelectorAll("#vendors input[type=checkbox]");
    const done = Array.from(boxes).filter((b) => b.checked).length;
    const bar = document.getElementById("checklist-bar");
    bar.max = boxes.length || 1;
    bar.value = done;
    const pct = boxes.length ? Math.round((done / boxes.length) * 100) : 0;
    const prog = document.getElementById("checklist-progress");
    if (done === boxes.length && boxes.length > 0) {
      prog.textContent = `All ${boxes.length} vendor tasks completed! (100%) - You're celebration ready! 🎉`;
    } else {
      prog.textContent = `${done} of ${boxes.length} tasks completed (${pct}%)`;
    }
  }

  function checkbox(id, label) {
    const input = el("input", { type: "checkbox", id });
    input.addEventListener("change", updateProgress);
    return el("label", { class: "check", for: id }, [input, el("span", { text: label })]);
  }

  function renderVendors(plan) {
    const box = document.getElementById("vendors");
    clear(box);
    let counter = 0;
    plan.vendor_checklist.forEach((group) => {
      const set = el("fieldset", { class: "vendor" }, [el("legend", { text: group.vendor })]);
      group.items.forEach((item) => set.appendChild(checkbox("chk-" + counter++, item)));
      box.appendChild(set);
    });
    const extras = plan.insights.checklist_extras;
    if (extras.length) {
      const set = el("fieldset", { class: "vendor" }, [el("legend", { text: "Extra suggestions for your event" })]);
      extras.forEach((e) => set.appendChild(checkbox("chk-" + counter++, `${e.category}: ${e.item}`)));
      box.appendChild(set);
    }
    updateProgress();
  }

  function renderIdeas(plan) {
    const ideas = document.getElementById("ideas");
    clear(ideas);
    plan.insights.ideas.forEach((idea) => {
      ideas.appendChild(el("li", {}, [el("strong", { text: idea.title }), el("span", { text: idea.description })]));
    });
    const tips = document.getElementById("tips");
    clear(tips);
    plan.insights.saving_tips.forEach((tip) => tips.appendChild(el("li", { text: tip })));
  }

  function replayReveal() {
    results.querySelectorAll(".sec").forEach((section, index) => {
      section.classList.remove("reveal");
      void section.offsetWidth; // restart the CSS animation
      section.style.animationDelay = index * 70 + "ms";
      section.classList.add("reveal");
    });
  }

  function setupScrollSpy() {
    if (spy) spy.disconnect();
    if (!("IntersectionObserver" in window)) return;
    const links = new Map(
      Array.from(document.querySelectorAll(".jump a")).map((a) => [a.getAttribute("href").slice(1), a])
    );
    spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          links.forEach((link) => link.removeAttribute("aria-current"));
          const active = links.get(entry.target.id);
          if (active) active.setAttribute("aria-current", "true");
        });
      },
      { rootMargin: "-20% 0px -65% 0px" }
    );
    links.forEach((_, id) => {
      const section = document.getElementById(id);
      if (section) spy.observe(section);
    });
  }

  function render(plan) {
    currentPlan = plan;
    renderOverview(plan);
    renderWarnings(plan);
    const bars = renderBudget(plan);
    renderTimeline(plan);
    renderVendors(plan);
    renderIdeas(plan);
    layout.classList.add("has-results");
    results.hidden = false;
    replayReveal();
    growBars(bars);
    setupScrollSpy();
    results.focus({ preventScroll: true });
    results.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
  }

  /* ---------- calendar export ---------- */
  function icsEscape(text) {
    return text.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
  }

  function compact(iso) {
    return iso.replace(/-/g, "");
  }

  function nextDay(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(Date.UTC(y, m - 1, d + 1)).toISOString().slice(0, 10);
  }

  function buildIcs(plan) {
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+/, "");
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Celebration Event Planner//EN", "CALSCALE:GREGORIAN"];
    plan.milestones.forEach((m, index) => {
      lines.push(
        "BEGIN:VEVENT",
        `UID:${index}-${compact(m.due_date)}@celebration-planner`,
        `DTSTAMP:${stamp}`,
        `DTSTART;VALUE=DATE:${compact(m.due_date)}`,
        `DTEND;VALUE=DATE:${compact(nextDay(m.due_date))}`,
        `SUMMARY:${icsEscape(plan.title + ": " + m.task)}`,
        "END:VEVENT"
      );
    });
    lines.push("END:VCALENDAR");
    return lines.join("\r\n");
  }

  function downloadIcs() {
    if (!currentPlan) return;
    const blob = new Blob([buildIcs(currentPlan)], { type: "text/calendar" });
    const url = URL.createObjectURL(blob);
    const link = el("a", { href: url, download: "event-timeline.ics" });
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  /* ---------- submit ---------- */
  function readForm() {
    const type = form.querySelector("input[name=event_type]:checked");
    const value = (id) => document.getElementById(id).value;
    const number = (id) => (value(id) === "" ? null : Number(value(id)));
    return {
      event_type: type ? type.value : "",
      title: value("title"),
      guest_count: number("guest_count"),
      budget: number("budget"),
      event_date: value("event_date"),
      city: value("city"),
      preferences: value("preferences"),
    };
  }

  function setBusy(busy) {
    submitBtn.disabled = busy;
    submitBtn.classList.toggle("loading", busy);
    submitLabel.textContent = busy ? "Planning" : "Create my plan";
    if (busy) form.setAttribute("aria-busy", "true");
    else form.removeAttribute("aria-busy");
  }

  async function onSubmit(event) {
    event.preventDefault();
    clearErrors();
    setBusy(true);
    statusEl.textContent = "Creating your plan. This can take a few seconds.";
    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(readForm()),
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        statusEl.textContent = "Your plan is ready.";
        render(data);
      } else if (response.status === 422 && data.details) {
        statusEl.textContent = "";
        showErrors(data.details);
      } else {
        statusEl.textContent = data.message || "Something went wrong. Please try again.";
      }
    } catch (err) {
      statusEl.textContent = "Network problem. Please check your connection and try again.";
    } finally {
      setBusy(false);
    }
  }

  document.getElementById("event_date").min = todayIso();
  form.addEventListener("submit", onSubmit);
  document.getElementById("print-btn").addEventListener("click", () => window.print());
  document.getElementById("ics-btn").addEventListener("click", downloadIcs);
})();
