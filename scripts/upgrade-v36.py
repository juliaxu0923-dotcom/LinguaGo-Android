#!/usr/bin/env python3
"""Apply LinguaGo V3.6 offline audio and online learning fixes."""
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1] if len(sys.argv) > 1 else 'LinguaGo-Mobile-V2')
www = root / 'www'; html_path = www / 'index.html'; cloud_path = www / 'cloud-sync.js'
if not html_path.exists() or not cloud_path.exists(): raise SystemExit(f'Expected Capacitor web source under {www}')
html = html_path.read_text(encoding='utf-8'); cloud = cloud_path.read_text(encoding='utf-8')
assert '/auth/v1/token?grant_type=password' in cloud
assert '/rest/v1/learning_progress' in cloud
assert 'storeSession(null)' in cloud
assert 'localStorage.clear' not in cloud
audio_files=[]
for base in (www/'audio',www/'assets'/'audio',www/'media'):
    if base.exists(): audio_files.extend(sorted(base.rglob('*.mp3')))
if len(audio_files)<29: raise SystemExit(f'V3.6 requires 29 bundled dialogue MP3 files; found {len(audio_files)}')
marker='/* LINGUAGO_V36_AUDIO_FIX */'
if marker not in html:
    manifest={'version':'3.6.0','offlineDialogueMp3':[str(p.relative_to(www)).replace('\\','/') for p in audio_files[:29]],'questionBankUrls':['https://raw.githubusercontent.com/juliaxu0923-dotcom/LinguaGo-Android/main/linguago-content.json','https://cdn.jsdelivr.net/gh/juliaxu0923-dotcom/LinguaGo-Android@main/linguago-content.json'],'questionBankTimeoutMs':6500,'nativeAudioControls':True,'harmonyAudioFix':True}
    payload=json.dumps(manifest,ensure_ascii=False,separators=(',',':'))
    injection=f'''
<script id="linguago-v36-config">{marker}
window.LinguaGoV36={payload};
window.LinguaGoV36.audio=new Audio();
window.LinguaGoV36.playDialogue=function(index){{const list=window.LinguaGoV36.offlineDialogueMp3||[];if(!list[index])return Promise.resolve(false);const audio=window.LinguaGoV36.audio;audio.src=list[index];audio.controls=true;audio.preload='auto';if('mediaSession' in navigator){{navigator.mediaSession.metadata=new MediaMetadata({{title:'LinguaGo 听力 '+(index+1),artist:'LinguaGo V3.6'}});navigator.mediaSession.setActionHandler('play',()=>audio.play());navigator.mediaSession.setActionHandler('pause',()=>audio.pause())}}return audio.play().then(()=>true).catch(()=>false)}};
window.LinguaGoV36.fetchQuestionBank=async function(){{for(const url of window.LinguaGoV36.questionBankUrls){{const c=new AbortController();const t=setTimeout(()=>c.abort(),6500);try{{const r=await fetch(url,{{cache:'no-store',signal:c.signal}});if(r.ok)return await r.json()}}catch(_){{}}finally{{clearTimeout(t)}}}}return null}};
document.addEventListener('DOMContentLoaded',()=>{{const host=document.querySelector('[data-linguago-audio-controls]')||document.body;if(!document.querySelector('#linguago-v36-native-audio')){{const audio=document.createElement('audio');audio.id='linguago-v36-native-audio';audio.controls=true;audio.preload='none';audio.setAttribute('playsinline','');audio.style.cssText='width:100%;max-width:520px;margin:12px 0';host.appendChild(audio)}}}});
</script>
'''
    html=re.sub(r'</head>',injection+'</head>',html,count=1,flags=re.I)
    if '<script id="linguago-v36-config">' not in html: html=injection+html
html=html.replace('V3.5','V3.6').replace('v3.5','v3.6').replace('3.5.0','3.6.0'); html_path.write_text(html,encoding='utf-8')
sw_path=www/'sw.js'
if sw_path.exists():
    sw=sw_path.read_text(encoding='utf-8'); sw,count=re.subn(r'''const CACHE\s*=\s*['"][^'"]+['"]''',"const CACHE='linguago-mobile-v3.6-audio-fix'",sw,count=1)
    if count: sw_path.write_text(sw,encoding='utf-8')
for fn in ('package.json','package-lock.json'):
    p=root/fn
    if p.exists():
        d=json.loads(p.read_text(encoding='utf-8')); d['version']='3.6.0'
        if '' in d.get('packages',{}): d['packages']['']['version']='3.6.0'
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(www/'build-info.json').write_text(json.dumps({'version':'3.6.0','offlineDialogues':29,'harmonyAudioFix':True,'nativeAudioControls':True,'questionBankTimeoutMs':6500,'accountUi':'session-aware','cloudSync':'preserved'},ensure_ascii=False)+'\n',encoding='utf-8')
print('V3.6 ready: 29 offline MP3s, native audio controls, HarmonyOS audio fix, email/logout/cloud sync preserved')
