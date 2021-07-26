from fastapi import FastAPI

from api import _utils


app = FastAPI()


@app.post('/bot')
async def bot(request, token):
    data = await request.json()
    message = data.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = str(message.get('text') or '')

    reply = _utils.get_reply(text)
    if token and chat_id:
        _utils.send_reply(token, chat_id, reply)
        return '', 204
    return reply, 200, {'Access-Control-Allow-Origin': '*'}
