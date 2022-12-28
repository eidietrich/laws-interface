# Simple script to test vote scraper class by inspection
# Run as `python3 -m tests.floor-vote`
import json
from models.vote import Vote

vote = Vote({
    "url": "http://laws.leg.mt.gov/legprd/LAW0211W$BLAC.VoteTabulation?P_VOTE_SEQ=S204&P_SESS=20211",
    "bill": "HB 102",
    "action_id": "HB102-0038",
    "type": "floor"
},
    bill_needs_refresh=True,
    cache_base_path='cache/tests',
    use_verbose_logging=True)

print('## Vote data:')
print(json.dumps(vote.export(), indent=4))
