#!/usr/bin/env python3
"""Verify the V3.6 build-time output before APK and Pages publication."""
import json, re, sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else 'LinguaGo-Mobile-V2'); www=root/'www'
html=(www/'index.html').read_text(encoding='utf-8'); cloud=(www/'cloud-sync.js').read_text(encoding='utf-8')
mp3s=[]
for base in (www/'audio',www/'assets'/'audio',www/'media'):
    if base.exists(): mp3s.extend(sorted(base.rglob('*.mp3')))
checks={
 'offline_mp3_count':len(mp3s),
 'offline_mp3_29':len(mp3s)>=29,
 'native_audio_controls':'native-audio' in html and 'controls=true' in html,
 'media_session':'mediaSession' in html and 'MediaMetadata' in html,
 'harmony_audio_fix':'harmonyAudioFix' in html,
 'email_display':'data-linguago-current-email' in html,
 'logout_entry':'data-linguago-logout' in html and 'storeSession(null)' in cloud,
 'password_login':'/auth/v1/token?grant_type=password' in cloud,
 'cloud_sync':'/rest/v1/learning_progress' in cloud and 'localStorage.clear' not in cloud,
 'question_bank_timeout':'questionBankTimeoutMs' in html and '6500' in html,
}
if not all(checks[k] for k in checks if k != 'offline_mp3_count'):
    raise SystemExit('V3.6 verification failed: '+json.dumps(checks,ensure_ascii=False))
(www/'v36-verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V3.6 verification passed: '+json.dumps(checks,ensure_ascii=False))
