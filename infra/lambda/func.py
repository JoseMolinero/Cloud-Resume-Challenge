import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_visitas = dynamodb.Table('visitas')
table_direcciones = dynamodb.Table('direcciones')

def decimal_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError

def lambda_handler(event, context):

    try:
        body = json.loads(event.get('body', '{}'))
        ip_address = body.get('ip', 'Desconocida')

        response = table_visitas.get_item(Key={'id': '0'})
        views = response.get('Item', {}).get('views', 0) + 1

        table_visitas.put_item(Item={'id': '0', 'views': views})

        table_direcciones.put_item(Item={'ip': ip_address})

        return views
        

    except Exception as e:
        print(f"Error: {str(e)}")
        return "Ocurrió un error al procesar la solicitud"
