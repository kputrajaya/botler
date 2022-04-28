import asyncio
import base64
from datetime import datetime, timedelta
import json
import os
import re
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


async def get_reply(message):
    text = message.get('text') or ''
    chat_id = message.get('chat', {}).get('id')

    try:
        # Parse text
        command, args = None, []
        if text.startswith('/'):
            args = [x for x in text[1:].split(' ') if x]
            if args:
                command = args.pop(0).lower()

        # Process command
        if command == 'bca':
            username, password = base64.b64decode(args[0]).decode('utf-8').split(':')
            return _command_bca(username, password)
        if command == 'crypto':
            return _command_crypto()
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


def _command_bca(username, password):
    from robobrowser import RoboBrowser

    browser = RoboBrowser(parser='html.parser', user_agent=USER_AGENT)
    hostname = 'https://m.klikbca.com'

    try:
        # Login
        browser.open(f'{hostname}/login.jsp')
        form = browser.get_form(method='post')
        form['value(user_id)'].value = username
        form['value(pswd)'].value = password
        browser.submit_form(form)
        if 'accountstmt' not in browser.response.text:
            raise ValueError('Failed to login.')

        # Get balance then statements
        form = browser.get_form(method='post')
        form.action = 'balanceinquiry.do'
        browser.submit_form(form)
        balances = browser.select('table[cellpadding="5"] td[align="right"] b')
        if not balances:
            raise ValueError('Failed to get balance.')
        result = {'BALANCE': balances[0].contents}
        for i in range(4):
            result = {**result, **_get_bca_statements(browser, i)}
        return result
    finally:
        # Logout
        browser.open(f'{hostname}/authentication.do?value(actions)=logout')


def _command_crypto():
    res = _get('https://indodax.com/api/btc_idr/webdata')
    data = {
        k[:-3].upper(): _format_number(v)
        for k, v in res['prices'].items()
        if k.endswith('idr')
    }
    return data


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
        res = _get(f'https://www.duniainvestasi.com/bei/summaries/{code}', use_json=False)
        price_str = re.sub(
            r'^.+?<div class="span-3 summary_value last"><div[^>]*>([\d\,]+).+$',
            r'\1',
            res,
            flags=re.M | re.S)
        price = int(price_str.replace(',', ''))
        price_map[code] = price

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


def _get_bca_statements(browser, backdate_week):
    from robobrowser.forms.fields import Input

    now = datetime.now() + timedelta(hours=7)
    end_date = now - timedelta(days=backdate_week * 7)
    start_date = end_date - timedelta(days=6)
    start_d = start_date.strftime('%d')
    start_m = start_date.strftime('%m')
    start_y = start_date.strftime('%Y')
    end_d = end_date.strftime('%d')
    end_m = end_date.strftime('%m')
    end_y = end_date.strftime('%Y')

    # Go to statements
    form = browser.get_form(method='post')
    form.action = 'accountstmt.do?value(actions)=acctstmtview'
    form_data = {
        'value(r1)': '1',
        'value(D1)': '0',
        'value(startDt)': start_d,
        'value(startMt)': start_m,
        'value(startYr)': start_y,
        'value(endDt)': end_d,
        'value(endMt)': end_m,
        'value(endYr)': end_y,
    }
    for key, value in form_data.items():
        form.add_field(Input(f'<input name="{key}" value="{value}"/>'))
    browser.submit_form(form)
    if 'IDR' not in browser.response.text:
        raise ValueError('Failed to get statements data.')

    # Get data tables
    tables = browser.select('table[cellpadding="3"] table')
    if len(tables) != 3:
        raise ValueError('Statements data is in unexpected format.')

    # Parse transactions
    transaction_table = tables[1]
    transactions = {}
    for transaction in transaction_table.select('tr')[1:]:
        cells = transaction.select('td')
        if len(cells) < 3:
            raise ValueError('Transaction data is in unexpected format.')

        # Parse and attach to transactions
        data = _parse_bca_transaction(cells, now)
        transactions[data['date']] = transactions.get(data['date'], [])
        transactions[data['date']].append([data['description'], data['amount']])
    return transactions


def _parse_bca_transaction(cells, now):
    contents = [
        x.strip()
        for x in cells[1].contents
        if x and isinstance(x, str) and x[0] not in ('<', '\n')]

    # Prepare date
    date = cells[0].text.strip()
    if date == 'PEND':
        date_parsed = now
    else:
        current_year = int(now.strftime('%Y'))
        date_parsed = datetime.strptime(f'{current_year}/{date}', '%Y/%d/%m')
        if date_parsed > now:
            date_parsed = date_parsed.replace(year=current_year - 1)
    date = date_parsed.strftime('%Y/%m/%d')

    # Prepare amount
    amount = contents[-1]
    if cells[2].text == 'DB':
        amount = f'({amount})'

    # Prepare description
    description = ' ' + ' '.join(contents[:-2]) + ' '
    for pattern, sub in (
        (r' M-BCA ', ' '),
        (r' KARTU (DEBIT|KREDIT) ', ' '),
        (r' (DB|DR|CR) ', ' '),
        (r' (BYR VIA|TRSF) E-BANKING ', ' '),
        (r' KR OTOMATIS ', ' '),
        (r' TRANSFER ', ' '),
        (r' SWITCHING ', ' '),
        (r' TANGGAL :', ' '),
        (r' ([\d]{2}/[\d]{2} )+', ' '),
        (r' [\d]{3,5}/FT[A-Z]{2,4}/WS[\d]{4,6} ', ' '),
        (r' WSID[\d]{7,8} ', ' '),
        (r' [\d]{2,} ', ' '),
        (r' (- )+', ' '),
        (rf' {amount.replace(",", "")} ', ' '),
        (r'[\s]+', ' '),
    ):
        description = re.sub(pattern, sub, description)
    description = description.upper().strip()

    return {
        'date': date,
        'amount': amount,
        'description': description,
    }
