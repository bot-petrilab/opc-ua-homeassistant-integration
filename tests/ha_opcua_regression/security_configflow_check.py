import asyncio, json
from playwright.async_api import async_playwright

URL='http://localhost:8123'; USER='admin'; PASS='Admin123'

async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(headless=True)
    page=await b.new_page(); page.set_default_timeout(30000)
    await page.goto(URL); await page.wait_for_timeout(1000)
    if await page.locator('input[name="username"]').count()>0:
      await page.fill('input[name="username"]',USER); await page.fill('input[name="password"]',PASS); await page.keyboard.press('Enter'); await page.wait_for_timeout(3000)

    async def api(m,path,data=None):
      raw = await page.evaluate('''async (a)=>{const ha=document.querySelector('home-assistant');try{return JSON.stringify({ok:true,out:await ha.hass.callApi(a.m,a.p,a.d||undefined)});}catch(e){return JSON.stringify({ok:false,err:e});}}''', {'m':m,'p':path,'d':data})
      obj=json.loads(raw)
      if not obj['ok']: raise RuntimeError(obj['err'])
      return obj['out']

    entries=await api('GET','config/config_entries/entry')
    for e in [x for x in entries if x.get('domain')=='opcua' and x.get('title') in ['SEC CFG TEST','SEC CFG TEST 2']]:
      try: await api('DELETE',f"config/config_entries/entry/{e['entry_id']}")
      except Exception: pass

    init=await api('POST','config/config_entries/flow',{'handler':'opcua'})
    fid=init['flow_id']
    r1=await api('POST',f'config/config_entries/flow/{fid}',{
      'title':'SEC CFG TEST',
      'endpoint':'opc.tcp://127.0.0.1:4840',
      'security_policy':'Basic256Sha256_Sign',
      'scan_interval':2,
      'validate_on_save':False,
    })

    ok_missing = r1.get('type')=='form' and 'client_cert_path' in (r1.get('errors') or {}) and 'client_key_path' in (r1.get('errors') or {})

    init2=await api('POST','config/config_entries/flow',{'handler':'opcua'})
    fid2=init2['flow_id']
    r2=await api('POST',f'config/config_entries/flow/{fid2}',{
      'title':'SEC CFG TEST 2',
      'endpoint':'opc.tcp://127.0.0.1:4842',
      'security_policy':'Basic256Sha256_Sign',
      'client_cert_path':'/tmp/fake-client.crt',
      'client_key_path':'/tmp/fake-client.key',
      'scan_interval':2,
      'validate_on_save':False,
    })

    ok_create = r2.get('type')=='create_entry'

    print('ok_missing_required', ok_missing)
    print('ok_create_without_validation', ok_create)
    if not (ok_missing and ok_create):
      raise RuntimeError(f'checks failed: r1={r1} r2={r2}')

    await b.close()

asyncio.run(main())
