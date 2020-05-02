import asyncio
from pprint import pprint

from aiohttp import ClientSession

from indices import get_indices_lazy


async def main():
    async with ClientSession() as session:
        indices = await get_indices_lazy(market_code='a', session=session)

        pprint(sorted([(item['name'], item['stockCode']) for item in indices]))


if __name__ == '__main__':
    asyncio.run(main())
