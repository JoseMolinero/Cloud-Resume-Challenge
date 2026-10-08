import importlib.util
import json
import os
import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch


class CounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = {'visitas': Mock(), 'direcciones': Mock()}
        boto3 = types.SimpleNamespace(
            resource=lambda service: types.SimpleNamespace(Table=lambda name: cls.tables[name])
        )
        path = Path(__file__).resolve().parents[1] / 'infra' / 'lambda' / 'func.py'
        spec = importlib.util.spec_from_file_location('counter_lambda', path)
        cls.func = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'boto3': boto3}), patch.dict(os.environ, {'IP_RETENTION_DAYS': '180'}):
            spec.loader.exec_module(cls.func)

    def setUp(self):
        for table in self.tables.values():
            table.update_item.reset_mock(return_value=True, side_effect=True)
        environment = patch.dict(os.environ, {'TRUST_CLOUDFRONT_HEADERS': 'false'})
        environment.start()
        self.addCleanup(environment.stop)

    @staticmethod
    def request(method='POST', source_ip='198.51.100.42', headers=None):
        return {
            'requestContext': {'http': {'method': method, 'sourceIp': source_ip}},
            'headers': headers or {},
        }

    def test_post_increments_atomically(self):
        self.tables['visitas'].update_item.return_value = {'Attributes': {'views': Decimal('42')}}

        with patch.object(self.func.time, 'time', return_value=1_700_000_000):
            result = self.func.lambda_handler(self.request(), None)

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body']), {'views': 42})
        self.tables['visitas'].update_item.assert_called_once_with(
            Key={'id': '0'},
            UpdateExpression='ADD #views :increment',
            ExpressionAttributeNames={'#views': 'views'},
            ExpressionAttributeValues={':increment': 1},
            ReturnValues='UPDATED_NEW',
        )
        details = self.tables['direcciones'].update_item.call_args.kwargs
        self.assertEqual(details['Key'], {'ip': '198.51.100.42'})
        self.assertEqual(details['ExpressionAttributeValues'][':now'], '2023-11-14T22:13:20+00:00')
        self.assertEqual(details['ExpressionAttributeValues'][':expires'], 1_700_000_000 + 180 * 86400)
        self.assertEqual(details['ExpressionAttributeValues'][':increment'], 1)

    def test_untrusted_location_headers_are_ignored(self):
        self.tables['visitas'].update_item.return_value = {'Attributes': {'views': 1}}
        event = self.request(headers={
            'CloudFront-Viewer-Address': '203.0.113.8:12345',
            'CloudFront-Viewer-Country': 'ES',
        })

        self.func.lambda_handler(event, None)

        details = self.tables['direcciones'].update_item.call_args.kwargs
        self.assertEqual(details['Key'], {'ip': '198.51.100.42'})
        self.assertNotIn(':country', details['ExpressionAttributeValues'])

    def test_trusted_cloudfront_location_is_recorded(self):
        self.tables['visitas'].update_item.return_value = {'Attributes': {'views': 1}}
        event = self.request(source_ip='192.0.2.9', headers={
            'CloudFront-Viewer-Address': '198.51.100.42:12345',
            'CloudFront-Viewer-Country': 'ES',
            'CloudFront-Viewer-Country-Region': 'AN',
        })

        with patch.dict(os.environ, {'TRUST_CLOUDFRONT_HEADERS': 'true'}):
            self.func.lambda_handler(event, None)

        details = self.tables['direcciones'].update_item.call_args.kwargs
        self.assertEqual(details['Key'], {'ip': '198.51.100.42'})
        self.assertEqual(details['ExpressionAttributeValues'][':country'], 'ES')
        self.assertEqual(details['ExpressionAttributeValues'][':region'], 'AN')

    def test_other_methods_do_not_increment(self):
        result = self.func.lambda_handler(self.request(method='GET'), None)

        self.assertEqual(result['statusCode'], 405)
        for table in self.tables.values():
            table.update_item.assert_not_called()

    def test_missing_source_ip_does_not_increment(self):
        result = self.func.lambda_handler(self.request(source_ip=None), None)

        self.assertEqual(result['statusCode'], 400)
        for table in self.tables.values():
            table.update_item.assert_not_called()

    def test_database_error_returns_failure(self):
        self.tables['direcciones'].update_item.side_effect = RuntimeError('DynamoDB unavailable')

        with patch.object(self.func.logger, 'exception'):
            result = self.func.lambda_handler(self.request(), None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(json.loads(result['body']), {'error': 'Could not process visit'})
        self.tables['visitas'].update_item.assert_not_called()


if __name__ == '__main__':
    unittest.main()
