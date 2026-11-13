"""CRM-06.1: real PHP/MariaDB/HTTPS acceptance with rolled-back test writes."""
import json, os, socket, ssl, subprocess, time
from datetime import datetime,timezone
from scripts.verify_api04 import ROOT,FOLDER,server
from scripts.verify_crm02 import CRM,PHP
OUT=ROOT/'docs/evidencias_crm061'

def start_probe(env):
    p=subprocess.Popen([PHP,str(ROOT/'scripts/probe_crm061.php'),str(CRM),str(ROOT/'ML/artifacts/churn180-v1/test_predictions.csv')],cwd=CRM,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8')
    if p.stdout.readline().strip()!='READY':
        p.kill();p.communicate();raise RuntimeError('PHP acceptance driver failed to start')
    return p

def finish_probe(p, mode='valid', timeout=180):
    try:
        stdout,_=p.communicate(mode+'\n',timeout=timeout)
        result=json.loads(stdout)
        assert p.returncode==0 and result['rollback_verified'],result
        return result
    finally:
        if p.poll() is None:p.kill();p.communicate()

def main():
    out={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'local dataset demonstration; transactional acceptance'}
    bad=ROOT/'.local/crm061-invalid-key.txt';bad.write_text('invalid-key-test-'*4)
    try:
        with server({}) as port:
            env=os.environ.copy()|{'CHURN_API_URL':f'https://127.0.0.1:{port}','CHURN_CLIENT_KEY_FILE':str(FOLDER/'api-key.txt'),'CHURN_CLIENT_CA_FILE':str(FOLDER/'cert.pem'),'CHURN_EXPECTED_MODEL':'churn180-v1'}
            out['valid']=finish_probe(start_probe(env));assert out['valid']['status']=='success' and not out['valid']['created']
            out['401']=finish_probe(start_probe(env|{'CHURN_CLIENT_KEY_FILE':str(bad)}));assert out['401']['http_status']==401 and out['401']['attempts']==1
            out['422']=finish_probe(start_probe(env),'invalid');assert out['422']['http_status']==422 and out['422']['attempts']==1
            # Occupy the four actual API slots with bounded incomplete bodies (5 s timeout).
            # PHP bootstraps first so all three retries finish while these slots remain held.
            probe=start_probe(env);connections=[]
            try:
                ctx=ssl.create_default_context(cafile=str(FOLDER/'cert.pem'))
                key=(FOLDER/'api-key.txt').read_text().strip()
                for _ in range(4):
                    conn=ctx.wrap_socket(socket.create_connection(('127.0.0.1',port),timeout=5),server_hostname='127.0.0.1');connections.append(conn)
                    conn.sendall((f'POST /v1/predict/transactions HTTP/1.1\r\nHost: 127.0.0.1\r\nX-API-Key: {key}\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{{').encode())
                time.sleep(0.1)
                out['503']=finish_probe(probe)
                assert out['503']['http_status']==503 and out['503']['attempts']==3,out['503']
            finally:
                for conn in connections:conn.close()
                if probe.poll() is None:probe.kill();probe.communicate()
            time.sleep(0.2)
            started=time.monotonic();out['batch']=finish_probe(start_probe(env),'batch',300);out['batch']['elapsed_seconds']=round(time.monotonic()-started,3)
            assert out['batch']['passed'],out['batch']
        # The real service has stopped; this is a connection failure, not a mocked error.
        out['stopped']=finish_probe(start_probe(env));assert out['stopped']['status']=='error' and out['stopped']['attempts']==3
        with server({}) as new_port:
            out['recovery']=finish_probe(start_probe(env|{'CHURN_API_URL':f'https://127.0.0.1:{new_port}'}))
            assert out['recovery']['status']=='success' and not out['recovery']['created']
        for name in ['401','422','503','stopped']:
            assert out[name]['valid_prediction_preserved'] and out[name]['run_status']=='failed' and out[name]['panel_latest_run']=='failed'
        out['passed']=True
        (OUT/'aceptacion_https.json').write_text(json.dumps(out,indent=2),encoding='utf8')
        print(json.dumps(out,indent=2))
    finally:bad.unlink(missing_ok=True)
if __name__=='__main__':main()
