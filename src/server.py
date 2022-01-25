from sanic import Sanic
from sanic.response import empty, json

import utils


app = Sanic('botler')


@app.post('/bot')
async def bot(request):
    token = request.args.get('token')
    message = request.json.get('message', {})
    text = message.get('text') or ''
    chat_id = message.get('chat', {}).get('id')

    reply = await utils.get_reply(text)
    if token and chat_id:
        utils.send_reply(token, chat_id, reply)
        return empty()

    return json(reply, sort_keys=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
