import json
import boto3
import random
import os
import requests

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

DYNAMO_TABLE_NAME = os.environ.get('DYNAMO_TABLE_NAME')
OPENSEARCH_URL = os.environ.get('OPENSEARCH_URL')
SES_SENDER_EMAIL = os.environ.get('SES_SENDER_EMAIL')

OPENSEARCH_USERNAME = os.environ.get('user_name', 'janardhanareddyms')
OPENSEARCH_PASSWORD = os.environ.get('password', 'Janu@123')

if not all([DYNAMO_TABLE_NAME, OPENSEARCH_URL, SES_SENDER_EMAIL, OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD]):
    raise ValueError("Missing required environment variables in AWS Lambda.")

def lambda_handler(event, context):
    print(f"🔍 Received Event: {json.dumps(event, indent=2)}")

    try:
        for record in event.get("Records", []):
            message_body = json.loads(record["body"])
            print(f"Processing Message: {json.dumps(message_body, indent=2)}")

            cuisine_type = message_body.get("cuisine")
            location = message_body.get("location")
            user_email = message_body.get("email")

            if not cuisine_type or not user_email or not location:
                print("Missing required fields in message.")
                continue 


            search_query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"cuisine": cuisine_type}},
                            {"match": {"location": location}}
                        ]
                    }
                },
                "size": 10
            }

            headers = {"Content-Type": "application/json"}
            search_url = f"{OPENSEARCH_URL}/resdatabasic/_search"

            response = requests.get(search_url, auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD), headers=headers, json=search_query)

            if response.status_code != 200:
                print(f" OpenSearch query failed: {response.text}")
                continue 

            search_results = response.json()
            hits = search_results.get("hits", {}).get("hits", [])
            if not hits:
                print(f"No OpenSearch results for {cuisine_type} in {location}")
                continue

            selected_hit = random.choice(hits)["_source"]
            business_id = selected_hit["business_id"]

            table = dynamodb.Table(DYNAMO_TABLE_NAME)
            db_response = table.get_item(Key={"business_id": business_id})

            restaurant = db_response.get("Item")
            if not restaurant:
                print(f" No restaurant details found for business_id: {business_id}")
                continue

            restaurant_name = restaurant.get("name", "Unknown Restaurant")
            address = restaurant.get("address", "Unknown Address")
            lat = restaurant.get("latitude", "N/A")
            lon = restaurant.get("longitude", "N/A")
            ratings = restaurant.get("rating", "N/A")

            email_subject = f"Your {cuisine_type} Restaurant Recommendation"

            email_body = f"""
            Hello,

            Based on your request, I recommend this place:

            🍽️ **{restaurant_name}**  
            📍 **Address:** ({address}, {location}) 
            🍴 **Cuisine:** {cuisine_type} 
            ⭐️ **Rating:** {ratings} 

            Enjoy your meal! 🍕🍜🥗  

            Best,  
            Dining Concierge Bot
            """

            ses.send_email(
                Source=SES_SENDER_EMAIL,
                Destination={'ToAddresses': [user_email]},
                Message={
                    'Subject': {'Data': email_subject},
                    'Body': {'Text': {'Data': email_body}}
                }
            )

            print(f"Email sent to {user_email}")

    except Exception as e:
        print(f"Error processing message: {str(e)}")

    return {'statusCode': 200, 'body': json.dumps('Processing complete')}