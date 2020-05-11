from flask import Flask, request

from api import _utils


app = Flask(__name__)


@app.route('/bot', methods=['POST'])
def bot():
    data = request.json
    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    message = str(message.get('text') or '')
    reply = _utils.get_reply(message)

    if chat_id:
        _utils.send_reply(chat_id, reply)
        return None
    return reply, {'Access-Control-Allow-Origin': '*'}
