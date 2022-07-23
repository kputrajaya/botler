from sanic import Sanic
from sanic.response import empty, json, text

import utils


app = Sanic('Botler')


@app.get('/bot')
async def bot_get(request):
    text = request.args.get('text') or ''

    reply = await utils.get_reply({'text': text})
    return json(reply, sort_keys=True)


@app.post('/bot')
async def bot_post(request):
    message = request.json.get('message', {})
    chat_id = message.get('chat', {}).get('id')

    reply = await utils.get_reply(message)
    if chat_id:
        utils.send_reply(chat_id, reply)
        return empty()
    return json(reply, sort_keys=True)


@app.post('/send')
async def send_post(request):
    chat_id = request.json.get('chat_id')
    text = request.json.get('text')
    utils.send_reply(chat_id, text)
    return empty()


@app.get('/ping')
async def ping_get(_):
    return text('Pong')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, fast=True)
