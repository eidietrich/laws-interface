import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from PyPDF2 import PdfReader
import os


FLOOR_DATE_FORMAT = '%B %m, %Y'


class Vote:
    """Data structure for Montana Legislature vote

        Can be a committtee or floor vote.
    """

    def __init__(self, inputs,
                 use_cache=True,
                 skip_remote_vote_fetch=False,
                 use_verbose_logging=False):
        self.id = inputs['action_id']
        self.inputs = inputs
        self.use_cache = use_cache
        self.use_verbose_logging = use_verbose_logging
        self.skip_remote_vote_fetch = skip_remote_vote_fetch

        # if self.use_verbose_logging:
        #     print('### Vote', self.id)

        self.data = {
            'url': inputs['url'],
            'bill': inputs['bill'],
            'action_id': inputs['action_id'],
            'type': inputs['type'],
        }
        if (inputs['type'] == 'veto override'):
            self.parse_override_vote()
        if (inputs['type'] == 'floor'):
            self.parse_floor_vote(inputs['url'])
        if (inputs['type'] == 'committee'):
            self.parse_committee_vote(inputs['url'])

        # print(json.dumps(self.data, indent=4))

    def parse_floor_vote(self, url):
        """
        Parse HTML floor vote page,
        e.g. http://laws.leg.mt.gov/legprd/LAW0211W$BLAC.VoteTabulation?P_VOTE_SEQ=H2050&P_SESS=20211
        """
        CACHE_PATH = f'cache-votes/{self.id}.html'

        if os.path.exists(CACHE_PATH) and self.use_cache:
            if self.use_verbose_logging:
                print('--- Reading floor vote data from', CACHE_PATH)
            with open(CACHE_PATH, 'r') as f:
                text = f.read()
        elif self.use_cache and self.skip_remote_vote_fetch:
            # Skips effort to fetch uncached URL, saving time for broken vote links
            # Should trigger for bills that don't need an update
            print(f'--- Skipping floor data for ${self.id} from', url)
            self.data['error'] = 'Missing vote page'
        else:
            if self.use_verbose_logging:
                print(f'--- Fetching floor vote data for {self.id} from', url)
            response = requests.get(url)
            text = response.text
            if "No Vote Records Found for this Action." in text:
                # Missing vote page error. Label as error and move on
                self.data['error'] = 'Missing vote page'
                err = self.data['error']
                if self.use_verbose_logging:
                    print(f'*** {err} fetching {self.id}. URL:', url)
                return None

            # Write cache
            if self.use_verbose_logging:
                print('--- Writing floor vote data to cache', CACHE_PATH)
            with open(CACHE_PATH, 'w') as f:
                f.write(text)

        soup = BeautifulSoup(text, 'lxml')

        self.data['seq_number'] = re.search(
            r'(?<=VOTE_SEQ\=)(H|S)\d+', url).group(0)

        vote_date = soup.find(text=re.compile(
            "DATE:")).text.replace(r'DATE:', '').strip()
        self.data['date'] = vote_date

        vote_description = soup.find_all('p')[1].text.strip()
        self.data['description'] = vote_description

        total_table = soup.find(text="YEAS").find_parent('table')
        total_cells = total_table.find_all('tr')[1].find_all('td')

        self.data['totals'] = {
            'Y': int(total_cells[0].text),
            'N': int(total_cells[1].text),
            'E': int(total_cells[2].text),
            'A': int(total_cells[3].text),
        }

        vote_cells = soup.find_all('table')[2].find_all('td')
        votes_by_name = []
        for td in vote_cells:
            text = td.text
            if len(text.strip()) == 0:
                break
            votes_by_name.append({
                'name': re.search(r'(?<=^(Y|N|E|A)).+', text).group(0).strip(),
                'vote': re.search(r'^(Y|N|E|A)', text).group(0),
            })
        self.data['votes'] = votes_by_name

    def parse_committee_vote(self, url):
        """
        Parse PDF committee vote page,
        e.g. https://leg.mt.gov/bills/2021/minutes/house/votesheets/HB0701TAH210401.pdf
        """
        CACHE_PATH = f'cache-votes/{self.id}.pdf'

        self.data['seq_number'] = None  # Only for floor votes
        self.data['error'] = None

        if os.path.exists(CACHE_PATH) and self.use_cache:
            if self.use_verbose_logging:
                print('--- Reading committee vote data from cache', CACHE_PATH)
            # Read existing PDF below for either method
        elif url is not None:
            if self.use_verbose_logging:
                print('--- Fetching committee vote data from URL', url)
            response = requests.get(url)
            if response.status_code == '200':
                raw = response.content
                with open(CACHE_PATH, 'wb') as f:
                    f.write(raw)
            else:
                self.data['error'] = 'Missing PDF'
        else:
            self.data['error'] = 'Missing URL'

        if self.data['error'] is not None:
            # Terminate data parsing here and move on
            err = self.data['error']
            if self.use_verbose_logging:
                print(f'*** {err} fetching {self.id}. URL:', url)
            return None

        with open(CACHE_PATH, 'rb') as f:
            pdf = PdfReader(f)
            text = pdf.getPage(0).extractText()

            header_rows = re.search(
                r'(?s).+(?=\nYEAS \- \d+\s+ NAYS \- \d+)', text).group(0).split('\n')
            total_row = re.search(r'YEAS \- \d+\s+ NAYS \- \d+', text).group(0)
            vote_re = re.compile(r'(Y|N|E|A) .+')
            # vote_rows = text.split('\n')[len(header_rows)+1:]
            vote_rows = list(filter(vote_re.match, text.split('\n')))

            # Assuming header rows are consistent
            self.data['date'] = header_rows[1]
            self.data['description'] = header_rows[-1]

            self.data['totals'] = {
                'Y': int(re.search(r'(?<=YEAS \- )\d+', total_row).group(0)),
                'N': int(re.search(r'(?<=NAYS \- )\d+', total_row).group(0)),
            }

            votes_by_name = []
            for row in vote_rows:
                votes_by_name.append({
                    'name': re.search(r'(?<=^(Y|N|E|A)).+', row).group(0).strip()
                    .replace(' ', '').replace(',', ', ').replace(';byProxy', ''),
                    'vote': re.search(r'^(Y|N|E|A)', row).group(0),
                })
            self.data['votes'] = votes_by_name

    def parse_override_vote(self):
        self.data['seq_number'] = None  # Only for floor votes
        self.data['error'] = None
        self.data['date'] = self.inputs['action_date']
        self.data['description'] = self.inputs['action_description']
        self.data['totals'] = self.inputs['bill_page_vote_count']

    def check_vote_counts_match(self, totals, names, bill_page_totals):
        # TODO as possible data integrity check
        # OR relegate to a testing suite
        pass

    # def export_without_vote_detail(self):
    #     keys = self.data.keys()
    #     return {key: self.data[key] for key in keys if key != 'votes'}

    def export(self,):
        return self.data
