/* ProfitLens chat widget (Phase 4). One self contained file, served by the chat service at /widget.js.
   Framer embed: <script src="https://<service address>/widget.js" defer></script>
   No cookies, no third party scripts. The conversation is kept in sessionStorage for the visit only. */
(function () {
  if (window.__profitlensChat) return;
  window.__profitlensChat = true;

  var script = document.currentScript;
  var API = script ? new URL(script.src).origin : "";
  var KEY = "profitlens_chat_v1";
  var AVATAR = API + "/avatar";

  function load() {
    try { return JSON.parse(sessionStorage.getItem(KEY)) || null; } catch (e) { return null; }
  }
  function save() {
    try { sessionStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode: works without memory */ }
  }
  function newId() {
    var a = new Uint8Array(12);
    (window.crypto || window.msCrypto).getRandomValues(a);
    return "w" + Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }

  var state = load() || { id: newId(), log: [], open: false, started: false, mode: "chat" };

  var css = [
    ":host { all: initial; }",
    "* { box-sizing: border-box; }",
    ".wrap { font-family: Geist, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #666666; font-size: 15px; line-height: 1.45; }",
    ".launcher { position: fixed; right: 20px; bottom: 20px; width: 56px; height: 56px; border-radius: 50%; border: 0; background: #111111; color: #fff; cursor: pointer; box-shadow: 0 6px 20px rgba(0,0,0,.18); display: flex; align-items: center; justify-content: center; z-index: 2147483000; }",
    ".launcher:focus-visible, button:focus-visible, input:focus-visible { outline: 2px solid #111111; outline-offset: 2px; }",
    ".launcher svg { width: 26px; height: 26px; }",
    ".launcher img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; display: block; border: 2px solid #111111; }",
    ".launcher.pic { background: #fff; padding: 0; }",
    ".who { display: flex; align-items: center; gap: 10px; min-width: 0; }",
    ".av { border-radius: 50%; object-fit: cover; flex: none; background: #efe9df; }",
    ".av-lg { width: 38px; height: 38px; }",
    ".row { display: flex; align-items: flex-end; gap: 8px; margin: 6px 0; }",
    ".row .msg { margin: 0; }",
    ".av-sm { width: 26px; height: 26px; }",
    ".panel { position: fixed; right: 20px; bottom: 88px; width: 370px; height: 560px; max-height: calc(100vh - 110px); background: #fff; border: 1px solid #e5e5e5; border-radius: 16px; box-shadow: 0 12px 40px rgba(0,0,0,.16); display: none; flex-direction: column; overflow: hidden; z-index: 2147483000; }",
    ".panel.open { display: flex; }",
    "header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid #e5e5e5; }",
    "header b { display: block; color: #111111; font-weight: 600; }",
    "header span { font-size: 12px; }",
    ".close { background: none; border: 0; color: #666666; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; font-size: 20px; line-height: 1; }",
    ".log { flex: 1; overflow-y: auto; padding: 14px; }",
    ".msg { max-width: 85%; padding: 9px 12px; border-radius: 12px; margin: 6px 0; white-space: pre-wrap; word-wrap: break-word; }",
    ".bot { background: #f4f4f4; color: #111111; }",
    ".me { background: #111111; color: #fff; margin-left: auto; }",
    ".typing { color: #999; font-size: 13px; margin: 4px 2px; }",
    "form { display: flex; gap: 8px; padding: 10px; border-top: 1px solid #e5e5e5; }",
    "input { flex: 1; min-width: 0; padding: 10px 12px; font: inherit; color: #111111; border: 1px solid #e5e5e5; border-radius: 10px; }",
    "form button { padding: 0 14px; font: inherit; font-weight: 600; color: #fff; background: #111111; border: 0; border-radius: 10px; cursor: pointer; }",
    "form button:disabled { opacity: .5; }",
    "@media (max-width: 480px) { .panel { right: 0; bottom: 0; width: 100vw; height: 100%; max-height: none; border-radius: 0; border: 0; } .panel.open ~ .launcher { display: none; } }"
  ].join("\n");

  var host = document.createElement("div");
  host.id = "profitlens-chat";
  var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;
  var style = document.createElement("style");
  style.textContent = css;
  root.appendChild(style);

  var wrap = el("div", "wrap");
  var panel = el("div", "panel");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "Chat with Jelena, the ProfitLens AI assistant");
  var header = el("header");
  var title = el("div");
  var b = el("b"); b.textContent = "Jelena";
  var sub = el("span"); sub.textContent = "AI assistant. A founder takes the call.";
  title.appendChild(b); title.appendChild(sub);
  var who = el("div", "who");
  var headAv = avatarImg("av av-lg", "Jelena");
  if (headAv) who.appendChild(headAv);
  who.appendChild(title);
  var close = el("button", "close"); close.type = "button"; close.setAttribute("aria-label", "Close chat"); close.textContent = "×";
  header.appendChild(who); header.appendChild(close);
  var log = el("div", "log"); log.setAttribute("aria-live", "polite");
  var form = el("form");
  var input = el("input"); input.type = "text"; input.placeholder = "Type your question"; input.setAttribute("aria-label", "Your message"); input.maxLength = 1000;
  var send = el("button"); send.type = "submit"; send.textContent = "Send";
  form.appendChild(input); form.appendChild(send);
  panel.appendChild(header); panel.appendChild(log); panel.appendChild(form);

  var launcher = el("button", "launcher");
  launcher.type = "button";
  launcher.setAttribute("aria-label", "Chat with Jelena, the ProfitLens AI assistant");
  var bubbleIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg>';
  var launchAv = avatarImg("", "");
  if (launchAv) {
    launcher.classList.add("pic");
    launcher.appendChild(launchAv);
    launchAv.onerror = function () { launcher.classList.remove("pic"); launcher.innerHTML = bubbleIcon; };
  } else {
    launcher.innerHTML = bubbleIcon;
  }

  wrap.appendChild(panel); wrap.appendChild(launcher);
  root.appendChild(wrap);

  function el(tag, cls) { var e = document.createElement(tag); if (cls) e.className = cls; return e; }

  function avatarImg(cls, alt) {
    if (!API) return null;
    var i = el("img", cls); i.src = AVATAR; i.alt = alt;
    i.onerror = function () { i.style.display = "none"; };
    return i;
  }

  function bubble(text, who) {
    var d = el("div", "msg " + (who === "me" ? "me" : "bot"));
    d.textContent = text;
    if (who === "me") {
      log.appendChild(d);
    } else {
      var row = el("div", "row");
      var av = avatarImg("av av-sm", "");
      if (av) row.appendChild(av);
      row.appendChild(d);
      log.appendChild(row);
    }
    log.scrollTop = log.scrollHeight;
  }
  function add(text, who) { state.log.push({ who: who, text: text }); save(); bubble(text, who); }

  var typing = null;
  function busy(on) {
    send.disabled = on; input.disabled = on;
    if (on && !typing) { typing = el("div", "typing"); typing.textContent = "Typing..."; log.appendChild(typing); log.scrollTop = log.scrollHeight; }
    if (!on && typing) { typing.remove(); typing = null; }
  }

  // Every request carries the sealed copy of the conversation from the last reply, so the
  // conversation continues even if the server restarted in between (ADR 0018).
  function post(path, body) {
    body.state = state.token || "";
    return fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (data) {
        if (!r.ok) throw data;
        if (data.state) { state.token = data.state; save(); }
        return data;
      }); });
  }

  function emailMode(done) {
    input.value = "";
    input.type = "email";
    input.placeholder = done ? "Thank you" : "Your email";
    input.setAttribute("aria-label", "Your email");
    send.textContent = "Send";
    input.disabled = send.disabled = !!done;
  }

  function handle(data) {
    if (data.reply) add(data.reply, "bot");
    state.mode = data.mode || "chat"; save();
    if (state.mode === "email_form") emailMode(false);
    if (state.mode === "done") emailMode(true);
    if (state.mode === "chat" && !input.disabled) input.focus();
  }

  function openPanel() {
    state.open = true; save();
    panel.classList.add("open");
    launcher.setAttribute("aria-label", "Close chat");
    if (!state.started) {
      state.started = true; save();
      busy(true);
      post("/start", { session_id: state.id }).then(function (data) { busy(false); handle(data); })
        .catch(function () { busy(false); state.started = false; save(); add("Sorry, the chat is not available right now. Please try again later.", "bot"); });
    } else {
      input.focus();
    }
  }
  function closePanel() {
    state.open = false; save();
    panel.classList.remove("open");
    launcher.setAttribute("aria-label", "Chat with Jelena, the ProfitLens AI assistant");
    launcher.focus();
  }

  launcher.onclick = function () { panel.classList.contains("open") ? closePanel() : openPanel(); };
  close.onclick = closePanel;
  panel.addEventListener("keydown", function (e) { if (e.key === "Escape") closePanel(); });

  form.onsubmit = function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    add(text, "me");
    input.value = "";
    busy(true);
    var req = state.mode === "email_form"
      ? post("/leave-email", { session_id: state.id, email: text })
      : post("/chat", { session_id: state.id, message: text });
    req.then(function (data) { busy(false); handle(data); })
      .catch(function (err) {
        busy(false);
        add(err && err.detail && typeof err.detail === "string" ? err.detail : "Sorry, please try again.", "bot");
      });
  };

  // Restore the conversation after moving to another page of the site.
  state.log.forEach(function (m) { bubble(m.text, m.who); });
  if (state.mode === "email_form") emailMode(false);
  if (state.mode === "done") emailMode(true);
  if (state.open) panel.classList.add("open");

  function mount() { document.body.appendChild(host); }
  if (document.body) mount(); else document.addEventListener("DOMContentLoaded", mount);
})();
