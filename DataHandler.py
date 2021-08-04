# DataHandler.py
# This file processes raw data to satisfy the requirement of other steps.
import datetime
from abc import ABCMeta, abstractmethod
import numpy as np

from EventBuilder import MarketEvent


class DataHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        raise NotImplementedError("Should implement get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        raise NotImplementedError("Should implement get_latest_bars_values()")

    @abstractmethod
    def update_bars(self):
        """
        Update bars into containers.
        """
        raise NotImplementedError("Should implement update_bars()")


class HistoricDataHandler(DataHandler):
    def __init__(self, events, stock_data, start_date, symbol_list):

        self.events = events
        self.stock_data = stock_data
        self.start_month = start_date.month
        self.start_date = start_date.strftime("%Y-%m-%d")
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.beginning_price = {}
        self.continue_backtest = True
        self.bar_index = 0
        self.data_generator = {}
        self.next_month_bar = {}
        self.latest_data_month = start_date.month

        self._open_and_convert_datafile()

    def _open_and_convert_datafile(self, symbol_list=None):

        if symbol_list is None:
            symbol_list = self.symbol_list

        comb_index = self.stock_data.set_index('datetime').index.unique()

        # Split dataframes for each stock
        for s in symbol_list:
            df_stock = self.stock_data[self.stock_data.symbol.isin([s])]
            self.symbol_data[s] = df_stock.set_index('datetime').sort_index()

        for s in symbol_list:
            # Initialization
            self.latest_symbol_data[s] = []
            self.next_month_bar[s] = []
            if len(self.symbol_data[s]) < len(comb_index):
                self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad')
            self.symbol_data[s] = self.symbol_data[s].fillna(0)

            self.symbol_data[s]["Pct_change"] = self.symbol_data[s].close.pct_change()
            self.symbol_data[s] = self.symbol_data[s].loc[self.start_date:]
            self.data_generator[s] = self.symbol_data[s].iterrows() # Create a generator

    def _reset_latest_data(self, symbol_list=None):
        if symbol_list is None:
            symbol_list = self.symbol_list
        for s in symbol_list:
            self.data_generator[s] = self.symbol_data[s].iterrows()
            self.latest_symbol_data[s] = []
            self.next_month_bar[s] = []

    def _get_new_bar(self, symbol):
        """
        Get the latest bar from the data set
        """
        for b in self.data_generator[symbol]:
            yield b

    def get_latest_bar(self, symbol):
        """
        Get the latest bar from latest symbol_data list.
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Get the latest N bars，if there is no so many bars ,return N-k bars
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Return corresponding Python datetime of the latest bar
        """

        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type="close"):
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That Symbol is not available in the historical data")
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type="close", N=1):
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That Symbol is not available in the historical data")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    def update_bars(self):
        """
        Update bars into latest_symbol_data.
        """

        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)

        self.events.put(MarketEvent())

    def update_bars_monthly(self):
        """
            Update bars into latest_symbol_data monthly.
        """
        prev_month = self.latest_data_month
        flag = 0
        for s in self.symbol_list:

            if self.next_month_bar[s]:
                self.latest_symbol_data[s].append(self.next_month_bar[s]) # Record the first bar of each month
                self.beginning_price[s] = self.next_month_bar[s][1]['close']
                self.next_month_bar[s] = []
            else:
                try:
                    bar = next(self._get_new_bar(s))
                except StopIteration:
                    self.continue_backtest = False
                else:
                    if bar is not None:
                        cur_month = datetime.datetime.strptime(bar[0], "%Y-%m-%d").month
                        if cur_month != self.latest_data_month:
                            self.next_month_bar[s] = bar
                            flag = 1

                        elif cur_month == self.latest_data_month:
                            self.latest_symbol_data[s].append(bar)
                        prev_month = cur_month

        self.latest_data_month = prev_month
        if flag == 1:
            self.events.put(MarketEvent())
