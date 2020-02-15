import asyncio
import json
from datetime import datetime
from datetime import timedelta

from aiohttp import ClientSession

from secret import LIXINGER_TOKEN, LIXINGER_METRICS, INTERESTING_CODES


def get_dict_with_token():
    return {'token': LIXINGER_TOKEN}


async def async_post(url: str, session: ClientSession, **kwargs) -> str:
    async with session.post(url, **kwargs) as resp:
        if resp.status == 200:
            return await resp.text()
        else:
            raise Exception('Http {}: {}'.format(resp.status, await resp.text()))


async def fetch_api(url, data, session):
    text = await async_post(url, session, json=data)
    d = json.loads(text)

    if d['code'] != 0:
        raise Exception('Invalid code: {}'.format(d))

    return d['data']


def get_cache(store, days=14):
    with open(store, 'r') as f:
        d = json.load(f)

        timestamp = datetime.fromisoformat(d['timestamp'])
        if datetime.utcnow() - timestamp > timedelta(days=days):
            raise Exception('too old')

        return d['data']


def write_cache(store, data):
    import os
    directory = os.path.dirname(store)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(store, 'w') as f:
        json.dump({'data': data, 'timestamp': datetime.utcnow().isoformat()}, f)


async def get_lazy(get_fn, store=None, session=None):
    try:
        data = get_cache(store)
    except Exception as ex:
        print(store, 'cache miss:', ex)
        data = await get_fn(session=session)

        write_cache(store, data)

    return data


async def get_indices(codes=None, session=None):
    data_req = get_dict_with_token()
    if codes is not None:
        data_req['stockCodes'] = codes

    return await fetch_api('https://open.lixinger.com/api/a/indice', data_req, session=session)


async def get_indices_lazy(session=None):
    async def get_fn(session=None):
        return await get_indices(codes=None, session=session)

    return await get_lazy(get_fn, store='data/a_indices.json', session=session)


async def get_indices_fundamental(codes, metrics, latest=True, session=None):
    data_req = get_dict_with_token()

    data_req['stockCodes'] = codes
    data_req['metrics'] = metrics

    if latest:
        data_req['date'] = 'latest'
        if len(codes) > 100:
            raise Exception('get_indices_fundamental: at most 100 allowed, {} passed', len(codes))
    else:
        data_req['startDate'] = '1900-01-01'
        if len(codes) != 1:
            raise Exception('get_indices_fundamental: at most 100 allowed in full mode, {} passed', len(codes))

    return await fetch_api('https://open.lixinger.com/api/a/indice/fundamental', data_req, session=session)


def indices_fundamental_store(code):
    return 'data/a_indices_fundamental/{}.json'.format(code)


async def get_indices_fundamental_lazy(codes, session=None):
    missing = []
    old = []

    ret = []

    for code in codes:
        try:
            data = get_cache(indices_fundamental_store(code), days=10)
            ret.append(data)
        except Exception as ex:
            print('indices_fundamental', code, 'cache miss:', ex)
            missing.append(code)

    for code in missing:
        data = await get_indices_fundamental([code], LIXINGER_METRICS, latest=False, session=session)
        write_cache(indices_fundamental_store(code), data)

        ret.append(data)

    return ret


def list_to_map(a, key):
    m = {}

    for d in a:
        m[d[key]] = d

    return m


async def main():
    async with ClientSession() as session:
        indices = await get_indices_lazy(session=session)

        code_info = list_to_map(indices, 'stockCode')

        for code in INTERESTING_CODES:
            print(code_info[code])

            d = await get_indices_fundamental_lazy([code], session=session)
            print(d[0][0])


if __name__ == '__main__':
    asyncio.run(main())
