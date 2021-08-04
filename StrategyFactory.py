# StrategyFactory.py
# This file is a factory to create strategies, and generate signal event.

import datetime
import numpy as np
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod

from EventBuilder import SignalEvent


class Strategy(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def _generate_position_state(self):
        pass

    @abstractmethod
    def calculate_signals(self, event):
        raise NotImplementedError("Should implement calculate_signals()")

    @abstractmethod
    def calculate_stopping(self):
        pass


class Smartbeta(Strategy):
    def __init__(self, bars, events, order_list,signal_list):
        self.bars = bars
        self.events = events
        self.order_list = order_list
        self.signal_list = signal_list
        self.stopping_rate = 0.09
        #self.date_list = self.order_list.date.unique().tolist()
        #self.to_trade_list = self.order_list.iloc[:,:2]
        self.reading_orders = True
        self.symbol_list = self.bars.symbol_list
        self.bought = self._generate_position_state()
        signals = self.signal_list.reset_index()
        self.signal_date_list = signals.Date.to_list()

    def calculate_signals(self, event):
        if event.type == 'MARKET':
            if not self.reading_orders:
                for s in self.symbol_list:
                    date_cur = self.bars.get_latest_bar_datetime(s)
                   
                    if date_cur in self.signal_date_list:
                        if self.signal_list["signal"].loc[date_cur] ==0:
                            cur_price = self.bars.get_latest_bar_value(s)
                            dt = datetime.datetime.utcnow()

                            weight = 0

                            if not cur_price == 0:
                                signal = SignalEvent(datetime=date_cur, symbol=s,
                                                     timestamp=dt, order_price=cur_price, signal_type=None, weight=weight)
                                self.events.put(signal)
                        else:
                            # print(date_cur)
                            trading_days = self.order_list[s].date.tolist()
                            if date_cur in trading_days:
                                print(date_cur)
                                cur_price = self.bars.get_latest_bar_value(s)
                                dt = datetime.datetime.utcnow()
                                index = trading_days.index(date_cur)
                                weight = self.order_list[s].iloc[index, 2]
                                signal = SignalEvent(datetime=date_cur, symbol=s,
                                                     timestamp=dt, order_price=cur_price, signal_type=None,
                                                     weight=weight)
                                self.events.put(signal)
                            else:
                                self.reading_orders = False
                    else:
                        #print(date_cur)
                        trading_days = self.order_list[s].date.tolist()
                        if date_cur in trading_days:
                            print(date_cur)
                            cur_price = self.bars.get_latest_bar_value(s)
                            dt = datetime.datetime.utcnow()
                            index = trading_days.index(date_cur)
                            weight = self.order_list[s].iloc[index, 2]
                            signal = SignalEvent(datetime=date_cur, symbol=s,
                                                 timestamp=dt, order_price=cur_price, signal_type=None, weight=weight)
                            self.events.put(signal)
                        else:
                            self.reading_orders = False

                self.reading_orders = True

            else:
                self.reading_orders = False

