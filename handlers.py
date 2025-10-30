import time
import uuid

def handle_email(payload):
    """
    Expected payload:
    {
        "to": "user@example.com",
        "subject": "Hello",
        "body": "Message content"
    }
    
    TODO:
    1. Print "Sending email to {to}..."
    2. Sleep for 2 seconds (simulate network call)
    3. Return success result with message_id
    
    Example return:
    {
        "status": "sent",
        "message_id": "msg_abc123",
        "to": payload['to']
    }
    """
    # 1. Print "Sending email to {to}..."
    print(f"Sending email to {payload['to']}...")

    # 2. Sleep for 2 seconds (simulate network call)
    time.sleep(2)
    
    # 3. Return success result with message_id
    message_id = f"msg_{uuid.uuid4().hex[:10]}"
    return {
        "status": "sent",
        "message_id": message_id,
        "to": payload['to']
    }
