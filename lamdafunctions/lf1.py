import json
import boto3
from utils import elicit_slot, confirm_intent, close, delegate, validate_table_booking

sqs = boto3.client('sqs', region_name="us-east-1")
QUEUE_URL =" https://sqs.us-east-1.amazonaws.com/474668426434/DiningBotdataqueue"

def book_table(intent_request):
    session_attributes = intent_request.get('sessionState', {}).get('sessionAttributes', {})
    session_id = intent_request.get('sessionState', {}).get('sessionId', 'default-session')
    slots = intent_request["sessionState"]["intent"]["slots"]

    email = slots["Email"]["value"]["interpretedValue"] if slots["Email"] else None
    location = slots["Location"]["value"]["interpretedValue"] if slots["Location"] else None
    dining_date = slots["DiningDate"]["value"]["interpretedValue"] if slots["DiningDate"] else None
    dining_time = slots["DiningTime"]["value"]["interpretedValue"] if slots["DiningTime"] else None
    num_people = slots["NumberOfPeople"]["value"]["interpretedValue"] if slots["NumberOfPeople"] else None
    cuisine = slots["Cuisine"]["value"]["interpretedValue"] if slots["Cuisine"] else None
    

    validation_result = validate_table_booking( email,location, dining_date, dining_time, num_people, cuisine)

    if not validation_result["isValid"]:
        return {
            "sessionState": {
                "sessionAttributes": session_attributes,
                "dialogAction": {
                    "type": "ElicitSlot",
                    "slotToElicit": validation_result["violatedSlot"] 
                },
                "intent": intent_request["sessionState"]["intent"]
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": validation_result["message"]["content"]
                }
            ]
        }

    message_body = {
        "email": email,
        "location": location,
        "cuisine": cuisine,
        "dining_date": dining_date,
        "dining_time": dining_time,
        "num_people": num_people
    }

    
    try:
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        print("SQS SendMessage Response:", response)  
    except Exception as e:
        print("Error sending message to SQS:", str(e))  

    response_text = f"I have found a recommendation for you on {dining_date} at {dining_time}. Please check your email for more details."

    return {
        "sessionState": {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled"
            },
            "intent": intent_request["sessionState"]["intent"]
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_text
            }
        ]
    }

def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']

    if intent_name == 'BookTable':
        return book_table(intent_request)

    raise Exception(f"Intent with name {intent_name} not supported")

def lambda_handler(event, context):
    return dispatch(event)
