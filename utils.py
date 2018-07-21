import json
from urllib import request


def parse_message(message):
    if message.startswith('/'):
        message = message[1:].lower()
        args = [x for x in message.split(' ') if x]
        if args:
            command = args.pop(0)
            return command, args

    return None, []


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
