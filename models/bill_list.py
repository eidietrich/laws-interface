# import json
import requests
import re
from bs4 import BeautifulSoup
from datetime import date
from os.path import exists


from functions import write_json, read_json

from models.bill import Bill

from config import BASE_URL

BILL_LIST_HTML_CACHE_PATH = 'cache-bills/all-introduced-bills.html'
RAW_BILL_PATH = 'raw/bills.json'

PRIOR_SCRAPE_DATA_PATH = 'cache-data/last-scrape-bills.json'

# BASE_URL = 'http://laws.leg.mt.gov/legprd/'

TODAY = date.today().strftime('%m/%d/%Y')


class BillList:
    """Data structure for gathering list of bills from LAWS system

    Cache Logic: Import bills where either bill page "Status Date" or "Status" don't match cached version
        OR where the date of the last status update is today.

    """

    def __init__(self, url,
                 fetch_bill_actions=True,
                 use_html_bill_list_cache=False,
                 use_verbose_logging=False):
        bill_list = self.get_bill_list(url, use_cache=use_html_bill_list_cache)
        self.use_verbose_logging = use_verbose_logging

        # write_json(raw_bills, RAW_BILL_PATH)

        if exists(PRIOR_SCRAPE_DATA_PATH):
            self.last_scrape_bills = read_json(PRIOR_SCRAPE_DATA_PATH)
        else:
            self.last_scrape_bills = []

        self.bills = []
        for raw in bill_list:
            matches = [
                last for last in self.last_scrape_bills if last['key'] == raw['key']
            ]
            can_use_cache = len(matches) > 0 \
                and (raw['statusDate'] == matches[0]['statusDate']) \
                and (raw['lastAction'] == matches[0]['lastAction']) \
                and (raw['statusDate'] != TODAY)
            bill = Bill(raw,
                        use_cache=can_use_cache,
                        fetch_actions=fetch_bill_actions,
                        use_verbose_logging=self.use_verbose_logging)
            self.bills.append(bill)

        self.export()

    def get_bill_list(self, list_url, use_cache=False, write_cache=True):
        if use_cache:
            print("Fetching bill list from cache", BILL_LIST_HTML_CACHE_PATH)
            with open(BILL_LIST_HTML_CACHE_PATH, 'r') as f:
                text = f.read()
                parsed = self.parse_bill_list_html(text)
                return parsed
        else:
            print("Fetching bill list from", list_url)
            r = requests.get(list_url)
            text = r.text
            if write_cache:
                print("Fetched bill list written to cache at",
                      BILL_LIST_HTML_CACHE_PATH)
                with open(BILL_LIST_HTML_CACHE_PATH, 'w') as f:
                    f.write(text)
            parsed = self.parse_bill_list_html(text)
            return parsed

    def parse_bill_list_html(self, text):
        """
        Returns bill list as raw dicts
        """
        TEXT_BEFORE_TABLE = 'Total number of Introduced and Unintroduced Bills'

        soup = BeautifulSoup(text, 'html.parser')
        table_title = soup.find(text=re.compile(TEXT_BEFORE_TABLE))
        bill_table = table_title.find_next_sibling("table")
        rows = bill_table.find_all('tr')
        headers = [th.text for th in rows[0].find_all('th')]

        bills = [self.parse_bill_row(node, headers) for node in rows[1:]]
        return bills

    def parse_bill_row(self, node, keys):
        cells = [td.text for td in node.find_all('td')]
        links = node.find_all('a', href=True)
        bill_page_link = links[0]['href']
        bill_html_link = links[1]['href']
        bill_pdf_link = links[2]['href']
        raw = {}
        for i, key in enumerate(keys):
            raw[key] = cells[i]
        sponsor_raw = raw['Primary Sponsor'].replace('|', '')
        sponsor_district = re.search(r'(H|S)D \d+', sponsor_raw).group()
        sponsor_party = re.search(r'R|D(?=\) (H|S)D \d+)', sponsor_raw).group()
        sponsor_name = re.search(
            r'.+(?=\(R|D\) (H|S)D \d+)', sponsor_raw).group().strip().replace('  ', ' ')
        sponsor_name = re.sub(r'\($', '', sponsor_name).strip()
        bill = {
            'key': raw['Bill Type - Number'].replace('\u00a0', ''),
            'billPageUrl': "".join([BASE_URL, bill_page_link]),
            'billTextUrl': bill_html_link,
            'billPdfUrl': bill_pdf_link,
            'lc': raw['LC Number'],
            'title': raw['Short Title'],
            'sponsor': sponsor_name,
            'sponsorParty': sponsor_party,
            'sponsorDistrict': sponsor_district,
            'statusDate': raw['Status Date'],
            'lastAction': raw['Status'].replace('|', ''),
        }
        return bill

    def export(self):
        bill_list = [bill.export() for bill in self.bills]
        action_list = []
        vote_list = []
        for bill in self.bills:
            action_list += bill.export_actions()
            vote_list += bill.export_votes()

        write_json(bill_list, PRIOR_SCRAPE_DATA_PATH)
        write_json(bill_list, './raw/bills.json')
        write_json(action_list, './raw/actions.json')
        write_json(vote_list, './raw/votes.json')
