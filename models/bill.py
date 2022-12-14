import json
import re
import requests
from bs4 import BeautifulSoup
from os.path import exists

from models.bill_action import BillAction

from config import BASE_URL


class Bill:
    """
    Data structure for Montana Legislature bill


    """

    def __init__(self, input, use_cache=True, fetch_actions=True, use_verbose_logging=True):
        self.key = input['key']
        self.url = input['billPageUrl']
        self.use_cache = use_cache
        self.use_verbose_logging = use_verbose_logging
        self.fetch_actions = fetch_actions

        if use_verbose_logging:
            print('##', self.key)

        # Use input as starting point for building out bill data
        self.data = {
            'key': input['key'],
            'billPageUrl': input['billPageUrl'],
            'billTextUrl': input['billTextUrl'],
            'billPdfUrl': input['billPdfUrl'],
            'lc': input['lc'],
            'title': input['title'],
            'sponsor': input['sponsor'],
            'sponsorParty': input['sponsorParty'],
            'sponsorDistrict': input['sponsorDistrict'],
            'statusDate': input['statusDate'],
            'lastAction': input['lastAction'],
        }

        self.get_bill_page_data()

    def get_bill_page_data(self, write_cache=True):

        BILL_CACHE_PATH = f'cache-bills/{self.key}.html'
        if self.use_cache and exists(BILL_CACHE_PATH):
            if self.use_verbose_logging:
                print(f'- Fetching {self.key} data from html cache')
            with open(BILL_CACHE_PATH) as f:
                text = f.read()
        else:
            if self.use_verbose_logging:
                print(f'- Fetching {self.key} data from', self.url)
            r = requests.get(self.url)
            text = r.text
            if write_cache:
                if self.use_verbose_logging:
                    print(f'- {self.key} html written to cache',
                          BILL_CACHE_PATH)
                with open(BILL_CACHE_PATH, 'w') as f:
                    f.write(text)
        self.parse_bill_html(text)

    def parse_bill_html(self, text):
        """
        Parses bill page information

        """
        soup = BeautifulSoup(text, 'lxml')

        # Assume most high-level information has been picked up by bill list scraper
        # and will be more current from there

        bill_status_parent = soup.find(
            text="Current Bill Progress: ").find_parent('font')
        bill_status = [t for t in bill_status_parent][1].strip()
        self.data['billStatus'] = bill_status

        fiscal_notes_tag = soup.find(
            text="Fiscal Note(s)")
        if fiscal_notes_tag:
            fiscal_notes_link = fiscal_notes_tag.find_parent('a')['href']
        else:
            fiscal_notes_link = None
        self.data['fiscalNotesListUrl'] = fiscal_notes_link

        bill_amendments_tag = soup.find(
            text="Associated Amendments")
        if bill_amendments_tag:
            bill_amendments_link = bill_amendments_tag.find_parent('a')['href']
        else:
            bill_amendments_link = None
        self.data['amendmentListUrl'] = bill_amendments_link

        # Bill sponsors
        sponsor_table = soup.find(
            'a', {"name": "spon_table"}).find_parent().find('table')
        sponsor_table_data = {}
        for row in sponsor_table.find_all('tr')[1:]:
            cells = [td.text for td in row.find_all('td')]
            sponsor_table_data[cells[0]] = " ".join(
                [cells[2], cells[1]]).replace('&nbsp', '').strip()
        self.data['draftRequestor'] = sponsor_table_data.get('Requestor')
        self.data['billRequestor'] = sponsor_table_data.get('By Request Of')
        self.data['primarySponsor'] = sponsor_table_data.get('Primary Sponsor')

        # Bill subjects
        subject_table = soup.find(
            'a', {"name": "subj_table"}).find_parent().find('table')
        subjects = []
        for row in subject_table.find_all('tr')[1:]:
            cells = [td.text for td in row.find_all('td')]
            subjects.append({
                'subject': cells[0],
                'fiscalCode': cells[1].replace('&nbsp', ''),
                'voteReq': cells[2],
            })
        self.data['subjects'] = subjects
        self.data['voteRequirements'] = list(
            set([s['voteReq'] for s in subjects]))

        additional_bill_info_table = soup.find(
            'a', {"name": "abi_table"}).find_parent().find('table')

        def search_table(label):
            return additional_bill_info_table.find(
                text=label).find_parent('td').find_next_sibling().text
        deadline_category = search_table("Category:")
        transmittal_deadline = search_table("Transmittal Date:")
        amended_return_deadline = search_table(
            "Return (with 2nd house amendments) Date:")
        self.data['deadlineCategory'] = deadline_category
        self.data['transmittalDeadline'] = transmittal_deadline
        self.data['amendedReturnDeadline'] = amended_return_deadline

        # print(json.dumps(self.data, indent=4))

        actions_table = soup.find(
            'a', {"name": "ba_table"}).find_parent().find('table')

        if self.fetch_actions:
            self.actions = [BillAction(
                tr=tr,
                bill_key=self.key,
                action_key=i,
                skip_remote_vote_fetch=self.use_cache,
                use_verbose_logging=self.use_verbose_logging,
            )
                for i, tr in enumerate(actions_table.find_all('tr')[1:][::-1])]

    def export_actions(self):
        if self.fetch_actions:
            return [a.export() for a in self.actions]
        else:
            return []

    def export_votes(self):
        if self.fetch_actions:
            return [a.get_vote().export() for a in self.actions if a.get_vote()]
        else:
            return []

    def export(self):
        # Exports bill data sans-actions, which we're dealing with separately
        return self.data
