import json
import os
from urllib import request


def bot(event, context):
    try:
        # Parse input
        data = json.loads(event['body'])
        chat_id = data['message']['chat']['id']
        message = str(data['message']['text'])

        # Get and send reply
        reply = _get_reply(message)
        _send(chat_id, reply)
    except Exception as e:
        print(e)

    return {'statusCode': 200}


def _get_reply(message):
    return 'This is a response'


def _send(chat_id, text):
    # Prepare URL, headers, and data
    token = os.environ['TELEGRAM_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    headers = {'Content-Type': 'application/json'}
    data = {'chat_id': chat_id, 'text': text}

    # Call Telegram API
    req = request.Request(
        url,
        headers=headers,
        data=json.dumps(data).encode('utf-8'))
    request.urlopen(req)
