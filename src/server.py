from sanic import Sanic
from sanic.response import empty, json

import utils


app = Sanic('Botler')


@app.get('/bot')
async def get(request):
    text = request.args.get('text') or ''

    reply = await utils.get_reply({'text': text})
    return json(reply, sort_keys=True)


@app.post('/bot')
async def post(request):
    token = request.args.get('token')
    message = request.json.get('message', {})
    chat_id = message.get('chat', {}).get('id')

    reply = await utils.get_reply(message)
    if token and chat_id:
        utils.send_reply(token, chat_id, reply)
        return empty()
    return json(reply, sort_keys=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, fast=True)
