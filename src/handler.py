import base64
import json
import os

from src import utils


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
    reply = 'Sorry, I don\'t understand what you mean.'

    # Get arguments
    command, args = utils.parse_message(message)
    if not command:
        return reply

    # Process commands
    try:
        if command == 'bca':
            credentials = base64.b64decode(args[0]).decode('utf-8').split(':')
            username = credentials[0]
            password = credentials[1]
            reply = utils.get_bca_statements(username, password)
        elif command == 'crypto':
            reply = utils.get_crypto_prices()
        elif command == 'ip':
            reply = utils.get_ip_address()
        elif command == 'mc':
            hostname = args[0] if args else 'mc.heyimkev.in'
            reply = utils.get_mc_server_status(hostname)
        elif command == 'start':
            reply = ('Hello there, please see command list to see '
                     'what I can help you with.')
    except Exception as e:
        reply = 'Sorry, something went wrong.'
        print(f'ERROR: {e}')

    # Format as pretty JSON
    if not isinstance(reply, str):
        reply = json.dumps(reply, indent=2)
        reply = f'```\n{reply}\n```'

    return reply


def _send_reply(chat_id, text):
    token = os.environ['TELEGRAM_TOKEN']
    utils.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        {'Content-Type': 'application/json'},
        {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        })
