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
        _send_reply(chat_id, reply)
    except Exception as e:
        print(e)

    return {'statusCode': 200}


def _get_reply(message):
    reply = 'Sorry, I don\'t understand what you said.'
    if not message or not message.startswith('/'):
        return reply

    # Process commands
    try:
        command = message.split(' ')[0][1:].lower()
        if command == 'crypto':
            data = _get('https://indodax.com/api/btc_idr/webdata')
            reply = data['prices']
        elif command == 'mc':
            data = _get('https://api.mcsrvstat.us/1/mc.heyimkev.in')
            reply = {
                'motd': data['motd']['clean'],
                'players': data['players']['list']
            }
    except Exception as e:
        print(e)
        reply = 'Sorry, something went wrong.'

    # Format as pretty JSON
    if not isinstance(reply, str):
        reply = '```' + json.dumps(reply, indent=2) + '```'

    return reply


def _send_reply(chat_id, text):
    # Prepare URL, headers, and data
    token = os.environ['TELEGRAM_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    headers = {'Content-Type': 'application/json'}
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }

    # Call Telegram API
    req = request.Request(
        url,
        headers=headers,
        data=json.dumps(data).encode('utf-8'))
    request.urlopen(req)


def _get(url):
    res = request.urlopen(url)
    encoding = res.info().get_param('charset') or 'utf-8'
    data = json.loads(res.read().decode(encoding))
    return data
