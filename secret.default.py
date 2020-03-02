LIXINGER_TOKEN = 'XXX'
LIXINGER_METRICS = ['pe_ttm.weightedAvg']

INTERESTING_CODES = ['000016']


def MY_INDICATOR(x):
    return x[0]['pe_ttm']['weightedAvg']['latestVal']
