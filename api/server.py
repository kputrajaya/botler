from sanic import Sanic
from sanic.response import empty, json

from api import _utils


app = Sanic(__name__)


@app.post('/bot')
async def bot(request):
    token = request.args.get('token')
    message = request.json.get('message', {})
    text = message.get('text') or ''
    chat_id = message.get('chat', {}).get('id')

    reply = await _utils.get_reply(text)
    if token and chat_id:
        _utils.send_reply(token, chat_id, reply)
        return empty()

    return json(reply, sort_keys=True)
