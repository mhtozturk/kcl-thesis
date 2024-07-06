import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

class Data:
    """
    This class gathers, processes, and prepares SEC Filing data obtained via
    SEC EDGAR API.
    """
    # CONSTANTS:
    # agent for accessing API
    AGENT = {'User-Agent': 'mehmet.ozturk@kcl.ac.uk'}
    # operations/income/earnings statement target terms
    OIE_TERMS = {
        'revenue': ['revenue', 'total revenue', 'net sale', 'total net sales'],
        'gross profit': ['gross profit', 'gross margin'],
        'operating income': ['operating income', 'income from operations', 'loss from operations'],
        'net income': ['net income', 'net income (loss)', 'net loss'],
        'eps': ['basic', 'basic earnings per share']
    }
    # regex's for formatting
    NEGATIVE_PATTERN = re.compile(r'[(),]')
    POSITIVE_PATTERN = re.compile(r',')

    def __init__(self, ticker: str):
        # used to obtain CIK (central index key)
        self.ticker = ticker
        # used to obtain metadata
        self.cik = None
        # used to store data
        self.data = {}
        # metadata
        self.metadata = None

    def get_cik(self, df: pd.DataFrame) -> None:
        """Method for getting the CIK of a company.

        :param df: DataFrame of CIKs obtained via <https://www.sec.gov/files/company_tickers.json>.
        """
        self.cik = df.loc[df['ticker'] == self.ticker, 'cik_str'].iat[0]

    def get_metadata(self) -> None:
        """Method for getting the SEC filings metadata of a company.
        """
        # API for the metadata of all filings
        metadata = requests.get(
            f'https://data.sec.gov/submissions/CIK{self.cik.zfill(10)}.json',
            headers = Data.AGENT
        )
        # request check
        if metadata.status_code == 200:
            print(f'Respone: [{metadata.status_code}], metadata obtained successfully.')
        else:
            print(f'Response: [{metadata.status_code}], couldn\'t obtain metadata.')
            return
        
        # filtering out all filings except 10-Q and 10-K
        self.metadata = pd.DataFrame.from_dict(metadata.json()['filings']['recent'])
        self.metadata = self.metadata[self.metadata['form'].isin(['10-K', '10-Q'])].reset_index(drop=True)
        self.metadata = self.metadata.sort_index(ascending=False).reset_index(drop=True)

        # storing only the last 25 for consistency as the source code of filings changed after 2015 
        self.metadata = self.metadata.tail(25)

    def process_quarterly(self, accession_number: str) -> dict:
        """Method for processing quarterly [10-Q] filings.

        :param accession_number: Unique access number for each filing.
        :rtype: Dictionary.
        """
        # accessing the [.txt] file that contains all HTML source code for a filing
        filing = requests.get(
            f'https://www.sec.gov/Archives/edgar/data/{self.cik}/{accession_number.replace("-", "")}/{accession_number}.txt',
            headers = Data.AGENT
        )
        # request check
        if filing.status_code == 200:
            print(f'Respone: [{filing.status_code}], filing obtained successfully.')
        else:
            print(f'Response: [{filing.status_code}], couldn\'t obtain filing.')
            return
        
        # initialising dictionary for storing data (features)
        data = {}

        # parsing filing with BeautifulSoup
        soup = BeautifulSoup(filing.content, 'lxml')
        # extracting [10-Q] form
        form = soup.find('document')
        # DEBUGGING: printing out file's name for easy access if needed
        name = form.filename.find(text = True, recursive = False).strip()
        print(f"Current filename:\t {name}")

        # splitting into seperate pages for easier parsing
        # <hr> tag is used consistently in filings for page breaks
        hr_breaks = form.find_all(lambda tag: tag.name == 'hr' and 'page-break-after:always' in tag.get('style', ''))
        # transforming into string objects for regex
        hr_breaks = [str(hr) for hr in hr_breaks]
        form_str = str(form)
        # creating regular expression for splitting pages
        hr_regex = '|'.join(map(re.escape, hr_breaks))
        
        form_pages = re.split(hr_regex, form_str)

        # getting numerical data
        for page in form_pages:
            page_soup = BeautifulSoup(page, 'html5lib')
            # operations/income/earnings statement (page)
            if ((page_soup.find(lambda tag: tag.name == 'div' and 'text-align:center' in tag.get('style', '') and 
                           any(term in tag.get_text(strip = True).lower() for term in ['income', 'operations', 'earnings'])
                           and 'comprehensive' not in tag.get_text(strip = True).lower() and tag.find('table') == None)) or 
                    (page_soup.find(lambda tag: tag.name == 'p' and 'text-align:center' in tag.get('style', '') and 
                           any(term in tag.get_text(strip = True).lower() for term in ['income', 'operations', 'earnings'])
                           and 'comprehensive' not in tag.get_text(strip = True).lower() and tag.find('table') == None))):
                # DEBUGGING
                print("Page found")

                # finding the table that shows the statement
                table = page_soup.find(lambda tag: tag.name == 'table' and 
                                  float(tag.get('style', '').split('width:')[1].split(';')[0].strip()[:-1]) > 99.5)
                # checking if a table is found
                if table == None:
                    continue
                # DEBUGGING
                print("Table found")
                
                # parsing through rows
                for row in table.find_all('tr'):
                    # getting elements in the row
                    cells = [td.get_text(strip = True).lower() for td in row.find_all('td') 
                             if td.get_text(strip = True) != '$' and td.get_text(strip = True) != '']
                    # at least 2 elements in a row
                    if len(cells) < 2:
                        continue
                    # DEBUGGING
                    # print('Row:', cells)
                    # keyword name
                    key = cells[0]

                    for term, variations in Data.OIE_TERMS.items():
                        if any(word in key for word in variations): 
                            if term not in data.keys():
                                try:
                                    # the value we are interested in for the term
                                    value = cells[1]
                                    # formatting vaue
                                    if '(' in value:
                                        value = -float(Data.NEGATIVE_PATTERN.sub('', value)) if '.' in value else int(Data.NEGATIVE_PATTERN.sub('', value))
                                        data[term] = value
                                    else:
                                        value = float(Data.POSITIVE_PATTERN.sub('', value)) if '.' in value else int(Data.POSITIVE_PATTERN.sub('', value))
                                        data[term] = value
                                except:
                                    data[term] = None

        return data

    def process_annual(self, accession_number: str) -> dict:
        """Method for processing annual [10-K] filings.

        :param accession_number: Unique access number for each filing.
        :rtype: Dictionary.
        """

    def process_filings(self) -> None:
        """Master method for processing filings.
        """
        # for idx in range(len(self.metadata)):
        for idx in range(2):
            if self.metadata.iloc[idx]['form'] == '10-Q':
                self.data[self.metadata.iloc[idx]['reportDate']] = self.process_quarterly(self.metadata.iloc[idx]['accessionNumber'])
            elif self.metadata.iloc[idx]['form'] == '10-K':
                continue


