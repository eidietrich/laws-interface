# import json
import requests
import re
from bs4 import BeautifulSoup
from datetime import date
from os.path import exists, join


from functions import write_json, read_json

from models.bill import Bill

from config import BASE_URL, CACHE_BASE_PATH, OUTPUT_BASE_PATH

BILL_LIST_HTML_CACHE_PATH = join(CACHE_BASE_PATH, 'all-introduced-bills.html')
BILL_DATA_CACHE = join(CACHE_BASE_PATH, 'last-scrape-bill-data.json')

LAST_SCRAPE_BILLS_PATH = join(OUTPUT_BASE_PATH, 'all-bills.json')
LAST_SCRAPE_ACTIONS_PATH = join(OUTPUT_BASE_PATH, 'all-bill-actions.json')
LAST_SCRAPE_VOTES_PATH = join(OUTPUT_BASE_PATH, 'all-votes.json')

TODAY = date.today().strftime('%m/%d/%Y')


class BillList:
    """Data structure for gathering list of bills from LAWS system

    Cache Logic: Import bills where either bill page "Status Date" or "Status" don't match cached version
        OR where the date of the last status update is today.

    """

    def __init__(self, url,
                 use_html_bill_list_cache=False,
                 use_verbose_logging=False):
        bill_list = self.get_bill_list(url, use_cache=use_html_bill_list_cache)
        self.use_verbose_logging = use_verbose_logging

        if exists(BILL_DATA_CACHE):
            self.last_scrape_bills = read_json(BILL_DATA_CACHE)
        else:
            if use_verbose_logging:
                print('No bill data cache found at', BILL_DATA_CACHE)
            self.last_scrape_bills = []

        self.bills = []
        for raw in bill_list:
            matches = [
                last for last in self.last_scrape_bills if last['key'] == raw['key']
            ]
            needs_refresh = len(matches) == 0 \
                or (raw['statusDate'] != matches[0]['statusDate']) \
                or (raw['lastAction'] != matches[0]['lastAction']) \
                or (raw['statusDate'] == TODAY)
            bill = Bill(raw,
                        needs_refresh=needs_refresh,
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
        bill_list = []
        action_list = []
        vote_list = []
        for bill in self.bills:

            bill_data = bill.export()
            write_json(bill_data, join(
                OUTPUT_BASE_PATH, f'{bill.urlKey}--data.json'), log=False)
            bill_list += bill_data

            actions = bill.export_actions()
            write_json(actions, join(
                OUTPUT_BASE_PATH, f'{bill.urlKey}--actions.json'), log=False)
            action_list += actions

            votes = bill.export_votes()
            vote_list += votes
            write_json(actions, join(
                OUTPUT_BASE_PATH, f'{bill.urlKey}--votes.json'), log=False)

        # Write combined files
        write_json(bill_list, 'all-bills.json')
        write_json(action_list, 'all-bill-actions.json')
        write_json(vote_list, 'all-votes.json')
