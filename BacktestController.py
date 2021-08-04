# BacktestController.py
# This file controls all trading activities to do backtesting.

import datetime
import pprint
import queue
import time

from PerformanceDT import Performance
from EventBuilder import MarketEvent


class Backtest(object):

    def __init__(
            self,
            stock_data, symbol_list, order_list,signal_list, initial_capital, heartbeat, start_date,
            data_handler_cls, execution_handler_cls, portfolio_cls, strategy_cls
    ):

        self.stock_data = stock_data
        self.order_list = order_list
        self.symbol_list = symbol_list
        self.signal_list = signal_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat

        self.start_date = start_date

        self.data_handler_cls = data_handler_cls
        self.execution_handler_cls = execution_handler_cls
        self.portfolio_cls = portfolio_cls
        self.strategy_cls = strategy_cls

        self.events = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fills = 0
        # self.num_strats = 1

        self._generate_trading_instances()

    def _generate_trading_instances(self):

        print(
            "Creating DataHandler, StrategyFactory, Portfolio and Execution Objects/n")

        self.data_handler = self.data_handler_cls(self.events, self.stock_data, self.start_date, self.symbol_list)

        self.strategy = self.strategy_cls(self.data_handler, self.events, self.order_list,self.signal_list)

        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date,
                                            self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)

    def _reset_classes(self):
        self.strategy = self.strategy_cls(self.data_handler, self.events, self.order_list,self.signal_list)

        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date,
                                            self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)

    def _run_backtest(self):

        i = 0
        while True:  # The outer while loop is to control the feed of data
            i += 1
            print(i)

            if self.data_handler.continue_backtest:
                # self.data_handler.update_bars_monthly() # Feed data in a monthly space, create a market event at the end of each month.
                self.data_handler.update_bars()  # Feed data at the frequency of raw data.
                # self.strategy.calculate_stopping()  # Stopping loss
                self.portfolio.update_timeindex()  # Update all position and equity recordings

            else:
                break

            while True:  # The inner while loop is to control the event queue
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)

                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.process_signal(event)  # generate_smart_order
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.process_fill(event)

                if self.events.empty() and self.strategy.reading_orders == False:  # If events are all processed and a sold process finished
                    self.events.put(MarketEvent())

            time.sleep(self.heartbeat)

    def _output_performance(self):
        performance_inst = Performance(self.portfolio)

        print("Creating summary stats...")
        metrics = performance_inst.calculate_metrics()

        print("Creating equity curve...")
        print(performance_inst.equity_curve.tail(10))
        for output in metrics:
            print(output)

        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)
        performance_inst.equity_curve.to_csv('equity.csv')
        self.execution_handler.execution_records.to_csv('Execution_summary.csv')

    def run_trading(self):

        self._run_backtest()
        self._output_performance()
        curve_plot = Performance(self.portfolio)
        curve_plot.curve_plot()
