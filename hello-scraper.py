# Adapted from https://github.com/palewire/first-github-scraper/blob/main/scrape.ipynb

import requests
import bs4
import csv

URL = 'http://www.dllr.state.md.us/employment/warn.shtml'
warn_page = requests.get(URL)
# soup = bs4.BeautifulSoup(warn_page.text, 'html.parser')
soup = bs4.BeautifulSoup(warn_page.text, 'lxml')


table = soup.find('table')
rows = table.find_all('tr')

HEADERS = [
    'warn_date',
    'naics_code',
    'biz',
    'address',
    'wia_code',
    'total_employees',
    'effective_date',
    'type_code'
]

with open('test-data.csv', 'w', newline='') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(HEADERS)
    for row in rows[1:]:
        cells = row.find_all('td')
        values = [c.text.strip() for c in cells]
        writer.writerow(values)
