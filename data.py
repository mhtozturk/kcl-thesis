import requests
import pandas as pd
from bs4 import BeautifulSoup

class Data:
    """
    This class gathers, processes, and prepares SEC Filing data obtained via
    SEC EDGAR API.
    """
    AGENT = {'User-Agent': 'mehmet.ozturk@kcl.ac.uk'} # agent for accessing API

    def __init__(self, ticker: str) -> None:
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
        # accessing the txt file that contains all HTML source code for a filing
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
        # DEBUGGING: printing out file's name for easy access to source code
        name = form.find('filename').get_text(strip=True)
        print(f"Current filename:\t {name}")

    def process_annual(self, accession_number: str) -> dict:
        """Method for processing annual [10-K] filings.

        :param accession_number: Unique access number for each filing.
        :rtype: Dictionary.
        """

    def process_filings(self) -> None:
        """Master method for processing filings.
        """
        for idx in range(len(self.metadata)):
            if self.metadata.iloc[idx]['form'] == '10-Q':
                q = self.process_quarterly(self.metadata.iloc[idx]['accessionNumber'])
                self.data[self.metadata.iloc[idx]['reportDate']] = q


