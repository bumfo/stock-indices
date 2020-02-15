import asyncio
import json
from datetime import datetime
from datetime import timedelta

from aiohttp import ClientSession

from secret import LIXINGER_TOKEN


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
    return json.loads(text)


async def get_indice(stockCodes=None, session=None):
    data_req = get_dict_with_token()
    if stockCodes is not None:
        data_req['stockCodes'] = stockCodes

    return await fetch_api('https://open.lixinger.com/api/a/indice', data_req, session=session)


async def get_indice_lazy(stockCodes=None, session=None):
    data = None
    store = 'data/a_indice.json'
    try:
        with open(store, 'r') as f:
            d = json.load(f)

            timestamp = datetime.fromisoformat(d['timestamp'])
            if datetime.utcnow() - timestamp > timedelta(days=14):
                raise Exception('too old')

            data = d['data']
    except Exception as ex:
        print('get_indice_lazy cache miss:', ex)
        data = await get_indice(stockCodes=stockCodes, session=session)

        with open(store, 'w') as f:
            json.dump({'data': data['data'], 'timestamp': datetime.utcnow().isoformat()}, f)

    return data


async def main():
    async with ClientSession() as session:
        print(await get_indice_lazy(session=session))


if __name__ == '__main__':
    asyncio.run(main())
