(function () {
  const cfg = window.EDUOGE;
  if (!cfg) return;

  const taskText = document.getElementById("taskText");
  const seedBadge = document.getElementById("seedBadge");
  const resultBox = document.getElementById("resultBox");
  const nextBtn = document.getElementById("nextBtn");
  const checkBtn = document.getElementById("checkBtn");
  const solutionBtn = document.getElementById("solution");

  const codeInput = document.getElementById("codeInput");
  const langSelect = document.getElementById("langSelect");

  let editor = null;
  let currentTask = null;
  let solutionShown = false;

  function errorKindToRu(kind) {
    if (kind === "syntax") return "Синтаксическая ошибка";
    if (kind === "timeout") return "Превышено время";
    return "Ошибка выполнения";
  }

  function langToMode(lang) {
    return (lang === "js") ? "javascript" : "python";
  }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const c of cookies) {
      const cookie = c.trim();
      if (cookie.startsWith(name + "=")) {
        return decodeURIComponent(cookie.substring(name.length + 1));
      }
    }
    return null;
  }

  function getParam(name) {
    return new URLSearchParams(window.location.search).get(name);
  }

  function setParam(name, value) {
    const url = new URL(window.location.href);
    url.searchParams.set(name, value);
    history.replaceState({}, "", url.toString());
  }

  function ensureSeedInUrl() {
    let seed = getParam("seed");
    if (!seed) {
      seed = String(Date.now());
      setParam("seed", seed);
    }
    return seed;
  }

  function resetUI() {
    if (!resultBox) return;
    resultBox.hidden = true;
    resultBox.textContent = "";
    resultBox.classList.remove("result--ok", "result--bad");
  }

  function showResultHtml(ok, html) {
    if (!resultBox) return;
    resultBox.hidden = false;
    resultBox.classList.remove("result--ok", "result--bad");
    resultBox.classList.add(ok ? "result--ok" : "result--bad");
    resultBox.innerHTML = html;
  }

  function showResult(ok, text) {
    if (!resultBox) return;
    resultBox.hidden = false;
    resultBox.classList.remove("result--ok", "result--bad");
    resultBox.classList.add(ok ? "result--ok" : "result--bad");
    resultBox.textContent = text;
  }

  function initEditor() {
    if (!codeInput) return;

    if (!window.CodeMirror) {
      console.warn("CodeMirror not loaded, using textarea");
      return;
    }

    editor = window.CodeMirror.fromTextArea(codeInput, {
      mode: langToMode(langSelect?.value || "python"),
      theme: "eclipse",
      lineNumbers: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      lineWrapping: true,
      placeholder: "# Напиши решение тут",
    });

    editor.setSize("100%", "100%");
  }

  function getEditorValue() {
    return editor ? editor.getValue() : String(codeInput?.value || "");
  }

  function clearEditor() {
    if (editor) editor.setValue("");
    else if (codeInput) codeInput.value = "";
  }

  function esc(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function nl2br(s) {
    return esc(s).replaceAll("\n", "<br>");
  }

  function renderTask(data) {
    const statement = data.statement ?? data.text ?? "";
    const exIn = data.example_inp ?? "";
    const exOut = data.example_out ?? "";

    const hasExample = exIn && exOut;

    taskText.innerHTML = `
      <div class="task__title">Задание:</div>
      <div class="task__statement">${nl2br(statement)}</div>
      ${hasExample ? `
        <div class="task__example-title">Пример работы программы</div>
        <table class="io-table">
          <thead>
            <tr>
              <th>Входные данные</th>
              <th>Выходные данные</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><pre>${esc(exIn)}</pre></td>
              <td><pre>${esc(exOut)}</pre></td>
            </tr>
          </tbody>
        </table>
      ` : ``}
    `;
  }

  async function loadTask(forceSeed = null) {
    resetUI();
    solutionShown = false;

    const type = String(getParam("type") || cfg.type || 16);
    const seed = forceSeed ? String(forceSeed) : ensureSeedInUrl();

    setParam("type", type);
    setParam("seed", seed);
    if (seedBadge) seedBadge.textContent = `seed: ${seed}`;

    const url = new URL(cfg.apiExercise, window.location.origin);
    url.searchParams.set("type", type);
    url.searchParams.set("seed", seed);

    const res = await fetch(url.toString(), { method: "GET", credentials: "same-origin" });
    const ct = (res.headers.get("content-type") || "").toLowerCase();

    if (!ct.includes("application/json")) {
      const text = await res.text();
      throw new Error(`API /api/exercise вернул не JSON (status=${res.status}).\n${text.slice(0, 200)}`);
    }

    const data = await res.json();
    if (!res.ok || data.ok === false) {
      const msg = data.error || `Ошибка генерации (status=${res.status})`;
      if (taskText) taskText.textContent = msg;
      throw new Error(msg);
    }

    currentTask = data;
    renderTask(data);
    clearEditor();
  }

  async function checkCode() {
    resetUI();

    const type = String(getParam("type") || cfg.type || 16);
    const seed = String(getParam("seed") || ensureSeedInUrl());
    const language = String(langSelect?.value || "python");
    const code = getEditorValue();
    const csrf = getCookie("csrftoken");

    const res = await fetch(cfg.apiCheck, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(csrf ? { "X-CSRFToken": csrf } : {}),
      },
      body: JSON.stringify({ type, seed, language, code }),
    });

    const ct = (res.headers.get("content-type") || "").toLowerCase();
    if (!ct.includes("application/json")) {
      const text = await res.text();
      showResult(false, `Ошибка: сервер вернул не JSON (status=${res.status})`);
      throw new Error(text.slice(0, 500));
    }

    const data = await res.json();

    if (!res.ok || data.ok === false) {
      const msg = data.error || `Ошибка проверки (status=${res.status})`;
      showResult(false, msg);
      return;
    }

    const isCorrect = !!data.is_correct;
    const stdoutRaw = String(data.stdout ?? "");
    const stdoutTrim = stdoutRaw.trim();

    let header = isCorrect ? "Верно." : "Неверно.";
    if (data.error_kind) header = `Ошибка: ${errorKindToRu(String(data.error_kind))}`;

    let html = `<div>${esc(header)}</div>`;
    if (stdoutTrim) {
      html += `
        <div style="margin-top:10px;">Программа вернула:</div>
        <pre style="margin:8px 0 0; white-space:pre-wrap;">${esc(stdoutRaw)}</pre>
      `;
    }

    const okStyle = isCorrect && !data.error_kind;
    showResultHtml(okStyle, html);
  }

  function toggleSolution() {
    resetUI();

    if (!currentTask) {
      showResult(false, "Решение недоступно: задача не загружена.");
      return;
    }

    const lang = String(langSelect?.value || "python");
    const sol = (lang === "js")
      ? String(currentTask.solution_js || "")
      : String(currentTask.solution_py || "");

    if (!sol.trim()) {
      showResult(false, "Решение не пришло с сервера. Значит бэк его не отдаёт.");
      return;
    }

    solutionShown = !solutionShown;

    if (!solutionShown) {
      resetUI();
      return;
    }

    showResultHtml(true, `
      <div><b>Решение (${esc(lang)}):</b></div>
      <pre style="margin:8px 0 0; white-space:pre-wrap;">${esc(sol)}</pre>
    `);
  }

  // handlers
  if (checkBtn) checkBtn.addEventListener("click", () => checkCode().catch(console.error));
  if (nextBtn) nextBtn.addEventListener("click", () => loadTask(String(Date.now())).catch(console.error));
  if (solutionBtn) solutionBtn.addEventListener("click", toggleSolution);

  if (langSelect) {
    langSelect.addEventListener("change", () => {
      if (editor) editor.setOption("mode", langToMode(langSelect.value));
      // если решение показано и язык сменился, обновим вывод решения
      if (solutionShown) toggleSolution(), toggleSolution();
    });
  }

  initEditor();
  loadTask(null).catch((err) => {
    console.error(err);
    if (taskText) taskText.textContent = "Не удалось загрузить задачу. См. консоль.";
  });
})();
