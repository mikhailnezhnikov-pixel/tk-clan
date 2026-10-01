import json
import urllib.request
import urllib.error
BASE='https://hk-license.89.125.1.71.sslip.io/api/v1/cabinet/contest/'
def request(action,body=None,method=None):
    req=urllib.request.Request(BASE+action,data=json.dumps(body).encode() if body is not None else None,
        headers={'Origin':'https://tk-clan.ru','Content-Type':'application/json'},method=method)
    try:r=urllib.request.urlopen(req,timeout=20)
    except urllib.error.HTTPError as exc:r=exc
    with r:
        raw=r.read()
        return r.status,dict(r.headers),json.loads(raw) if raw else {}
code,headers,data=request('status')
assert code==200 and data['visible'] is True and data['phase'] in ('scheduled','open') and data['start_at']==1790861400,(code,data)
assert 'stages' not in data and 'leaderboard' not in data and 'admin_config' not in data
assert headers.get('Access-Control-Allow-Origin')=='https://tk-clan.ru',headers
print('LIVE_PUBLIC_TIMER_ONLY=PASS; no tasks, answers, or rating exposed')
code,_,data=request('login',{'telegram':{}})
assert code==401 and data['error']=='invalid_telegram_login',(code,data)
code,_,data=request('answer',{'stage':0,'answer':'test'})
assert code==401 and data['error']=='unauthorized',(code,data)
code,headers,_=request('answer',method='OPTIONS')
assert code in (200,204) and headers.get('Access-Control-Allow-Origin')=='https://tk-clan.ru'
print('LIVE_AUTH_AND_CORS=PASS')
with urllib.request.urlopen('https://hk-license.89.125.1.71.sslip.io/health',timeout=20) as response:
    assert response.status==200
print('LIVE_SERVICE_HEALTH=PASS')
