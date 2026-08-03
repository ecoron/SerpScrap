const notice = document.getElementById('notice');
export function notify(message, type = 'info') { notice.textContent = message; notice.className = `notice${type === 'error' ? ' error' : ''}`; notice.hidden = false; }
export function clearNotice() { notice.hidden = true; notice.textContent = ''; }
