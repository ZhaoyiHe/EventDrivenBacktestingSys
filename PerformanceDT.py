# PerformanceDT.py
# This file conquers the measurement of the strategy, including metrics, and equity curve.

import numpy as np
import pandas as pd
import scipy.stats
import matplotlib.pyplot as plt
import datetime
from highcharts import Highstock


def calculate_VaR(returns):
    # Calculate the average and volatility
    avg = np.mean(returns)
    vol = np.std(returns)
    # Calculate the 0.99 VaR
    VaR = dict()
    VaR[r"95%_VaR"] = -(avg - 1.645 * vol)
    VaR[r"99%_VaR"] = -(avg - 2.326 * vol)
    return VaR


def calculate_sharpe_ratio(returns, window_size=252):
    return np.sqrt(window_size) * (np.mean(returns)) / np.std(returns)


def calculate_drawdowns(returns, window_size=None):
    # By using a rolling maximum
    roll_max = returns.cummax()
    # Calculate the drawdown by computing the falling ratio from the maximum return
    drawdown = 1 - returns / roll_max
    # maxDD = drawdown.rolling(window=window_size).max()
    maxDD = drawdown.max()
    return maxDD


def calculate_metrics(returns, cum_return):
    metrics = {}
    # total_return = self.equity_curve['equity_curve'][-1]
    metrics['total_return'] = "%f%%" % (100 * cum_return.iloc[-1] - 1)

    metrics['daily_return'] = "%f%%" % (100 * (cum_return.iloc[-1] - 1) / len(cum_return))  # Calculate average daily
    # return
    metrics['annual_return'] = "%f%%" % (100 * (cum_return.iloc[-1] - 1) / len(cum_return) * 252)
    # returns = self.equity_curve['returns']
    # pnl = self.equity_curve['equity_curve']

    metrics['sharpe_ratio'] = calculate_sharpe_ratio(returns)  # Calculate Sharpe ratio
    metrics['max_drawdown'] = "%f%%" % (100 * calculate_drawdowns(cum_return,window_size=len(cum_return))) # Calculate maximum drawdown
    metrics['volatility'] = np.std(returns)

    metrics[r"95%_VaR"] = calculate_VaR(returns)[r"95%_VaR"]
    metrics[r"99%_VaR"] = calculate_VaR(returns)[r"99%_VaR"]
    metrics_df = pd.DataFrame.from_dict(metrics, orient="index")
    return metrics_df


def calculate_corr(return_df1, return_df2):
    comb_df = pd.merge(return_df1.reset_index(), return_df2.reset_index(), how="inner", on="date").dropna().set_index(
        "date")
    coef, p = scipy.stats.pearsonr(comb_df.iloc[:, 0], comb_df.iloc[:, 1])
    return [coef]


class Benchmark:
    def __init__(self, symbol, date_range):
        self.symbol = symbol
        self.date_range = date_range
        self._load_data()
        self._calculate_return()

    def _load_data(self):
        if self.symbol == "CSI":
            csi_data = pd.read_csv('000800.csv')
            csi_data = csi_data.iloc[csi_data.date.to_list().index(self.date_range[0]):csi_data.date.to_list().index(
                self.date_range[1]), ]
            self.data = csi_data
        elif self.symbol == "SPX":
            spx_data = pd.read_csv('SPX.csv')
            spx_data.date = spx_data.date.apply(lambda x: datetime.datetime.strptime(x, "%Y/%m/%d"))
            spx_data = spx_data.set_index("date").sort_index().reset_index()
            spx_data.date = spx_data.date.apply(lambda x: datetime.datetime.strftime(x, "%Y-%m-%d"))
            spx_data = spx_data.iloc[spx_data.date.to_list().index(self.date_range[0]):spx_data.date.to_list().index(
                self.date_range[1]), ]
            self.data = spx_data

    def _calculate_return(self):
        self.data = self.data.set_index("date")
        self.returns = self.data.close.pct_change()
        self.cum_return = (1 + self.returns).cumprod()


class Performance:
    def __init__(self, portfolio_info):
        self.portfolio_info = portfolio_info
        self.equity_curve = self.create_equity_curve_dataframe()

        self.fig = plt.figure()
        self.fig.patch.set_facecolor('white')
        curve_matrix = self.equity_curve.reset_index()
        self.date_range = [curve_matrix.date.iloc[0], curve_matrix.date.iloc[-1]]
        self.csi = Benchmark("CSI", self.date_range)
        self.spx = Benchmark("SPX", self.date_range)


    def calculate_metrics(self):
        indi_metrics = dict()
        corr_metrics = dict()
        all_metrics = list()
        # VaR_metrics = dict()
        indi_metrics["Strategy"] = calculate_metrics(returns=self.equity_curve.returns,
                                                     cum_return=self.equity_curve.equity_curve)
        indi_metrics["CSI800"] = calculate_metrics(returns=self.csi.returns, cum_return=self.csi.cum_return)
        indi_metrics["SP500"] = calculate_metrics(returns=self.spx.returns, cum_return=self.spx.cum_return)
        all_metrics.append(pd.concat(indi_metrics, axis=1))

        corr_metrics["Strategy_CSI800"] = calculate_corr(self.equity_curve.returns, self.csi.returns)
        corr_metrics["Strategy_SP500"] = calculate_corr(self.equity_curve.returns, self.spx.returns)
        corr_metrics["CSI800_SP500"] = calculate_corr(self.csi.returns, self.spx.returns)
        all_metrics.append(pd.DataFrame.from_dict(corr_metrics))
        """
        VaR_metrics["Strategy"] = calculate_VaR(self.equity_curve.returns)
        VaR_metrics["CSI800"] = calculate_VaR(self.csi.returns)
        VaR_metrics["SP500"] = calculate_VaR(self.spx.returns)
        all_metrics.append(pd.concat(VaR_metrics))
        """
        return all_metrics


    def create_equity_curve_dataframe(self):
        curve = pd.DataFrame(self.portfolio_info.all_holdings)
        curve = curve.rename(columns={"datetime": "date"})
        curve.set_index('date', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (
                1.0 + curve['returns']).cumprod()  # Create a net value curve for the strategy trading history
  
        return curve.iloc[1:, ]

    def curve_plot(self):
        curve = self.equity_curve
        initial_cash = curve.cash.iloc[0]
        # curve = self.equity_curve.iloc[1:,]
        strategy_pnl = list(curve['equity_curve'].apply(lambda x: (x - 1) * initial_cash))
        date = list(curve.index.to_series().apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d')))
        strategy_pnl = list(zip(date, strategy_pnl))

        csi_pnl = self.csi.cum_return.apply(lambda x: (x - 1) * initial_cash).to_list()
        csi_pnl = list(zip(date, csi_pnl))

        spx_pnl = self.spx.cum_return.apply(lambda x: (x - 1) * initial_cash).to_list()
        spx_pnl = list(zip(date, spx_pnl))

        PnL = Highstock(width=1000, height=600)
        PnL.add_data_set(strategy_pnl, name="Strategy")
        PnL.add_data_set(csi_pnl, name="CSI800")
        PnL.add_data_set(spx_pnl, name="SP500")
        PnL.set_dict_options(

            {

                'chart': {
                    'renderTo': 'PnL'},
                'title': {
                    'text': 'Profit and Loss'},
                "plotOptions": {
                    "series": {"compare": "value"},
                },
                "legend": {
                    "layout": "vertical",
                    "align": 'right',
                    "verticalAlign": "middle",
                    "enabled": True},

            }
        )

        PnL.save_file("PnL")
