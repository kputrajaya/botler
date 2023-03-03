import asyncio
import json
import os
import random
import socket
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from aioify import aioify
import werkzeug


werkzeug.cached_property = werkzeug.utils.cached_property

MSG_START = 'Hi there, open command list to see what I can help you with.'
MSG_UNKNOWN = 'Hmm, I don\'t understand what you mean.'
MSG_ERROR = 'Sorry, something went wrong.'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
ICEBREAKER_QUESTIONS = [
    'Are you a morning person or a night person?',
    'Are you a traveler or a homebody?',
    'Are you reading anything interesting right now?',
    'As a child, what did you want to be when you grew up?',
    'Be honest, how often do you work from bed?',
    'Do you have a dedicated office space at home?',
    'Do you have a favorite breakfast?',
    'Do you have a favorite plant?',
    'Do you think you could live without your smartphone for 24 hours?',
    'Favorite weird (but brilliant) food combo?',
    'Have you ever met anyone famous?',
    'Have you ever met your idol or someone you revere greatly?',
    'Have you seen any good movies or shows lately?',
    'How do you stay productive and motivated working virtually?',
    'How many cities have you lived in during your life and which is your favorite?',
    'How would your best friend describe you?',
    'How would your enemy describe you?',
    'If you could be any animal in the world, what animal would you choose to be?',
    'If you could be any supernatural creature, what would you be and why?',
    'If you could be guaranteed one thing in life (besides money), what would it be?',
    'If you could be immortal, what age would you choose to stop aging at and why?',
    'If you could be on a reality TV show, which one would you choose and why?',
    'If you could change places with anyone in the world, who would it be and why?',
    'If you could commit any crime and get away with it what would you choose and why?',
    'If you could eliminate one thing from your daily routine, what would it be and why?',
    'If you could go to Mars, would you? Why or why not?',
    'If you could hang out with any cartoon character, who would you choose and why?',
    'If you could have dinner with one person, dead or alive, who would it be and why?',
    'If you could have someone follow you around all the time like a personal assistant, what would you have them do?',
    'If you could have the power of teleportation right now, where would you go and why?',
    'If you could instantly become an expert in something, what would it be?',
    'If you could live anywhere in the world for a year, where would it be?',
    'If you could magically become fluent in any language, what would it be?',
    'If you could only use one piece of technology, what would it be?',
    'If you could see one movie again for the first time, what would it be and why?',
    'If you could travel anywhere in the world today, where would you go?',
    'If you could write a book that was guaranteed to be a best seller, what would you write?',
    'If you didn\'t have to work right now, what would you be doing instead?',
    'If you had a time machine and could only use it once, would you go back in time or into the future?',
    'If you had one free hour each day, what would you do?',
    'If you had to delete all but 3 apps from your smartphone, which ones would you keep?',
    'If you had to teach a class on one thing, what would you teach?',
    'If you were to donate to one charity, what would it be and why?',
    'If you were to host your own talk show, who would be your first guest?',
    'If your life were a TV show, what genre would it be?',
    'What book, movie read/seen recently you would recommend and why?',
    'What breed of dog would you be?',
    'What does your favorite shirt look like?',
    'What does your morning routine look like when working from home?',
    'What is the best gift ever you ever received?',
    'What is your absolute dream job?',
    'What is your cellphone wallpaper?',
    'What is your favorite beverage?',
    'What is your favorite dessert?',
    'What is your favorite food?',
    'What is your favorite hobby or pastime?',
    'What is your favorite item you\'ve bought this year?',
    'What is your favorite magical or mythological animal?',
    'What is your favorite meal to cook and why?',
    'What is your favorite quotation of all time?',
    'What is your favorite time of the day and why?',
    'What is your favorite TV show?',
    'What is your most used emoji?',
    'What is your useless superpower?',
    'What languages do you know how to speak?',
    'What sport would you compete in if you were in the Olympics?',
    'What was the worst job you ever had?',
    'What was your favorite game to play as a child?',
    'What was your first job?',
    'What would the title of your autobiography be?',
    'What would your dream house be like?',
    'What\'s is one thing we don\'t know about you?',
    'What\'s the best piece of advice you\'ve ever been given?',
    'What\'s the first thing you remember buying with your own money?',
    'What\'s the hardest part about working virtually for you?',
    'What\'s your favorite place of all the places you\'ve travelled?',
    'What\'s your favorite tradition or holiday?',
    'When does time pass by way too quickly?',
    'When does time seem to crawl by at a snail\'s pace?',
    'When you die, what do you want to be remembered for?',
    'Where was the last place you went for the first time?',
    'Which one do you prefer, coffee or tea?',
    'Which one do you prefer, teleportation or flying?',
    'Which one fictional place would you most like to visit?',
    'Who is your favorite fictional hero or heroine?',
    'Who was most influential in your life as a kid?',
    'Would you rather be able to fly or turn invisible?',
    'Would you rather give up your smartphone or your computer?',
    'Would you rather lose all of your money or all of your pictures?',
    'You have a time machine. When (and where) would you like to visit first?',
]


async def get_reply(message):
    text = message.get('text') or ''
    chat_id = message.get('chat', {}).get('id')

    try:
        command, args = None, []
        if text.startswith('/'):
            args = [x for x in text[1:].split(' ') if x]
            if args:
                command = args.pop(0).lower()
        return await _command(command, args, chat_id)
    except Exception as e:
        print(f'Error @ get_reply: {e}')
        return MSG_ERROR


def send_reply(chat_id, text):
    if not chat_id or not text:
        return

    try:
        if not isinstance(text, str):
            text = json.dumps(text, sort_keys=True, indent=2)
            text = f'```\n{text}\n```'
        _post(
            f'https://api.telegram.org/bot{os.environ["TELEGRAM_BOT_TOKEN"]}/sendMessage',
            {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            },
            {'Content-Type': 'application/json'})
    except Exception as e:
        print(f'Error @ send_reply: {e}')


def _format_number(value):
    return int(value) if int(value) < 1000 else '{:,}'.format(int(value))


def _get(url, use_json=True):
    return _request(Request(url, headers={'User-Agent': USER_AGENT}), use_json)


def _post(url, payload, headers={}, use_json=True):
    data = (json.dumps(payload) if use_json else payload).encode('utf-8')
    return _request(Request(url, headers={**headers, 'User-Agent': USER_AGENT}, data=data), use_json)


def _request(request, use_json):
    try:
        with urlopen(request) as res:
            encoding = res.info().get_content_charset('utf-8')
            body = res.read().decode(encoding)
            return json.loads(body) if use_json else body
    except HTTPError as e:
        raise ValueError(f'{e.code}: {e.read().decode()}')


async def _command(command, args, chat_id):
    if command == 'crypto':
        return _command_crypto()
    if command == 'icebreaker':
        return _command_icebreaker()
    if command == 'id':
        return _command_id(chat_id)
    if command == 'ip':
        return _command_ip()
    if command == 'mc':
        hostname = args[0]
        return _command_mc(hostname)
    if command == 'port':
        hostname = args[0]
        port = int(args[1])
        return _command_port(hostname, port)
    if command == 'start':
        return MSG_START
    if command == 'stock':
        stock_map = {}
        for arg in args:
            code, count = arg.split('=')
            stock_map[code] = int(count)
        return await _command_stock(stock_map)
    return MSG_UNKNOWN


def _command_crypto():
    res = _get('https://indodax.com/api/btc_idr/webdata')
    data = {
        k[:-3].upper(): _format_number(v)
        for k, v in res['prices'].items()
        if k.endswith('idr')
    }
    return data


def _command_icebreaker():
    return {
        'QUESTION': random.choice(ICEBREAKER_QUESTIONS)
    }


def _command_id(chat_id):
    return {
        'ID': chat_id
    }


def _command_ip():
    res = _get('https://api.ipify.org/?format=json')
    return {
        'IP': res.get('ip')
    }


def _command_mc(hostname):
    res = _get(f'https://api.mcsrvstat.us/1/{hostname}')
    data = {
        'HOSTNAME': res['hostname'],
        'ONLINE': not res.get('offline', False),
        'PLAYERS': res.get('players')
    }
    if not data['PLAYERS']:
        data.pop('PLAYERS')
    return data


def _command_port(hostname, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((hostname, port))
    sock.close()
    return {
        'OPEN': result == 0
    }


async def _command_stock(stock_map):
    price_map = {}

    @aioify
    def populate_price(code):
        res = _get(f'https://pasardana.id/api/Stock/GetByCode?code={code}&username=anonymous')
        price_map[code] = res['LastData']['AdjustedClosingPrice']

    tasks = [populate_price(code) for code in stock_map.keys()]
    await asyncio.gather(*tasks)

    total = 0
    detail = {}
    for code, lot_count in stock_map.items():
        price = price_map.get(code)
        if price is None:
            continue
        value = lot_count * 100 * price
        detail[code.upper()] = f'{_format_number(price)} x {_format_number(lot_count)} = {_format_number(value)}'
        total += value
    return {
        'STOCKS': detail,
        'TOTAL': _format_number(total)
    }
