# Execution.py
# This file pricess order events and generate fill events by simulating an execution handler.
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod

from EventBuilder import FillEvent


class ExecutionHandler(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecutionHandler(ExecutionHandler):

    def __init__(self, events):
        self.commission = 0.003
        self.events = events
        self.execution_records = pd.DataFrame(columns=['datetime', 'symbol', 'direction', 'quantity', 'order_price'])

    def execute_order(self, event):
        if event.type == 'ORDER':
            fill_event = FillEvent(event.datetime,
                                   event.symbol,
                                   event.quantity, event.buy_or_sell, fill_cost=None, commission=self.commission)
            self.events.put(fill_event)
            self.execution_records = self.execution_records.append(
                pd.DataFrame(
                    {'datetime': [event.datetime], 'symbol': [event.symbol], 'direction': [event.direction],
                     'quantity': [event.quantity], 'order_price': [event.order_price]

                     }
                )
            )
