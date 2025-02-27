import json
import boto3

lex_client = boto3.client('lexv2-runtime')

def lambda_handler(event, context):
    """Handles API requests and forwards them to Amazon Lex."""

    print("Received Event:", json.dumps(event))  

    try:
        body = event.get("body", {})
        messages = body.get("messages", [])
        user_message = messages[0]["unstructured"]["text"] if messages else "No message received"

        if not user_message:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "No message provided."})
            }

        lex_response = lex_client.recognize_text(
            botId='BKIHGC6E2Z',
            botAliasId='TSTALIASID',
            localeId='en_US',
            sessionId='12345',
            text=user_message
        )

        messages = lex_response.get('messages', [])
        lex_messages = [msg['content'] for msg in lex_response.get('messages', [])]

        return {
            "statusCode": 200,
            "body": json.dumps({"response": lex_messages})
        }

    except KeyError as e:
        print("KeyError:", str(e))
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing key in request: {str(e)}"})
        }
    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }