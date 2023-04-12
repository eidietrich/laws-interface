# Simple script to test bill scraper class by inspection

# Simple script to test vote scraper class by inspection
# Run as `python3 -m tests.bill`

import json

from functions import read_json

from models.bill import Bill

raw_bills = read_json('output/20231/all-bills.json')
bill_id = 'SB 73'
# bill_id = 'HB 1'
raw_bill = [bill for bill in raw_bills if bill['key'] == bill_id][0]
bill = Bill(raw_bill,
            needs_refresh=True,
            cache_base_path='cache/tests',
            use_verbose_logging=True)

print('## Bill data:')
# print(json.dumps(bill.export(), indent=4))
print(json.dumps(bill.export_actions(), indent=4))
# print(json.dumps(bill.export_votes(), indent=4))
