import pandas as pd

class Stock:
    """
    Class for stock inside portfolio.
    """

    def __init__(self, ticker: str, price: int = 0, quantity: int = 0) -> None:
        """Method for initialising stock object.

        ticker: Company's symbol
        price: Price
        quantity: Quantity in portfolio
        """
        # ticker
        self.ticker = ticker
        # In relation with portfolio
        # current price
        self.price = price
        # quantity
        self.quantity = quantity
        # position worth
        self.position = round(price * quantity, 2)

        # In relation with EDGAR
        # edgar for data
        self.edgar = None
        # filings dates
        self.filing_dates = None

        # trade history
        self.trades = {}

    def update_price(self, new_price: float) -> None:
        """Method for updating price and everything related.

        new_price: New price
        """
        self.price = new_price
        self.position = new_price * self.quantity

    def update_quantity(self, new_quantity: int) -> None:
        """Method for updating quantity and everything related.

        new_quantity: New quantity
        """
        self.quantity = new_quantity
        self.position = new_quantity * self.price

    def describe(self, date: pd.Timestamp | str) -> None:
        """Method for printing out stock description. 
        """
        if type(date) != str:
            date = date.strftime('%Y-%m-%d')
        
        print(f"{self.ticker} current position as of {date}")
        print("=" * 15)
        print(f"Price: {self.price}")
        print("-" * 10)
        print(f"Quantity: {self.quantity}")
        print("-" * 10)
        print(f"Position worth: {self.position}")
        print("=" * 15)