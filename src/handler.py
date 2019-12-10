import base64
import json
import os

import yaml

from src import utils


def bot(event, context):
    response = {'statusCode': 200}

    try:
        # Get reply
        data = json.loads(event['body'])
        message = str(data['message']['text'])
        reply = _get_reply(message)

        # Print or send back
        echo = data.get('echo')
        if echo:
            response['headers'] = {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
            response['body'] = json.dumps(reply, sort_keys=True)
        else:
            chat_id = data['message']['chat']['id']
            _send_reply(chat_id, reply)
    except Exception as e:
        print(f'ERROR: {e}')

    return response


def _get_reply(message):
    reply = 'Sorry, I don\'t understand what you mean.'

    # Get arguments
    command, args = utils.parse_message(message)
    if not command:
        return reply

    # Process commands
    try:
        if command == 'bca':
            username, password = base64.b64decode(args[0]).decode('utf-8').split(':')
            reply = utils.get_bca_statements(username, password)
        elif command == 'crypto':
            reply = utils.get_crypto_prices()
        elif command == 'ip':
            reply = utils.get_ip_address()
        elif command == 'mc':
            hostname = args[0] if args else 'mc.kputrajaya.com'
            reply = utils.get_mc_server_status(hostname)
        elif command == 'start':
            reply = ('Hello there, please see command list to see what I can help you with.')
    except Exception as e:
        print(f'ERROR: {e}')
        reply = 'Sorry, something went wrong.'

    return reply


def _send_reply(chat_id, text):
    if not isinstance(text, str):
        text = yaml.dump(text, default_flow_style=False)
        text = f'```\n{text}\n```'

    token = os.environ['TELEGRAM_TOKEN']
    utils.post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        {'Content-Type': 'application/json'},
        {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        })
