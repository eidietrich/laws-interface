# Simple script to test vote scraper class by inspection
# Run as `python3 -m tests.committee-vote`

import json
from models.vote import Vote

vote = Vote(
    # {
    #     "url": "https://leg.mt.gov/bills/2023/minutes/house/votesheets/HB0027TRH230109.pdf",
    #     "bill": "HB 27",
    #     "action_id": "HB27-0001",
    #     "type": "committee"
    # },
    {
        "url": "http://leg.mt.gov/bills/2023/minutes/house/votesheets/SB0073STH230404.pdf",
        "bill": "SB 73",
        "action_id": "SB73-0027",
        "type": "committee"
    },

    bill_needs_refresh=True,
    cache_base_path='cache/tests',
    use_verbose_logging=True)

print('## Vote data:')
print(json.dumps(vote.export(), indent=4))
