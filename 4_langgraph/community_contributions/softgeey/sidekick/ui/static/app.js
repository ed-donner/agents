/* SideKick — frontend chat logic */

// ── Lightweight markdown renderer ────────────────────────────────────
function renderMarkdown(text) {
  return text
    // code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
      `<pre><code class="lang-${lang}">${escapeHtml(code.trim())}</code></pre>`)
    // inline code
    .replace(/`([^`]+)`/g, (_, c) => `<code>${escapeHtml(c)}</code>`)
    // bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    // hr
    .replace(/^---+$/gm, '<hr>')
    // unordered lists (collect runs)
    .replace(/((?:^- .+\n?)+)/gm, block => {
      const items = block.trim().split('\n').map(l => `<li>${l.slice(2)}</li>`).join('');
      return `<ul>${items}</ul>`;
    })
    // ordered lists
    .replace(/((?:^\d+\. .+\n?)+)/gm, block => {
      const items = block.trim().split('\n').map(l => `<li>${l.replace(/^\d+\.\s/, '')}</li>`).join('');
      return `<ol>${items}</ol>`;
    })
    // links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // line breaks (paragraphs)
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, '<br>')
    // wrap in paragraph if not already block element
    .replace(/^(?!<[hupoa]|<pre|<hr)(.+)/gm, (match) => {
      if (match.startsWith('<')) return match;
      return match;
    });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ── State ────────────────────────────────────────────────────────────
let isLoading = false;
let currentIntent = 'general';

// ── DOM refs ─────────────────────────────────────────────────────────
const messagesEl  = document.getElementById('messages');
const inputEl     = document.getElementById('messageInput');
const sendBtn     = document.getElementById('sendBtn');
const intentBadge = document.getElementById('intentBadge');
const resetBtn    = document.getElementById('resetBtn');

// ── Send message ─────────────────────────────────────────────────────
async function sendMessage(text) {
  text = (text || inputEl.value).trim();
  if (!text || isLoading) return;

  appendMessage('user', text);
  inputEl.value = '';
  autoResize();
  hideWelcome();

  setLoading(true);
  const typingId = showTyping();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });

    removeTyping(typingId);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      appendMessage('agent', `⚠️ Error: ${err.detail || res.statusText}`);
      return;
    }

    const data = await res.json();
    appendMessage('agent', data.response);
    updateIntent(data.intent);

  } catch (err) {
    removeTyping(typingId);
    appendMessage('agent', `⚠️ Network error: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

// ── Append a chat bubble ──────────────────────────────────────────────
function appendMessage(role, text) {
  const div = document.createElement('div');
  div.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = `avatar ${role}-avatar`;
  avatar.textContent = role === 'user' ? 'YOU' : 'SK';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = role === 'agent'
    ? `<p>${renderMarkdown(text)}</p>`
    : escapeHtml(text).replace(/\n/g, '<br>');

  div.appendChild(avatar);
  div.appendChild(bubble);
  messagesEl.appendChild(div);
  scrollToBottom();
}

// ── Typing indicator ──────────────────────────────────────────────────
let typingCounter = 0;
function showTyping() {
  const id = `typing-${++typingCounter}`;
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.id = id;
  div.innerHTML = `
    <div class="avatar agent-avatar">SK</div>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  `;
  messagesEl.appendChild(div);
  scrollToBottom();
  return id;
}

function removeTyping(id) {
  document.getElementById(id)?.remove();
}

// ── Intent badge ──────────────────────────────────────────────────────
const intentLabels = {
  email:    '✉ Email',
  calendar: '📅 Calendar',
  tasks:    '✓ Tasks',
  research: '⌕ Research',
  general:  '· General',
};

function updateIntent(intent) {
  currentIntent = intent;
  intentBadge.textContent = intentLabels[intent] || intent;
  intentBadge.className = `intent-badge ${intent}`;
}

// ── Utilities ─────────────────────────────────────────────────────────
function setLoading(val) {
  isLoading = val;
  sendBtn.disabled = val;
  inputEl.disabled = val;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideWelcome() {
  document.getElementById('welcome')?.remove();
}

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
}

// ── Reset conversation ────────────────────────────────────────────────
async function resetConversation() {
  if (!confirm('Clear conversation history?')) return;
  await fetch('/reset', { method: 'POST' });
  messagesEl.innerHTML = '';
  updateIntent('general');
  renderWelcome();
}

function renderWelcome() {
  const div = document.createElement('div');
  div.id = 'welcome';
  div.className = 'welcome';
  div.innerHTML = `
    <div class="welcome-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
      </svg>
    </div>
    <h2>Good to have you back.</h2>
    <p>Ask me to draft an email, prep for a meeting, track project tasks, or research anything.</p>
  `;
  messagesEl.appendChild(div);
}

// ── Quick prompts ─────────────────────────────────────────────────────
function useQuickPrompt(text) {
  inputEl.value = text;
  autoResize();
  inputEl.focus();
}

// ── Event listeners ───────────────────────────────────────────────────
inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

inputEl.addEventListener('input', autoResize);
sendBtn.addEventListener('click', () => sendMessage());
resetBtn.addEventListener('click', resetConversation);

// ── Init ──────────────────────────────────────────────────────────────
renderWelcome();
inputEl.focus();
