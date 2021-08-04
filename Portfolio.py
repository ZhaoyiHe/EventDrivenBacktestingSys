# Portfolio.py
# Portfolio class receive signal events, generates order events and deal with fill events. The way to
# generate order events varies on different strategies.

import math
import datetime

from abc import ABCMeta, abstractmethod

from EventBuilder import SignalEvent, OrderEvent


class Portfolio(object):
    """
    Portfolio class receive signal events, generates order events and deal with fill events.
    """

    def __init__(self, bars, events, start_date, initial_capital):

        self.bars = bars
        self.events = events

        self.symbol_list = self.bars.symbol_list
        self.latest_datetime = None
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self._construct_all_positions()
        self.current_positions = dict((k, v) for k, v in
                                      [(s, 0) for s in self.symbol_list])
        self.all_holdings = self._construct_all_holdings()
        self.current_holdings = self._construct_current_holdings()

    @abstractmethod
    def generate_order(self, signal):
        raise NotImplementedError("Should implement generate_order()")

    def process_signal(self, event):
        if event.type == 'SIGNAL':
            order_event = self.generate_order(event)
            self.events.put(order_event)

    # Record positions and holdings
    def _construct_all_positions(self):
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]

    def _construct_all_holdings(self):
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def _construct_current_holdings(self):
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self):

        self.latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        # self.latest_datetime = order.datetime
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = self.latest_datetime
        dp.update(self.current_positions)
        self.all_positions.append(dp)

        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = self.latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        for s in self.symbol_list:
            self.current_holdings[s] = self.current_positions[s] * self.bars.get_latest_bar_value(s)
            dh[s] = self.current_holdings[s]
            dh['total'] += self.current_holdings[s]
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill_event):
        fill_dir = 0
        if fill_event.buy_or_sell == 'BUY':
            fill_dir = 1
        if fill_event.buy_or_sell == 'SELL':
            fill_dir = -1
        self.current_positions[fill_event.symbol] += fill_dir * fill_event.quantity

    def update_holdings_from_fill(self, fill_event):
        fill_dir = 0
        if fill_event.buy_or_sell == 'BUY':
            fill_dir = 1
        if fill_event.buy_or_sell == 'SELL':
            fill_dir = -1

        fill_price = self.bars.get_latest_bar_value(fill_event.symbol)
        cost = fill_dir * fill_price * fill_event.quantity
        self.current_holdings[fill_event.symbol] += cost
        self.current_holdings['commission'] += fill_event.commission * fill_price * fill_event.quantity
        self.current_holdings['cash'] -= (cost + fill_event.commission * fill_price * fill_event.quantity)

    def process_fill(self, event):
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)


class WeightstoPosition(Portfolio):

    def generate_order(self, signal):

        symbol = signal.symbol
        datetime = signal.datetime
        weight = signal.weight
        order_price = signal.order_price
        order = None
        order_type = 'MKT'

        cur_position = self.current_positions[symbol]

        commission = 0.003
        # free_cash = self.current_holdings['cash']
        total_equity = self.current_holdings['total']
        """
                if cur_position < 1/10000:
            print("Stopping Loss")
            order = OrderEvent(datetime, symbol, order_type, 0, 'SELL', order_price,
                               direction="LONG")
            return order
        """
        
        mkt_quantity = math.floor((total_equity * weight) * (1 - commission) / order_price)
        # mkt_quantity = (total_equity * weight) * (1 - commission) / order_price
        if mkt_quantity > cur_position:

            direction = "LONG"

            order = OrderEvent(datetime, symbol, order_type, mkt_quantity - cur_position, 'BUY', order_price,
                               direction)
        elif mkt_quantity < cur_position:
            direction = "EXIT"

            order = OrderEvent(datetime, symbol, order_type, abs(cur_position - mkt_quantity), 'SELL', order_price,
                               direction)
        return order
