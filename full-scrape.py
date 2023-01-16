
from config import BILL_LIST_URL

from models.bill_list import BillList

# Run scrape
bill_list = BillList(
    force_refresh=True,
    bill_list_url=BILL_LIST_URL,
    use_verbose_logging=True
)
bill_list.export()
