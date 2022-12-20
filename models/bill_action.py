import json

from config import SESSION_ID, BASE_URL

from models.vote import Vote


class BillAction:
    """
    Data structure for bill action

    Some but not all actions have associated votes

    - bill_needs_refresh - flag for whether parent bill needs a data refresh in current scrape

    TODO - use bill_needs_refresh flag to be smarter about whether votes need to be fetched


    """

    def __init__(self, tr, bill_key, action_key, bill_needs_refresh=True, use_verbose_logging=False):
        self.bill_needs_refresh = bill_needs_refresh
        self.use_verbose_logging = use_verbose_logging

        bill_key_ns = bill_key.replace(' ', '')
        action_id = f'{bill_key_ns}-{action_key:04}'

        tds = tr.find_all('td')

        action_description = tds[0].text
        action_date = tds[1].text

        self.has_vote = (tds[2].text != '&nbsp') and (tds[3].text != '&nbsp')

        if self.has_vote:
            vote_count = {
                'Y': int(tds[2].text),
                'N': int(tds[3].text)
            }
            total_votes = vote_count['Y'] + vote_count['N']
            vote_url = tds[2].find('a').get(
                'href') if tds[2].find('a') else None

            if vote_url is None:
                # Guess at vote category based on number of votes
                if 'Veto Override' in action_description:
                    vote_type = 'veto override'
                elif (total_votes > 40):
                    vote_type = 'floor'
                else:
                    vote_type = 'committee'
            elif 'leg.mt.gov' in vote_url:
                # committee vote
                vote_type = 'committee'
            elif 'LAW0211W$BLAC' in vote_url:
                vote_type = 'floor'
                vote_url = BASE_URL + vote_url
            else:
                print('Error, bad vote sorting algorithm')

            self.vote = Vote({
                'url': vote_url,
                'bill': bill_key,
                'action_id': action_id,
                'action_description': action_description,
                'action_date': action_date,
                'type': vote_type,
                'bill_page_vote_count': vote_count,
            },
                bill_needs_refresh=self.bill_needs_refresh,
                use_verbose_logging=self.use_verbose_logging
            )
        else:
            self.vote = None

        committee = tds[4].text.replace(
            '&nbsp', '') if tds[4].text != '&nbsp' else None
        recordings = [a.get('href') for a in tds[4].find_all(
            'a') if a.get('href') is not None and 'sg001-harmony.sliq.net' in a.get('href')]

        self.data = {
            'id': action_id,
            'bill': bill_key,
            'session': SESSION_ID,
            'action': action_description,
            'actionUrl': tds[0].get('href'),
            'date': action_date,
            'hasVote': self.has_vote,
            # 'voteType': vote_type,
            # 'voteUrl': vote_url,
            # 'voteCount': vote_count,
            'committee': committee,
            'recordings': recordings,
        }

        # print(json.dumps(self.data, indent=4))

    def get_vote(self):
        return self.vote

    def export(self):
        return self.data
