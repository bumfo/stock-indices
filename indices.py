import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime, date
from datetime import timedelta
from typing import Union

from aiohttp import ClientSession

from secret import LIXINGER_TOKEN, LIXINGER_METRICS, INTERESTING_CODES, MY_INDICATOR


def eprint(*args):
    print(*args, file=sys.stderr)


def get_dict_with_token():
    return {'token': LIXINGER_TOKEN}


def data_date(s: str) -> date:
    return datetime.fromisoformat(s).date()


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

        return d['data'], timestamp


def write_cache(store, data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.utcnow()

    import os
    directory = os.path.dirname(store)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(store, 'w') as f:
        json.dump({'data': data, 'timestamp': timestamp.isoformat()}, f)


async def get_lazy(get_fn, store=None, session=None):
    try:
        data, _ = get_cache(store)
    except Exception as ex:
        eprint(store, 'cache miss:', ex)
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


async def get_indices_fundamental(codes, metrics, latest: Union[bool, date] = True, session=None):
    data_req = get_dict_with_token()

    data_req['stockCodes'] = codes
    data_req['metrics'] = metrics

    if latest:
        data_req['date'] = 'latest' if latest is True else latest.isoformat()
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
    now = datetime.utcnow()

    missing = []
    code_data = {}
    code_time = {}

    for code in codes:
        try:
            data, timestamp = get_cache(indices_fundamental_store(code), days=10)
            code_data[code] = data
            code_time[code] = timestamp
        except Exception as ex:
            eprint('indices_fundamental', code, 'cache miss:', ex)
            missing.append(code)

    for code in missing:
        data = await get_indices_fundamental([code], LIXINGER_METRICS, latest=False, session=session)
        sort_data(data, reverse=True)
        write_cache(indices_fundamental_store(code), data, timestamp=now)

        code_data[code] = data
        code_time[code] = now

    old_codes = []

    for code, t in code_time.items():
        if now - t > timedelta(hours=1):
            old_codes.append(code)

    if len(old_codes) > 0:
        update_data = []

        now_date = now.date()
        oldest = now_date

        outdated_codes = []

        for code in old_codes:
            data = code_data[code]
            if len(data) > 0:
                code_date = data_date(data[0]['date'])

                if code_date < now_date:
                    outdated_codes.append(code)

                if code_date < oldest:
                    oldest = code_date

        if len(outdated_codes) > 100:
            raise Exception('Up to 100 supported by get_indices_fundamental_lazy')

        if len(outdated_codes) > 0 and oldest < now_date:
            eprint("updating outdated codes:", outdated_codes)

            d = oldest + timedelta(days=1)
            while d < now_date:
                eprint('fetch', d)
                data = await get_indices_fundamental(outdated_codes, LIXINGER_METRICS, latest=d, session=session)
                update_data.extend(data)

                d += timedelta(days=1)

            eprint('fetch', 'latest')

            data = await get_indices_fundamental(outdated_codes, LIXINGER_METRICS, latest=True, session=session)
            update_data.extend(data)

            if len(update_data) > 0:
                # eprint(update_data)

                merge_data(code_data, update_data)

                for code in outdated_codes:
                    data = code_data[code]
                    write_cache(indices_fundamental_store(code), data, timestamp=now)

    ret = []
    for code in codes:
        ret.append(code_data[code])

    return ret


def sort_data(data: list, reverse=False):
    data.sort(key=lambda x: data_date(x['date']), reverse=reverse)


def merge_data(code_data, update_data):
    code_update = defaultdict(list)

    for d in update_data:
        code_update[d['stockCode']].append(d)

    for code, d in code_update.items():
        sort_data(d)

        data: list = code_data[code]
        data.reverse()

        first = data_date(d[0]['date'])

        while len(data) > 0 and data_date(data[-1]['date']) >= first:
            eprint('pop', code, data.pop()['date'])

        data.extend(d)

        data.reverse()


def list_to_map(a, key):
    m = {}

    for d in a:
        m[d[key]] = d

    return m


async def main():
    async with ClientSession() as session:
        indices = await get_indices_lazy(session=session)

        code_info = list_to_map(indices, 'stockCode')

        data = await get_indices_fundamental_lazy(INTERESTING_CODES, session=session)
        for code, d in zip(INTERESTING_CODES, data):
            info = code_info[code]
            print('{}\t{}\t{}\t{}'.format(info['stockCode'], info['name'], MY_INDICATOR(d), data_date(d[0]['date'])))


if __name__ == '__main__':
    asyncio.run(main())
