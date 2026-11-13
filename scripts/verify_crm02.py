"""Acceptance of the real PHP consumer against a temporary HTTPS Python service."""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.verify_api04 import FOLDER, ROOT, server

CRM = Path('C:/xampp/htdocs/KrayinCRM/laravel-crm-2.2')
PHP = 'C:/xampp/php/php.exe'


def run_php(args, env, payload=None):
    process = subprocess.run(
        [PHP, *args], cwd=CRM, env=env,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True, text=True, encoding='utf-8', timeout=55,
    )
    # Do not print raw stderr / transport exceptions.
    try:
        return process.returncode, json.loads(process.stdout)
    except json.JSONDecodeError:
        raise RuntimeError('PHP did not return the expected JSON contract.') from None


def main():
    evidence = ROOT / 'docs/evidencias_crm02'
    evidence.mkdir(exist_ok=True)
    bad_key = ROOT / '.local/crm02-invalid-key.txt'
    bad_ca = ROOT / '.local/crm02-invalid-ca.pem'
    bad_key.write_text('invalid-test-key-' * 3)
    bad_ca.write_text('Not a valid CA certificate')
    result = {}
    try:
        with server({}) as port:
            env = os.environ.copy()
            env.update({
                'CHURN_API_URL': f'https://127.0.0.1:{port}',
                'CHURN_CLIENT_KEY_FILE': str(FOLDER / 'api-key.txt'),
                'CHURN_CLIENT_CA_FILE': str(FOLDER / 'cert.pem'),
                'CHURN_EXPECTED_MODEL': 'churn180-v1',
            })
            code, prediction = run_php(['artisan', 'churn:predict-customer', 'AA-10315', '--as-of=2018-06-30'], env)
            assert code == 0, prediction
            with (ROOT / 'ML/artifacts/churn180-v1/test_predictions.csv').open() as stream:
                expected = next(row for row in csv.DictReader(stream) if row['Customer ID'] == 'AA-10315')
            assert abs(prediction['probabilidad_churn'] - float(expected['probabilidad_churn'])) < 1e-12
            assert prediction['automatic_action_allowed'] is False
            result['prediction_from_database'] = prediction
            result['matches_temporal_test_probability'] = True
            payload = {'customer_id': 'TEST', 'as_of': '2018-06-30', 'history_start': '2017-01-01', 'transactions': [
                {'line_id': '1', 'order_id': '1', 'order_date': '2018-06-29', 'sales': 10.0, 'category': 'Office', 'subcategory': 'Paper'}
            ]}
            probe = [str(ROOT / 'scripts/probe_crm02.php'), str(CRM)]
            code, error = run_php(probe, env | {'CHURN_CLIENT_KEY_FILE': str(bad_key)}, payload)
            assert code == 1 and error['http_status'] == 401 and error['attempts'] == 1
            result['invalid_key'] = error
            payload['transactions'][0]['sales'] = -1
            code, error = run_php(probe, env, payload)
            assert code == 1 and error['http_status'] == 422 and error['attempts'] == 1
            result['invalid_data'] = error
            code, error = run_php(probe, env | {'CHURN_CLIENT_CA_FILE': str(bad_ca)}, payload)
            assert code == 1 and error['reason'] == 'transport_or_tls_error' and error['attempts'] == 1
            result['invalid_ca_rejected'] = error
        # The context manager has stopped the temporary service.
        code, error = run_php(probe, env, payload)
        assert code == 1 and error['reason'] == 'retries_exhausted' and error['attempts'] == 3
        result['service_stopped'] = error
        result['passed'] = True
        (evidence / 'https_real.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        bad_key.unlink(missing_ok=True)
        bad_ca.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
