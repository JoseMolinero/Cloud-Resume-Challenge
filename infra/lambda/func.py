import ipaddress
import json
import logging
import os
import time
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource('dynamodb')
table_visitas = dynamodb.Table('visitas')
table_direcciones = dynamodb.Table('direcciones')
logger = logging.getLogger(__name__)
RETENTION_DAYS = int(os.getenv('IP_RETENTION_DAYS', '180'))


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body),
    }


def lambda_handler(event, context):
    http = event.get('requestContext', {}).get('http', {})
    method = http.get('method')
    if method != 'POST':
        return response(405, {'error': 'Method not allowed'})

    ip = http.get('sourceIp')
    headers = {key.lower(): value for key, value in event.get('headers', {}).items()}
    trusted_cloudfront = os.getenv('TRUST_CLOUDFRONT_HEADERS') == 'true'
    if trusted_cloudfront and headers.get('cloudfront-viewer-address'):
        address = headers['cloudfront-viewer-address'].rsplit(':', 1)[0].strip('[]')
        try:
            ip = str(ipaddress.ip_address(address))
        except ValueError:
            logger.warning('Invalid CloudFront viewer address')
            return response(400, {'error': 'Invalid viewer address'})

    if not ip:
        return response(400, {'error': 'Missing source IP'})

    try:
        now = int(time.time())
        timestamp = datetime.fromtimestamp(now, timezone.utc).isoformat()
        details = {
            ':increment': 1,
            ':now': timestamp,
            ':expires': now + RETENTION_DAYS * 86400,
        }
        names = {
            '#first_seen': 'first_seen',
            '#last_seen': 'last_seen',
            '#expires_at': 'expires_at',
            '#visits': 'visits',
        }
        update = ('SET #first_seen = if_not_exists(#first_seen, :now), '
                  '#last_seen = :now, #expires_at = :expires')
        if trusted_cloudfront:
            for name, header in (('country', 'cloudfront-viewer-country'),
                                 ('region', 'cloudfront-viewer-country-region')):
                if headers.get(header):
                    update += f', #{name} = :{name}'
                    names[f'#{name}'] = name
                    details[f':{name}'] = headers[header]

        table_direcciones.update_item(
            Key={'ip': ip},
            UpdateExpression=update + ' ADD #visits :increment',
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=details,
        )
        result = table_visitas.update_item(
            Key={'id': '0'},
            UpdateExpression='ADD #views :increment',
            ExpressionAttributeNames={'#views': 'views'},
            ExpressionAttributeValues={':increment': 1},
            ReturnValues='UPDATED_NEW',
        )
        return response(200, {'views': int(result['Attributes']['views'])})
    except Exception:
        logger.exception('Error processing visit')
        return response(500, {'error': 'Could not process visit'})
