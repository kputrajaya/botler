from typing import Optional

from fastapi import FastAPI, Response
from pydantic import BaseModel

from api import _utils


app = FastAPI()


class Chat(BaseModel):
    id: int


class Message(BaseModel):
    chat: Optional[Chat]
    text: str


class Data(BaseModel):
    message: Message


@app.post('/bot')
async def bot(data: Data, response: Response, token: Optional[str] = None):
    reply = _utils.get_reply(data.message.text)
    if token and data.message.chat:
        _utils.send_reply(token, data.message.chat.id, reply)
        return None
    response.headers['Access-Control-Allow-Origin'] = '*'
    return reply
