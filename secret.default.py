LIXINGER_TOKEN = 'XXX'
LIXINGER_METRICS_LIST = ('pe_ttm.mcw',)

API_LIXINGER_INDEX = 'https://open.lixinger.com/api/{market_code}/index'
API_LIXINGER_INDEX_FUNDAMENTAL = 'https://open.lixinger.com/api/{market_code}/index/fundamental'

INTERESTING_CODES = ('000016',)


def MY_INDICATOR(x):
    return x[0]['pe_ttm']['mcw']['cvpos']
