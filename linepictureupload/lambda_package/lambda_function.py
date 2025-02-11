import json
import boto3
import requests
from botocore.exceptions import NoCredentialsError
import os

# S3クライアントを作成
s3 = boto3.client('s3')

# Lambdaの環境変数LINE_CHANNEL_ACCESS_TOKENを取得
access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

# Lambda関数を作成
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    try:
        if 'body' not in event:
            raise KeyError("Missing 'body' in event")

        # イベントの `body` からメッセージIDを取得
        body = json.loads(event['body'])
        message_id = body['events'][0]['message']['id']
        
        print("Event body: " + json.dumps(body, indent=2))

        # LINE API から画像を取得
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        image_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        response = requests.get(image_url, headers=headers, stream=True)

        # LINE API のレスポンスをログに出力
        print("Response status code:", response.status_code)
        print("Response headers:", response.headers)

        # HTTP ステータスコードのチェック
        if response.status_code != 200:
            print("Error: Failed to retrieve image from LINE API")
            print("Response text:", response.text)
            return {
                'statusCode': 400,
                'body': json.dumps(f"Error: Failed to retrieve image from LINE API. Response: {response.text}")
            }

        # 画像データであるかを確認
        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            print("Error: Response is not an image. Saving response text instead.")
            print("Response text:", response.text)
            return {
                'statusCode': 400,
                'body': json.dumps(f"Error: Response is not an image. Response text: {response.text}")
            }

        # S3 に画像をアップロード
        bucket_name = "linepicture-us-east-1"
        s3.put_object(
            Bucket=bucket_name,
            Key=f"images/{message_id}.jpg",
            Body=response.content,
            ContentType=content_type  # 画像の Content-Type を設定
        )

        print(f"Image {message_id}.jpg uploaded successfully to S3")

        return {
            'statusCode': 200,
            'body': json.dumps('Image uploaded successfully to S3!')
        }

    except KeyError as e:
        print(f"KeyError: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Error: Missing key in event - {str(e)}")
        }

    except NoCredentialsError:
        print("Error: AWS credentials not available")
        return {
            'statusCode': 500,
            'body': json.dumps('Error: AWS credentials not available')
        }

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
