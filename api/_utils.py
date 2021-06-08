import base64
import datetime
import json
import re
from urllib.request import Request, urlopen

from robobrowser import RoboBrowser
from robobrowser.forms.fields import Input
import yaml

MSG_START = 'Hi there, open command list to see what I can help you with.'
MSG_UNKNOWN = 'Hmm, I don\'t understand what you mean.'
MSG_ERROR = 'Sorry, something went wrong.'


def get_reply(message):
    try:
        command, args = parse_message(message)
        if command == 'bca':
            username, password = base64.b64decode(args[0]).decode('utf-8').split(':')
            return get_bca_statements(username, password)
        if command == 'crypto':
            return get_crypto_prices()
        if command == 'ip':
            return get_ip_address()
        if command == 'mc':
            hostname = args[0] if args else 'mc.kputrajaya.com'
            return get_mc_server_status(hostname)
        if command == 'start':
            return MSG_START
        if command == 'stock':
            stock_map = {}
            for arg in args:
                arg_split = arg.split('=')
                stock_map[arg_split[0]] = int(arg_split[1])
            return get_stock_prices(stock_map)
        return MSG_UNKNOWN
    except Exception as e:
        print(f'ERROR: {e}')
        return MSG_ERROR


def send_reply(token, chat_id, text):
    if not isinstance(text, str):
        text = yaml.dump(text, default_flow_style=False)
        text = f'```\n{text}\n```'

    post(
        f'https://api.telegram.org/bot{token}/sendMessage',
        {'Content-Type': 'application/json'},
        {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        })


def parse_message(message):
    if message.startswith('/'):
        args = [x for x in message[1:].split(' ') if x]
        if args:
            command = args.pop(0).lower()
            return command, args
    return None, []


def get_bca_statements(username, password):
    browser = RoboBrowser(parser='html.parser', user_agent='Mozilla/5.0')
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


def get_crypto_prices():
    res = get('https://indodax.com/api/btc_idr/webdata')
    data = {
        k[:-3].upper(): _format_number(v)
        for k, v in res['prices'].items()
        if k.endswith('idr')
    }
    return data


def get_stock_prices(stock_map):
    total = 0
    detail = {}
    for code, lot_count in stock_map.items():
        res = get(f'https://www.idx.co.id/umbraco/Surface/ListedCompany/GetTradingInfoDaily?code={code}')
        price = res.get('ClosingPrice')
        if price is None:
            continue
        value = lot_count * 100 * price
        detail[code.upper()] = f'{_format_number(price)} x {_format_number(lot_count)} = {_format_number(value)}'
        total += value
    return {
        'STOCKS': detail,
        'TOTAL': _format_number(total)
    }


def get_ip_address():
    res = get('https://api.ipify.org/?format=json')
    return {
        'IP': res.get('ip')
    }


def get_mc_server_status(hostname):
    res = get(f'https://api.mcsrvstat.us/1/{hostname}')
    data = {
        'HOSTNAME': res['hostname'],
        'ONLINE': not res.get('offline', False),
        'PLAYERS': res.get('players')
    }
    if not data['PLAYERS']:
        data.pop('PLAYERS')
    return data


def get(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urlopen(req)
    encoding = res.info().get_param('charset') or 'utf-8'
    data = json.loads(res.read().decode(encoding))
    return data


def post(url, headers, data):
    req = Request(url, headers=headers, data=json.dumps(data).encode('utf-8') if data else None)
    urlopen(req)


def _get_bca_statements(browser, backdate_week):
    now = datetime.datetime.now() + datetime.timedelta(hours=7)
    end_date = now - datetime.timedelta(days=backdate_week * 7)
    start_date = end_date - datetime.timedelta(days=6)
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
        'r1': '1',
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
            date_parsed = datetime.datetime.strptime(f'{current_year}/{date}', '%Y/%d/%m')
            if date_parsed > now:
                date_parsed = datetime.datetime.strptime(f'{current_year - 1}/{date}', '%Y/%d/%m')
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

        # Attach to transactions
        transactions[date] = transactions.get(date, [])
        transactions[date].append([description, amount])

    return transactions


def _format_number(value):
    return int(value) if int(value) < 1000 else '{:,}'.format(int(value))
