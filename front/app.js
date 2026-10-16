const messages = [];
const list = document.querySelector('#messages');
const form = document.querySelector('#composer');
const input = document.querySelector('#message-input');
const send = document.querySelector('#send-button');
const API_URL = window.MYSIMPLEAGENT_API_URL || 'http://localhost:8000';
let sessionId = crypto.randomUUID();

function addMessage(role, content) {
  document.querySelector('.welcome')?.remove();
  const item = document.createElement('div');
  item.className = `message ${role}`;
  item.innerHTML = `<div class="avatar">${role === 'user' ? '你' : '✦'}</div><div class="message-body"></div>`;
  item.querySelector('.message-body').textContent = content;
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;
}

async function sendMessage(content) {
  messages.push({ role: 'user', content });
  addMessage('user', content);
  send.disabled = true;
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: content, messages, session_id: sessionId }),
    });
    if (!response.ok) throw new Error(`请求失败（${response.status}）`);
    const data = await response.json();
    const answer = data.content ?? data.message ?? data.response ?? data.choices?.[0]?.message?.content;
    if (!answer) throw new Error('后端响应中没有内容');
    messages.push({ role: 'assistant', content: answer });
    addMessage('assistant', answer);
  } catch (error) {
    addMessage('assistant', `连接后端失败：${error.message}`);
  } finally { send.disabled = false; input.focus(); }
}

form.addEventListener('submit', (event) => { event.preventDefault(); const content = input.value.trim(); if (!content || send.disabled) return; input.value = ''; sendMessage(content); });
input.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
document.querySelector('#new-chat').addEventListener('click', () => { messages.length = 0; sessionId = crypto.randomUUID(); list.innerHTML = '<div class="welcome"><div class="welcome-icon">✦</div><h2>有什么可以帮你？</h2><p>发送消息开始一次新的会话。</p></div>'; input.focus(); });
