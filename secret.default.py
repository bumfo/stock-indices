LIXINGER_TOKEN = 'XXX'
LIXINGER_METRICS_LIST = ('pe_ttm.mcw',)

API_LIXINGER_INDEX = 'https://open.lixinger.com/api/{market_code}/index'
API_LIXINGER_INDEX_FUNDAMENTAL = 'https://open.lixinger.com/api/{market_code}/index/fundamental'


def _my_indicator(x):
    return x[0]['pe_ttm']['mcw']['cvpos']


MY_CODES = (
    {
        'market_code': 'a',
        'codes': ('000016',),
        'indicator': _my_indicator
    },
)
