import math
import pandas as pd
import yfinance as yf
from stock import Stock

class Portfolio:
    """
    Class for portfolio.
    """
    MAX = 0.5
    MIN = 0.05

    def __init__(self, stock_tickers: list, cash: int = 100000.0) -> None:
        """Method for initialising portfolio object.

        tickers: A list of selected tickers for the portfolio
        cash: Initial amount of cash
        """
        # stock tickers
        self.stock_tickers = stock_tickers
        # stocks' closing price history
        self.price_history = None

        # cash
        self.cash = cash

        # portfolio's worth
        self.worth = 0.0
        # portfolio's worth history for plotting
        self.worth_history = {}

        # trade history
        self.trades = {}
        # current positions
        self.positions = {}

        # for simulation
        self.date = None

    def get_price_history(self, start_date: str | pd.Timestamp = '2017-01-01', end_date: str | pd.Timestamp = '2024-01-01') -> pd.DataFrame:
        """Method for getting the stocks' daily closing prices between the start and end dates.

        start_date: Start date in the form [YYYY-MM-DD]
        end_date: End date in the form [YYYY-MM-DD]
        """
        price_history = yf.download(self.stock_tickers, start=start_date, end=end_date)['Close']
        price_history = price_history.round(2)
        price_history.index = pd.to_datetime(price_history.index)

        return price_history
    
    def setup_equal_weight(self) -> None:
        """Method for initialising portfolio with equal weights.
        """
        per_stock_position = self.cash / len(self.stock_tickers)
        # print(per_stock_position)

        # for saving to trade history
        self.trades[self.date] = {}

        # opening positions
        for ticker in self.stock_tickers:
            # print(ticker)
            # getting stock's price
            price = self.price_history.loc[self.date][ticker]
            # print(price)
            # calculating stock's quantity
            quantity = math.floor(per_stock_position / price)
            # print(quantity)

            # opening and adding to current positions
            self.positions[ticker] = Stock(ticker=ticker, price=price, quantity=quantity)
            stock = self.positions[ticker]

            # updating
            self.cash -= stock.position
            self.cash = round(self.cash, 2)

            # save trade
            stock.trades[self.date] = (price, quantity)

            # saving to trade history
            self.trades[self.date][stock.ticker] = (stock.price, stock.quantity)

        self.update_worth()

    def setup_best_stock(self, ticker: str = 'NVDA') -> None:
        """Method for initialising portfolio with only best stock (NVDA).
        """

        # for saving to trade history
        self.trades[self.date] = {}

        # opening positions
        # getting stock's price
        price = self.price_history.loc[self.date]
        # print(price)
        # calculating stock's quantity
        quantity = math.floor(self.cash / price)
        # print(quantity)

        # opening and adding to current positions
        self.positions[ticker] = Stock(ticker=ticker, price=price, quantity=quantity)
        stock = self.positions[ticker]

        # updating
        self.cash -= stock.position
        self.cash = round(self.cash, 2)

        # save trade
        stock.trades[self.date] = (price, quantity)

        # saving to trade history
        self.trades[self.date][stock.ticker] = (stock.price, stock.quantity)

        self.update_worth()

    def setup_market(self, ticker: str = '^GSPC') -> None:
        """Method for initialising portfolio with only market (S&P 500).
        """

        # for saving to trade history
        self.trades[self.date] = {}

        # opening positions
        # getting stock's price
        price = self.price_history.loc[self.date]
        # print(price)
        # calculating stock's quantity
        quantity = math.floor(self.cash / price)
        # print(quantity)

        # opening and adding to current positions
        self.positions[ticker] = Stock(ticker=ticker, price=price, quantity=quantity)
        stock = self.positions[ticker]

        # updating
        self.cash -= stock.position
        self.cash = round(self.cash, 2)

        # save trade
        stock.trades[self.date] = (price, quantity)

        # saving to trade history
        self.trades[self.date][stock.ticker] = (stock.price, stock.quantity)

        self.update_worth()

    def update_worth(self) -> None:
        """Method for updating the worth of the portfolio.
        """
        data = {}

        worth = 0
        for ticker, stock in self.positions.items():
            worth += stock.position

        # updating
        self.worth = worth + self.cash
        self.worth = round(self.worth, 2)

        # saving
        data['worth'] = self.worth
        self.worth_history[self.date] = data

    def update_prices(self) -> None:
        """Method for updating the prices of the portfolio's stocks and everything related.
        """
        if len(self.positions.keys()) > 1:
            for ticker, stock in self.positions.items():
                # getting new price
                new_price = self.price_history.loc[self.date][ticker]
                # updating price
                stock.update_price(new_price=new_price)
        else:
            for ticker, stock in self.positions.items():
                # getting new price
                new_price = self.price_history.loc[self.date]
                # updating price
                stock.update_price(new_price=new_price)
        
        # updating worth
        self.update_worth()

    def buy_stock(self, stock: Stock) -> None:
        """Method for buying stocks and updating everything related.

        stock: Stock
        """
        # check if cash available
        if self.cash >= stock.price:
            # max quantity for 50% weight
            max = math.floor((self.worth * Portfolio.MAX) / stock.price)

            # amount of new quantity
            bought_quantity = math.floor(self.cash / stock.price)

            # check
            if bought_quantity + stock.quantity > max:
                # adjust
                bought_quantity = max - stock.quantity
                total_quantity = bought_quantity + stock.quantity
            else:
                # total quantity
                total_quantity = bought_quantity + stock.quantity

            # updates
            stock.update_quantity(new_quantity=total_quantity)
            self.cash -= stock.price * bought_quantity
            self.cash = round(self.cash, 2)
            
            # save trade
            stock.trades[self.date] = (stock.price, bought_quantity)

            # save to trade history
            if self.date in self.trades.keys():
                self.trades[self.date][stock.ticker] = (stock.price, bought_quantity)
            else:
                self.trades[self.date] = {}
                self.trades[self.date][stock.ticker] = (stock.price, bought_quantity)
        
        else:
            return

    def sell_stock(self, stock: Stock) -> None:
        """Method for selling stocks and updating everything related.

        stock: Stock
        """
        # calculating target quantity for 5% weight
        target_quantity = math.floor((self.worth * Portfolio.MIN) / stock.price)

        # check
        if target_quantity >= stock.quantity:
            return

        # calculating sold quantity
        sold_quantity = stock.quantity - target_quantity

        # updates
        stock.update_quantity(new_quantity=target_quantity)
        self.cash += stock.price * sold_quantity
        self.cash = round(self.cash, 2)

        # save trade
        stock.trades[self.date] = (stock.price, -sold_quantity)

        # save to trade history
        if self.date in self.trades.keys():
            self.trades[self.date][stock.ticker] = (stock.price, -sold_quantity)
        else:
            self.trades[self.date] = {}
            self.trades[self.date][stock.ticker] = (stock.price, -sold_quantity)

    def describe(self) -> None:
        """Method for printing out portfolio description. 
        """
        print(f"Current positions as of {self.date}")
        print("-" * 15)
        
        for ticker, stock in self.positions.items():
            print(f"Ticker: {ticker}")
            print(f"Price: {stock.price}")
            print(f"Quantity: {stock.quantity}")
            print(f"Weight: {stock.position / self.worth}")
            print("-" * 15)
        
        print(f"Cash: {self.cash}")
        print("-" * 15)
        print(f"Portfolio worth: {self.worth}")
        # print("=" * 25)

    def simulation(self) -> None:
        """Method for running a simulation from start to end date.
        """
        # for idx in range(4):
        for idx in range(len(self.price_history)):
            self.date = self.price_history.index[idx]

            if idx == 0:
                self.setup_equal_weight()
                self.update_worth()
                self.describe()

            else:
                self.update_prices()
 
                # trades (first sell then buy)
                # ...
                
                self.update_worth()
                self.describe()

