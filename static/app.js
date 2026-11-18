const eligibilityForm = document.querySelector("#eligibility-form");
const results = document.querySelector("#results");
const chatForm = document.querySelector("#chat-form");
const chatInput = document.querySelector("#chat-message");
const messages = document.querySelector("#messages");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function statusClass(status) {
  return status === "Potential match" ? "" : "unknown";
}
eligibilityForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(eligibilityForm).entries());
  results.innerHTML = '<div class="empty-state"><p>Checking the available scheme records…</p></div>';
  try {
    const response = await fetch("/api/recommend", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Could not check the profile.");
    if (!payload.results.length) {
      results.innerHTML = '<div class="empty-state"><h3>No potential matches in this demo dataset</h3><p>Try leaving optional fields blank or explore official portals for a wider set of schemes.</p></div>';
      return;
    }
    results.innerHTML = `<h3 style="font:700 15px Manrope;color:#122b3b;margin:0 0 14px">Your scheme matches <span style="color:#819095;font:400 10px 'DM Sans'">(${payload.results.length})</span></h3>` +
      payload.results.map(({scheme,eligibility}) => `
      <article class="scheme-result">
        <span class="status ${statusClass(eligibility.status)}">${escapeHtml(eligibility.status)}</span>
        <h4 style="margin-top:10px">${escapeHtml(scheme.name)}</h4>
        <p>${escapeHtml(scheme.summary)}</p>
        <div class="check-list">${eligibility.checks.map(c=>`<div class="check-item ${c.result}">${c.result==="pass"?"✓":c.result==="fail"?"✕":"•"} <b>${escapeHtml(c.condition)}:</b> ${escapeHtml(c.explanation)}</div>`).join("") || '<div class="check-item">No specific rule was evaluated in this demo record. Review official conditions.</div>'}</div>
        <a href="${escapeHtml(scheme.url)}" target="_blank" rel="noopener">Visit official source ↗</a>
      </article>`).join("") + `<p class="disclaimer">${escapeHtml(payload.note)}</p>`;
  } catch (err) {
    results.innerHTML = `<div class="empty-state"><h3>Something went wrong</h3><p>${escapeHtml(err.message)}</p></div>`;
  }
});
function addMessage(text, type) {
  const el = document.createElement("div");
  el.className = type === "user" ? "user-message" : "bot-message";
  el.textContent = text;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}
async function askAssistant(question) {
  if (!question.trim()) return;
  document.querySelectorAll(".suggestions").forEach(x=>x.remove());
  addMessage(question, "user");
  const pending = addMessage("Looking through the available scheme information…", "bot");
  try {
    const response = await fetch("/api/chat", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:question,language:document.querySelector("#language").value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Assistant is unavailable.");
    pending.textContent = data.answer;
    if (data.sources?.length) {
      const sourceLine = document.createElement("small");
      sourceLine.style.cssText = "display:block;color:#71878a;font-size:9px;margin-top:10px";
      sourceLine.textContent = "Sources: " + data.sources.map(s=>s.name + " (" + s.verified + ")").join(" · ");
      pending.appendChild(sourceLine);
    }
  } catch (err) { pending.textContent = err.message; }
  messages.scrollTop = messages.scrollHeight;
}
chatForm.addEventListener("submit", e=>{e.preventDefault();const q=chatInput.value;chatInput.value="";askAssistant(q);});
document.querySelectorAll(".suggestions button").forEach(b=>b.addEventListener("click",()=>askAssistant(b.textContent)));
document.querySelectorAll(".category-card").forEach(b=>b.addEventListener("click",()=>{document.querySelector("#assistant").scrollIntoView({behavior:"smooth"});askAssistant(b.dataset.question);}));
