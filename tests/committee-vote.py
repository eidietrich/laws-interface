# Simple script to test vote scraper class by inspection
# Run as `python3 -m tests.committee-vote`

import json
from models.vote import Vote

vote = Vote({
    "url": "http://leg.mt.gov/bills/2021/minutes/house/votesheets/HB0701TAH210401.pdf",
    "bill": "HB 701",
    "action_id": "HB701-0027",
    "type": "committee"
},
    bill_needs_refresh=True,
    cache_base_path='cache/tests',
    use_verbose_logging=True)

print('## Vote data:')
print(json.dumps(vote.export(), indent=4))
