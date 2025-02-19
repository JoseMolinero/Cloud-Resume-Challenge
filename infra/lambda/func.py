import json
import boto3

# Conectar con DynamoDB
dynamodb = boto3.resource('dynamodb')
table_visitas = dynamodb.Table('visitas')
table_direcciones = dynamodb.Table('direcciones')

def lambda_handler(event, context):
    try:
        # **Obtener la IP desde la petición**
        body = json.loads(event['body']) if 'body' in event else {}
        ip_address = body.get('ip', 'Desconocida')

        # **Actualizar la tabla de visitas**
        response = table_visitas.get_item(Key={'id': '0'})
        views = response['Item']['views'] + 1 if 'Item' in response else 1  # Inicializar si no existe

        table_visitas.put_item(Item={'id': '0', 'views': views})

        # **Guardar la IP en la tabla "direcciones"**
        table_direcciones.put_item(Item={'ip': ip_address})

        return {
            "statusCode": 200,
            "body": json.dumps({views})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Ocurrió un error al procesar la solicitud"})
        }
