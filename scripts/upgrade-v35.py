#!/usr/bin/env python3
"""Apply the LinguaGo V3.5 online/offline learning update at build time."""
import json, re, shutil, sys
from pathlib import Path
root = Path(sys.argv[1] if len(sys.argv) > 1 else 'LinguaGo-Mobile-V2')
www = root / 'www'
html_path = www / 'index.html'
cloud_path = www / 'cloud-sync.js'
if not html_path.exists() or not cloud_path.exists():
    raise SystemExit(f'Expected Capacitor web source under {www}')
html = html_path.read_text(encoding='utf-8')
cloud = cloud_path.read_text(encoding='utf-8')
assert '/auth/v1/token?grant_type=password' in cloud, 'password login flow missing'
assert '/rest/v1/learning_progress' in cloud, 'learning record sync flow missing'
assert 'storeSession(null)' in cloud, 'logout/session clearing flow missing'
assert 'localStorage.clear' not in cloud, 'destructive local data clearing detected'
audio_roots = [www / 'audio', www / 'assets' / 'audio', www / 'media']
mp3s = []
for base in audio_roots:
    if base.exists():
        mp3s.extend(sorted(base.rglob('*.mp3')))
if len(mp3s) < 25:
    raise SystemExit(f'V3.5 requires 25 bundled dialogue MP3 files; found {len(mp3s)}')
marker = '/* LINGUAGO_V35_ONLINE_OFFLINE */'
if marker not in html:
    manifest = {
        'version': '3.5.0',
        'offlineDialogueMp3': [str(p.relative_to(www)).replace('\\', '/') for p in mp3s[:25]],
        'questionBankUrls': [
            'https://raw.githubusercontent.com/juliaxu0923-dotcom/LinguaGo-Android/main/linguago-content.json',
            'https://cdn.jsdelivr.net/gh/juliaxu0923-dotcom/LinguaGo-Android@main/linguago-content.json'
        ],
        'questionBankTimeoutMs': 6500
    }
    payload = json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))
    injection = f'''
<script id="linguago-v35-config">{marker}
window.LinguaGoV35 = {payload};
window.LinguaGoV35.fetchQuestionBank = async function() {{
  const urls = window.LinguaGoV35.questionBankUrls;
  for (const url of urls) {{
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), window.LinguaGoV35.questionBankTimeoutMs);
    try {{
      const response = await fetch(url, {{cache: 'no-store', signal: controller.signal}});
      if (response.ok) return await response.json();
    }} catch (_) {{}} finally {{ clearTimeout(timer); }}
  }}
  return null;
}};
</script>
'''
    html = re.sub(r'</head>', injection + '</head>', html, count=1, flags=re.I)
    if '<script id="linguago-v35-config">' not in html:
        html = injection + html
html = html.replace('V3.4', 'V3.5').replace('v3.4', 'v3.5').replace('3.4.0', '3.5.0')
html_path.write_text(html, encoding='utf-8')
sw_path = www / 'sw.js'
if sw_path.exists():
    sw = sw_path.read_text(encoding='utf-8')
    sw, count = re.subn(r"const CACHE\s*=\s*['"][^'"]+['"]", "const CACHE='linguago-mobile-v3.5-offline-dialogues'", sw, count=1)
    if count:
        sw_path.write_text(sw, encoding='utf-8')
for filename in ('package.json', 'package-lock.json'):
    path = root / filename
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        data['version'] = '3.5.0'
        if '' in data.get('packages', {}): data['packages']['']['version'] = '3.5.0'
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(www / 'build-info.json').write_text(json.dumps({'version':'3.5.0','offlineDialogues':25,'questionBankTimeoutMs':6500,'accountUi':'session-aware','cloudSync':'preserved'}, ensure_ascii=False) + '\n', encoding='utf-8')
print('V3.5 ready: 25 offline dialogue MP3s, two question-bank URLs, 6.5s timeout, account/password login and cloud sync preserved')
