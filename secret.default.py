LIXINGER_TOKEN = 'XXX'
LIXINGER_METRICS_LIST = ('pe_ttm.weightedAvg',)

API_LIXINGER_INDEX = 'https://open.lixinger.com/api/a/index'
API_LIXINGER_INDEX_FUNDAMENTAL = 'https://open.lixinger.com/api/a/index/fundamental'

INTERESTING_CODES = ('000016',)


def MY_INDICATOR(x):
    return x[0]['pe_ttm']['weightedAvg']['latestVal']
