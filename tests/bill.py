# Simple script to test bill scraper class by inspection

# Simple script to test vote scraper class by inspection
# Run as `python3 -m tests.bill`

import json

from functions import read_json

from models.bill import Bill

raw_bills = read_json('output/20211/all-bills.json')
bill_id = 'HB 102'
raw_bill = [bill for bill in raw_bills if bill['key'] == bill_id][0]
bill = Bill(raw_bill,
            bill_needs_refresh=True,
            cache_base_path='cache/tests',
            use_verbose_logging=True)

print('## Bill data:')
print(json.dumps(bill.export(), indent=4))
