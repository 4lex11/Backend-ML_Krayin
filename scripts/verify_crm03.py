"""Real HTTPS prediction persistence, duplicate protection and failure preservation."""

import json
import os

from scripts.verify_api04 import FOLDER, ROOT, server
from scripts.verify_crm02 import CRM, run_php


def main():
    evidence = ROOT / 'docs/evidencias_crm03'
    evidence.mkdir(exist_ok=True)
    key = ROOT / '.local/crm03-invalid-key.txt'
    key.write_text('invalid-test-key-' * 3)
    command = ['artisan', 'churn:predict-customer', 'AA-10315', '--as-of=2018-06-30', '--save']
    try:
        with server({}) as port:
            env = os.environ.copy() | {
                'CHURN_API_URL': f'https://127.0.0.1:{port}',
                'CHURN_CLIENT_KEY_FILE': str(FOLDER / 'api-key.txt'),
                'CHURN_CLIENT_CA_FILE': str(FOLDER / 'cert.pem'),
                'CHURN_EXPECTED_MODEL': 'churn180-v1',
            }
            code, first = run_php(command, env)
            assert code == 0, first
            code, second = run_php(command, env)
            assert code == 0 and second['created'] is False
            assert first['prediction_id'] == second['prediction_id']
            assert first['prediction'] == second['prediction']
            assert abs(first['prediction']['probabilidad_churn'] - 0.3400690869680104) < 1e-12
            code, failed = run_php(command, env | {'CHURN_CLIENT_KEY_FILE': str(key)})
            assert code == 1 and failed['http_status'] == 401
            code, audit = run_php([str(ROOT / 'scripts/audit_crm03.php'), str(CRM)], env)
            assert code == 0 and len(audit['predictions']) == 1
            assert [r['status'] for r in audit['recent_runs']][:2] == ['failed', 'reused']
            assert audit['recent_runs'][0]['http_status'] == 401
            assert audit['recent_runs'][0]['prediction_id'] is None
            assert json.loads(audit['predictions'][0]['response']) == first['prediction']
            result = {'passed': True, 'first': first, 'repeat': second, 'failed_call': failed, 'database': audit}
            (evidence / 'persistencia_https.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf8')
            print(json.dumps({'passed': True, 'prediction_id': first['prediction_id'], 'prediction_rows': len(audit['predictions']), 'run_statuses': [r['status'] for r in audit['recent_runs']], 'valid_prediction_preserved': True}))
    finally:
        key.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
