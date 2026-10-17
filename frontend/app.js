const messages = [];
const list = document.querySelector('#messages');
const form = document.querySelector('#composer');
const input = document.querySelector('#message-input');
const send = document.querySelector('#send-button');
const API_URL = window.MYSIMPLEAGENT_API_URL || 'http://localhost:8000';
let sessionId = crypto.randomUUID();
const conversationList = document.querySelector('#conversation-list');
const modelSelect = document.querySelector('#model-select');
const maxContextInput = document.querySelector('#max-context');
const modelContextLimitLabel = document.querySelector('#model-context-limit');
let modelContextLimit = null;

function formatTokenLimit(value) {
  if (!value) return '';
  if (value >= 1000000) return `${(value / 1000000).toFixed(1).replace(/\.0$/, '')}M tokens`;
  if (value >= 1000) return `${Math.round(value / 1000)}K tokens`;
  return `${value} tokens`;
}

function updateContextLimit(model) {
  const option = [...modelSelect.options].find((item) => item.value === model);
  modelContextLimit = option?.dataset.maxContext ? Number(option.dataset.maxContext) : null;
  if (modelContextLimit) {
    maxContextInput.max = modelContextLimit;
    maxContextInput.placeholder = `最多 ${formatTokenLimit(modelContextLimit)}`;
    if (Number(maxContextInput.value) > modelContextLimit) maxContextInput.value = modelContextLimit;
    modelContextLimitLabel.textContent = `模型上限：${formatTokenLimit(modelContextLimit)}`;
  } else {
    maxContextInput.removeAttribute('max');
    maxContextInput.placeholder = '模型默认';
    modelContextLimitLabel.textContent = '模型上限未知';
  }
}

async function loadModels() {
  try {
    const response = await fetch(`${API_URL}/api/models`);
    if (!response.ok) return;
    const data = await response.json();
    modelSelect.innerHTML = '';
    data.models.forEach((model) => {
      const option = document.createElement('option');
      option.value = model.name;
      option.textContent = model.display_name || model.name;
      if (model.max_context) option.dataset.maxContext = model.max_context;
      modelSelect.appendChild(option);
    });
    if (modelSelect.options.length) updateContextLimit(modelSelect.value);
  } catch (_) { /* 后端未启动时保留空模型选择 */ }
}

function addMessage(role, content, messageId = null) {
  document.querySelector('.welcome')?.remove();
  const item = document.createElement('div');
  item.className = `message ${role}`;
  item.innerHTML = `<div class="avatar">${role === 'user' ? '你' : '✦'}</div><div class="message-body"></div>`;
  item.querySelector('.message-body').textContent = content;
  if (role === 'user' && messageId !== undefined && messageId !== null) {
    const edit = document.createElement('button');
    edit.className = 'edit-message';
    edit.textContent = '编辑';
    edit.onclick = () => startEditing(item, content, messageId);
    item.appendChild(edit);
  }
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;
}

function startEditing(item, content, messageId) {
  const body = item.querySelector('.message-body');
  const edit = item.querySelector('.edit-message');
  body.innerHTML = '';
  const textarea = document.createElement('textarea');
  textarea.className = 'edit-input';
  textarea.value = content;
  const actions = document.createElement('span');
  actions.className = 'edit-actions';
  actions.innerHTML = '<button class="edit-save">保存</button><button class="edit-cancel">取消</button>';
  body.append(textarea, actions);
  edit.remove();
  textarea.focus();
  actions.querySelector('.edit-cancel').onclick = () => renderMessages(messages);
  actions.querySelector('.edit-save').onclick = () => {
    const next = textarea.value.trim();
    if (next && next !== content) sendMessage(next, messageId);
    else renderMessages(messages);
  };
}

function addToolEvent(label, content) {
  document.querySelector('.welcome')?.remove();
  const item = document.createElement('div');
  item.className = 'tool-event';
  item.innerHTML = `<span class="tool-icon">⚙</span><span class="tool-label"></span><span class="tool-content"></span>`;
  item.querySelector('.tool-label').textContent = label;
  item.querySelector('.tool-content').textContent = content || '';
  list.appendChild(item);
  list.scrollTop = list.scrollHeight;
}

function renderMessages(items) {
  list.innerHTML = '';
  if (!items.length) {
    list.innerHTML = '<div class="welcome"><div class="welcome-icon">✦</div><h2>有什么可以帮你？</h2><p>发送消息开始一次新的会话。</p></div>';
    return;
  }
  items.forEach((item) => {
    if (item.role === 'user') {
      addMessage('user', item.content || '', item.id);
    } else if (item.role === 'assistant' && item.tool_calls?.length) {
      item.tool_calls.forEach((call) => addToolEvent(
        `调用工具：${call.function?.name || '未知工具'}`,
        call.function?.arguments || '',
      ));
    } else if (item.role === 'tool') {
      addToolEvent('工具结果', item.content || '');
    } else if (item.role === 'assistant' && item.content) {
      addMessage('assistant', item.content);
    }
  });
}

async function loadSessions() {
  try {
    const response = await fetch(`${API_URL}/api/sessions`);
    if (!response.ok) return;
    const data = await response.json();
    conversationList.innerHTML = '';
    data.sessions.forEach((session) => {
      const button = document.createElement('button');
      button.className = 'conversation-item';
      button.textContent = session.session_id;
      button.onclick = () => loadSession(session.session_id);
      conversationList.appendChild(button);
    });
  } catch (_) { /* 后端未启动时保留空列表 */ }
}

async function loadSession(id) {
  const response = await fetch(`${API_URL}/api/sessions/${encodeURIComponent(id)}`);
  if (!response.ok) return;
  const data = await response.json();
  sessionId = data.session_id;
  messages.splice(0, messages.length, ...data.messages);
  renderMessages(data.messages);
}

async function sendMessage(content, editMessageId = null) {
  if (editMessageId === null) {
    messages.push({ role: 'user', content });
    addMessage('user', content);
  } else {
    const messageIndex = messages.findIndex((item) => item.id === editMessageId);
    if (messageIndex >= 0) {
      messages.splice(messageIndex, messages.length - messageIndex, {
        id: editMessageId,
        role: 'user',
        content,
      });
      renderMessages(messages);
    }
  }
  send.disabled = true;
  try {
    const maxContext = maxContextInput.value ? Number(maxContextInput.value) : null;
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: content,
        messages,
        session_id: sessionId,
        edit_message_id: editMessageId,
        model: modelSelect.value,
        max_context: maxContext,
      }),
    });
    if (!response.ok) throw new Error(`请求失败（${response.status}）`);
    const data = await response.json();
    const answer = data.content ?? data.message ?? data.response ?? data.choices?.[0]?.message?.content;
    if (!answer) throw new Error('后端响应中没有内容');
    if (Array.isArray(data.messages)) {
      messages.splice(0, messages.length, ...data.messages);
      renderMessages(data.messages);
    } else {
      messages.push({ role: 'assistant', content: answer });
      addMessage('assistant', answer);
    }
    await loadSessions();
  } catch (error) {
    addMessage('assistant', `连接后端失败：${error.message}`);
  } finally { send.disabled = false; input.focus(); }
}

form.addEventListener('submit', (event) => { event.preventDefault(); const content = input.value.trim(); if (!content || send.disabled) return; input.value = ''; sendMessage(content); });
input.addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
document.querySelector('#new-chat').addEventListener('click', () => { messages.length = 0; sessionId = crypto.randomUUID(); renderMessages([]); input.focus(); });
modelSelect.addEventListener('change', () => updateContextLimit(modelSelect.value));
maxContextInput.addEventListener('input', () => {
  if (modelContextLimit && Number(maxContextInput.value) > modelContextLimit) {
    maxContextInput.value = modelContextLimit;
  }
});
loadModels();
loadSessions();
