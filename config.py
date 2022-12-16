from os.path import join

BASE_URL = 'http://laws.leg.mt.gov/legprd/'

SESSION_ID = '20211'  # 2021 regular session
# SESSION_ID = '20231' # 2023 regular session

BILL_LIST_URL = f'http://laws.leg.mt.gov/legprd/LAW0217W$BAIV.return_all_bills?P_SESS={SESSION_ID}'

CACHE_BASE_PATH = join('cache', SESSION_ID)
OUTPUT_BASE_PATH = join('output', SESSION_ID)
