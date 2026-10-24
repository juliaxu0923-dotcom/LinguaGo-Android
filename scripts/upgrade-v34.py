#!/usr/bin/env python3
"""Apply the shared V3.4 UI update to the existing V3.3 source at build time."""
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'LinguaGo-Mobile-V2')
www = root / 'www'
html_path = www / 'index.html'
cloud_path = www / 'cloud-sync.js'
html = html_path.read_text(encoding='utf-8')
cloud = cloud_path.read_text(encoding='utf-8')

helpers = r'''
  // V3.4: render the same account state in the dialog and on the Me page.
  function escapeAccountText(value) {
    return String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function accountCard() {
    if (!session || !session.user) {
      return '<div class="account-entry-card" data-account-state="signed-out"><strong>☁️ 登录账号 · 自动同步学习记录</strong><p>换版本、换手机也可以恢复已掌握单词、听力和口语进度；原有学习数据不会因打开登录窗口被清空。</p><button type="button" data-open-linguago-account>登录 / 注册 / 立即同步 →</button><p class="muted">LinguaGo V3.4</p></div>';
    }
    const email = escapeAccountText(session.user.email || '已登录账号');
    const status = escapeAccountText(lastSync ? '最近同步：' + lastSync : '学习记录保存在本机，等待云端同步');
    return '<div class="account-entry-card" data-account-state="signed-in"><strong>☁️ 已登录</strong><p style="font-weight:700;overflow-wrap:anywhere" data-linguago-current-email>' + email + '</p><p aria-live="polite">' + status + '</p><button type="button" data-open-linguago-account>立即同步 / 账号设置 →</button> <button type="button" data-linguago-logout>退出登录</button><p class="muted">LinguaGo V3.4 · 学习记录自动同步</p></div>';
  }
  function refreshAccountCards() {
    document.querySelectorAll('.account-entry-card').forEach(card => { card.outerHTML = accountCard(); });
  }
'''

if '// V3.4: render the same account state' not in cloud:
    marker = '  function draw() {'
    assert cloud.count(marker) == 1, 'Cannot locate account renderer'
    cloud = cloud.replace(marker, helpers + '\n' + marker, 1)
    marker = "    $('msg').textContent = message;\n  }"
    assert cloud.count(marker) == 1, 'Cannot locate dialog render completion'
    cloud = cloud.replace(marker, "    $('msg').textContent = message;\n    refreshAccountCards();\n  }", 1)
    marker = 'window.LinguaGoCloud = { scheduleSave()'
    assert cloud.count(marker) == 1, 'Cannot locate cloud bridge'
    cloud = cloud.replace(marker, 'window.LinguaGoCloud = { accountCard, scheduleSave()', 1)
    marker = "  $('close').onclick = closeAccount;"
    assert cloud.count(marker) == 1
    cloud = cloud.replace(marker, "  document.addEventListener('click', e => {\n    if (e.target.closest('[data-linguago-logout]')) { e.preventDefault(); $('logout').click(); }\n  });\n" + marker, 1)

if 'window.LinguaGoCloud?.accountCard?.()' not in html:
    pattern = r'(<div class="account-entry-card">.*?</div>)(?=<div class="stat-grid">)'
    assert len(re.findall(pattern, html, re.S)) == 1, 'Cannot locate Me account card'
    html = re.sub(pattern, lambda m: '${window.LinguaGoCloud?.accountCard?.() || `' + m.group(1) + '`}', html, count=1, flags=re.S)
html = html.replace('V3.3', 'V3.4').replace('v3.3', 'v3.4')
html_path.write_text(html, encoding='utf-8')
cloud_path.write_text(cloud, encoding='utf-8')

sw_path = www / 'sw.js'
sw = sw_path.read_text(encoding='utf-8')
sw, count = re.subn(r"const CACHE\s*=\s*['\"][^'\"]+['\"]", "const CACHE='linguago-mobile-v3.4-account-state'", sw, count=1)
assert count == 1, 'Cannot locate Service Worker cache version'
sw_path.write_text(sw, encoding='utf-8')
for filename in ('package.json', 'package-lock.json'):
    path = root / filename
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        data['version'] = '3.4.0'
        if '' in data.get('packages', {}):
            data['packages']['']['version'] = '3.4.0'
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(www / 'build-info.json').write_text(json.dumps({'version':'3.4.0','accountUi':'session-aware','cache':'linguago-mobile-v3.4-account-state'}) + '\n', encoding='utf-8')
assert '/auth/v1/token?grant_type=password' in cloud
assert '/rest/v1/learning_progress' in cloud
assert "storeSession(null)" in cloud
assert "localStorage.clear" not in cloud
print('V3.4 ready: account email, logout entry, password auth, cloud sync, new SW cache')
