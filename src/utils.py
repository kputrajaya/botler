import datetime
import json
from urllib import request

from robobrowser import RoboBrowser
from robobrowser.forms.fields import Input


def parse_message(message):
    if message.startswith('/'):
        message = message[1:]
        args = [x for x in message.split(' ') if x]
        if args:
            command = args.pop(0).lower()
            return command, args

    return None, []


def get_bca_statements(username, password):
    browser = RoboBrowser(
        parser='html.parser',
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like '
                   'Mac OS X) AppleWebKit/604.1.38 (KHTML, like '
                   'Gecko) Version/11.0 Mobile/15A372 Safari/604.1')
    hostname = 'https://m.klikbca.com'
    now = datetime.datetime.now() + datetime.timedelta(hours=7)
    last_week = now - datetime.timedelta(days=6)
    start_d = last_week.strftime('%d')
    start_m = last_week.strftime('%m')
    start_y = last_week.strftime('%Y')
    end_d = now.strftime('%d')
    end_m = now.strftime('%m')
    end_y = now.strftime('%Y')

    try:
        # Login
        browser.open(f'{hostname}/login.jsp')
        form = browser.get_form(method='post')
        form['value(user_id)'].value = username
        form['value(pswd)'].value = password
        browser.submit_form(form)
        if 'accountstmt' not in browser.response.text:
            raise ValueError('Failed to login.')

        # Go to statements
        form = browser.get_form(method='post')
        form.action = 'accountstmt.do?value(actions)=acctstmtview'
        _add_form_data(form, {
            'r1': '1',
            'value(D1)': '0',
            'value(startDt)': start_d,
            'value(startMt)': start_m,
            'value(startYr)': start_y,
            'value(endDt)': end_d,
            'value(endMt)': end_m,
            'value(endYr)': end_y,
        })
        browser.submit_form(form)
        if 'IDR' not in browser.response.text:
            raise ValueError('Failed to get statements data.')

        # Get data tables
        tables = browser.select('table[cellpadding=3] table')
        if len(tables) != 3:
            raise ValueError('Statements data is in unexpected format.')

        # Parse transactions
        transaction_table = tables[1]
        transactions = []
        for transaction in transaction_table.select('tr')[1:]:
            cells = transaction.select('td')
            if len(cells) < 3:
                raise ValueError('Transaction data is in unexpected format.')

            date = cells[0].text.strip()
            contents = [
                x.strip()
                for x in cells[1].contents
                if x and isinstance(x, str) and x[0] not in ('<', '\n')]
            description = ' '.join(contents[:-2]) \
                .replace('KARTU DEBIT', '') \
                .replace('KARTU KREDIT', '') \
                .replace('BYR VIA E-BANKING', '') \
                .replace('TRSF E-BANKING DB', '') \
                .replace('KR OTOMATIS', '') \
                .replace('SWITCHING CR TRANSFER DR', '') \
                .replace(' - ', ' ') \
                .replace('  ', ' ') \
                .replace(date, '') \
                .strip()
            sign = '-' if cells[2].text == 'DB' else '+'
            amount = f'{sign} {contents[-1]}'
            transactions.append([date, description, amount])

        # Parse balance
        balance_table = tables[2]
        balance_row = balance_table.select('tr')[-1]
        balance = balance_row.select('td')[-1].text

        transactions.append(['NOW', 'BALANCE', f'+ {balance}'])
        return transactions
    finally:
        # Logout
        browser.open(f'{hostname}/authentication.do?value(actions)=logout')


def get_crypto_prices():
    res = get('https://indodax.com/api/btc_idr/webdata')
    data = {
        f'{k[:-3].upper()}/IDR': '{:,}'.format(int(v))
        for k, v in res['prices'].items()
        if k.endswith('idr')
    }
    return data


def get_ip_address():
    res = get('https://api.ipify.org/?format=json')
    return res


def get_mc_server_status(hostname):
    res = get(f'https://api.mcsrvstat.us/1/{hostname}')
    data = {
        'hostname': res['hostname'],
        'online': not res.get('offline', False),
        'players': res.get('players')
    }
    if data['players'] is None:
        data.pop('players')
    return data


def get(url):
    res = request.urlopen(url)
    encoding = res.info().get_param('charset') or 'utf-8'
    data = json.loads(res.read().decode(encoding))
    return data


def post(url, headers, data):
    req = request.Request(
        url,
        headers=headers,
        data=json.dumps(data).encode('utf-8') if data else None)
    request.urlopen(req)


def _add_form_data(form, data):
    for key, value in data.items():
        form.add_field(Input(f'<input name="{key}" value="{value}"/>'))
