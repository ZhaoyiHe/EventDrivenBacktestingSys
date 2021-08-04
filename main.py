import datetime
import time
import pandas as pd

from EventBuilder import OrderEvent
from DataHandler import HistoricDataHandler

from StrategyFactory import Smartbeta

from Execution import SimulatedExecutionHandler

from Portfolio import WeightstoPosition

from PerformanceDT import Performance
from BacktestController import Backtest

if __name__ == "__main__":
    start_time = time.process_time()
    # input price data and feed into data Handler
    stock_data = pd.read_pickle('post_adjusted_price.pkl')
    orders = pd.read_csv('all_orders_50.csv').iloc[:,-3:]
    signals = pd.read_csv('signal.csv')
    signal_data = signals.set_index("Date")

    for i in range(0, len(orders)):
        stock_symbol = orders.stock.iloc[i]
        tail = stock_symbol[-2:]
        # date_time = datetime.datetime.strptime(str(orders.date[i]), "%Y%m%d")
        # orders.iloc[i, 0] = datetime.datetime.strftime(date_time, "%Y-%m-%d")
        # spx[i, 0] =  datetime.datetime.strftime(date_time,"%Y-%m-%d")
        if tail == "SZ":
            orders.iloc[i, 1] = stock_symbol.replace('SZ', 'XSHE')
        elif tail == "SH":
            orders.iloc[i, 1] = stock_symbol.replace('SH', 'XSHG')

    stocks = stock_data.symbol.unique()

    order_data = {}
    for s in stocks:
        orderlist = orders[orders.stock.isin([s])]
        # print(orderlist)
        order_data[s] = orderlist.set_index('date').sort_index().reset_index()

    initial_capital = 100000000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2015, 1, 1, 0, 0, 0)

    backtest = Backtest(stock_data=stock_data, symbol_list=stocks, order_list=order_data,signal_list = signal_data,
                        initial_capital=initial_capital,
                        heartbeat=heartbeat, start_date=start_date,
                        data_handler_cls=HistoricDataHandler, execution_handler_cls=SimulatedExecutionHandler,
                        portfolio_cls=WeightstoPosition,
                        strategy_cls=Smartbeta)
    backtest.run_trading()

    end_time = time.process_time()
    print('Running time: %s Seconds' % (end_time - start_time))
