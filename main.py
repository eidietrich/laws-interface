
import json
from config import BILL_LIST_URL

from models.bill_list import BillList
from models.bill import Bill
from models.vote import Vote

from functions import write_json, read_json


# bill_list = BillList(BILL_LIST_URL,
#                      use_html_bill_list_cache=True,
#                      use_verbose_logging=True)


raw_bills = read_json('output/all-bills.json')
bill_id = 'HB 102'
raw_bill = [bill for bill in raw_bills if bill['key'] == bill_id][0]

bill = Bill(raw_bill, use_verbose_logging=True)

# write_json(bill.export(), './raw/demo-bill.json')
# write_json(bill.export_actions(), './raw/demo-bill-actions.json')
# write_json(bill.export_votes(), './raw/demo-bill-votes.json')


# vote = Vote({
#     "url": "http://laws.leg.mt.gov/legprd/LAW0211W$BLAC.VoteTabulation?P_VOTE_SEQ=H1412&P_SESS=20211",
#     "bill": "HB 701",
#     "action_id": "HB701-0040",
#     "type": "floor"
# }, use_verbose_logging=True)


# vote = Vote({
#     "url": "http://leg.mt.gov/bills/2021/minutes/house/votesheets/HB0701TAH210401.pdf",
#     "bill": "HB 701",
#     "action_id": "HB701-0027",
#     "type": "committee"
# }, use_verbose_logging=True)
