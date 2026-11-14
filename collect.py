"""Haberleri derleyip statik JSON üretir. İddiaların doğruluğunu otomatik teyit ETMEZ."""
import calendar
import hashlib
import html
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

import feedparser
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parent
NOW = datetime.now(timezone.utc)
WINDOW_DAYS = int(os.getenv('WINDOW_DAYS', '10'))
TRANSLATE = os.getenv('TRANSLATE', '1') == '1'
MAX_ITEMS = int(os.getenv('MAX_ITEMS', '120'))
HEADERS = {'User-Agent': 'AIDunyaNewsCollector/1.0 (+public educational RSS aggregator)'}
STOP = set('the a an and or to for with of in on at is are from by new latest how why as it its into after this that about ai artificial intelligence model models says launches launch unveils announces announced reveals researchers research study company tech use using can will could has have more over under their our what when now gets gets'.split())
AI_WORDS = re.compile(r'\b(ai|artificial intelligence|machine learning|llm|gpt|gemini|claude|deepseek|qwen|robot|neural|openai|anthropic|agentic|mistral|language model|generative|transformer|deep learning|chip|nvidia|inference)\b', re.I)


def canonical(url):
    p = urlsplit(url.strip())
    params = [(k, v) for k, v in parse_qsl(p.query) if not k.startswith('utm_') and k not in ('fbclid','gclid')]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip('/'), urlencode(params), ''))


def clean(s):
    return re.sub(r'\s+', ' ', BeautifulSoup(html.unescape(str(s or '')), 'html.parser').get_text(' ', strip=True)).strip()


def dt_from_entry(entry):
    for k in ('published_parsed', 'updated_parsed', 'created_parsed'):
        value = entry.get(k)
        if value:
            try:
                return datetime.fromtimestamp(calendar.timegm(value), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass
    return NOW


def keywords(title):
    return {w for w in re.findall(r'[a-z0-9]+', title.lower()) if len(w) > 2 and w not in STOP}


def similar(a, b):
    x, y = keywords(a['original_title']), keywords(b['original_title'])
    if not x or not y:
        return False
    overlap = len(x & y)
    jac = overlap / max(1,len(x | y))
    ratio = SequenceMatcher(None, a['original_title'].lower(), b['original_title'].lower()).ratio()
    return overlap >= 3 and (jac >= 0.43 or ratio >= 0.76) and abs((a['date_obj']-b['date_obj']).days) <= 4


def classify(text, source):
    t = text.lower()
    if source['kind'] == 'onbaski': return 'Bilim ve Araştırma'
    if any(k in t for k in ['robot', 'humanoid', 'autonomous vehicle']): return 'Robotik'
    if any(k in t for k in ['regulation', 'law', 'policy', 'copyright', 'court', 'safety']): return 'Etik ve Düzenleme'
    if any(k in t for k in ['chip', 'gpu', 'semiconductor', 'data center', 'datacenter']): return 'Donanım'
    if any(k in t for k in ['model', 'gpt', 'gemini', 'claude', 'deepseek', 'qwen', 'mistral', 'llm']): return 'Yeni Modeller'
    return 'Sektör ve Uygulamalar'


def translate_text(text, translator, maxchars):
    text = text[:maxchars].strip()
    if not text or not translator: return text, False
    try:
        translated = translator.translate(text)
        if translated and translated.strip(): return translated.strip(), True
    except Exception as ex:
        print('Translation skipped:', str(ex)[:100])
    return text, False


def run():
    sources = json.loads((BASE/'sources.json').read_text(encoding='utf-8'))
    records, failures = [], []
    cutoff = NOW - timedelta(days=WINDOW_DAYS)
    for src in sources:
        try:
            r = requests.get(src['url'], headers=HEADERS, timeout=18)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            if not feed.entries: raise ValueError('Akış boş veya ayrıştırılamadı')
            num = 0
            for e in feed.entries[:45]:
                title = clean(e.get('title'))
                url = canonical(e.get('link',''))
                date = dt_from_entry(e)
                summary = clean(e.get('summary') or e.get('description') or '')[:650]
                if not title or not url.startswith('https://') or date < cutoff or date > NOW + timedelta(days=1): continue
                if src['kind'] not in ('onbaski',) and not AI_WORDS.search(title+' '+summary+' '+src['name']): continue
                records.append({'id':hashlib.sha1(url.encode()).hexdigest()[:16], 'original_title':title, 'original_summary':summary, 'url':url, 'date_obj':date, 'source':src['name'], 'kind':src['kind'], 'family':src['family'], 'region':src['region'], 'category':classify(title+' '+summary, src)})
                num += 1
            print(src['name'],num)
        except Exception as exc:
            failures.append({'source':src['name'], 'error':str(exc)[:150]})
            print('FEED ERROR', src['name'], str(exc)[:100])
    # Önce URL tekilleştirme, ardından yalnızca yüksek benzerlikli manşet eşleşmeleri.
    records = list({r['url']:r for r in records}.values())
    records.sort(key=lambda x:x['date_obj'], reverse=True)
    groups = []
    for r in records:
        match = next((g for g in groups if similar(g[0],r)), None)
        if match is None: groups.append([r])
        else: match.append(r)
    # Çok kaynaktan gelen haberler yüksek öncelikli, ancak doğrulanmış sayılmaz.
    groups.sort(key=lambda g:(len({r['family'] for r in g}) > 1, max(r['date_obj'] for r in g)), reverse=True)
    translator = None
    if TRANSLATE:
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target='tr')
        except Exception as e: print('Translator unavailable',e)
    old_path = BASE/'data'/'news.json'
    old = json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else {}
    cache = {r['url']:r for r in old.get('items',[])}
    out=[]
    for g in groups[:MAX_ITEMS]:
        lead = sorted(g, key=lambda r:({'bagimsiz':0,'resmi':1,'onbaski':2}.get(r['kind'],3),-r['date_obj'].timestamp()))[0]
        others = [r for r in g if r['url']!=lead['url'] and r['family']!=lead['family']]
        distinct = set(r['family'] for r in g)
        if lead['kind']=='onbaski':
            status='Ön baskı · hakem değerlendirmesi garanti değil'
            note='Araştırma paylaşılmıştır; sonuçların bağımsız tekrarı veya hakem onayı bu sistem tarafından doğrulanmamıştır.'
        elif others:
            status='Birden fazla bağımsız yayıncıda bulundu'
            note='Benzer gelişme birden fazla yayıncıda yer alıyor. Bu, iddiaların bağımsız olarak doğrulandığı anlamına gelmez.'
        else:
            status='Ek doğrulama gerekiyor'
            note='Bu gelişmeyle eşleşen ikinci bağımsız kaynak bulunamadı. Resmî açıklamalar da tarafın kendi beyanı olabilir.'
        prev=cache.get(lead['url'],{})
        if prev.get('title_tr') and prev.get('translated'):
            title_tr=prev['title_tr']; summary_tr=prev.get('summary_tr',''); translated=True
        else:
            title_tr,ok1=translate_text(lead['original_title'],translator,360)
            summary_tr,ok2=translate_text(lead['original_summary'],translator,500)
            translated=ok1 and (ok2 or not lead['original_summary'])
        item={'id':lead['id'],'title_tr':title_tr,'summary_tr':summary_tr,'translated':translated,
              'original_title':lead['original_title'],'date':lead['date_obj'].isoformat(),
              'category':lead['category'],'region':lead['region'],'status':status,'verification_note':note,
              'source_count':len(distinct), 'sources':[{'name':r['source'],'url':r['url'],'kind':r['kind']} for r in [lead]+others[:4]]}
        out.append(item)
        time.sleep(0.10 if translator else 0)
    # Yeni kaynak çekilemezse son kayıtlar silinmesin.
    if not out and cache:
        print('WARNING: all feeds failed; keeping old data')
        return
    payload={'updated_at':NOW.isoformat(),'item_count':len(out),'feed_failures':failures,'items':out}
    (BASE/'data').mkdir(exist_ok=True)
    old_path.write_text(json.dumps(payload,ensure_ascii=False,indent=2), encoding='utf-8')
    print('Saved',len(out),'news groups,',len(failures),'failed feeds')

if __name__=='__main__': run()
