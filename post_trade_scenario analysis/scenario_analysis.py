import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt


def calculate_drawdowns(portfolio_cum_return):
    # By using a rolling maximum
    roll_max = portfolio_cum_return.cummax()
    # Calculate the drawdown by computing the falling ratio from the maximum return
    drawdown = 1 - portfolio_cum_return / roll_max
    # maxDD = drawdown.rolling(window=window_size).max()
    # maxDD = drawdown.max()
    return drawdown


stock_data = pd.read_pickle('post_adjusted_price.pkl')
stock_data = stock_data.rename(columns={"datetime": "date", "symbol": "stock"})
stock_data.date = pd.to_datetime(stock_data.date)
stock_return = stock_data.set_index(["date", "stock"]).groupby(level=1).close.apply(lambda x: x.pct_change())
stock_return = stock_return.reset_index().set_index(["stock", "date"])
stock_dd = stock_data.set_index(["date", "stock"]).groupby(level=1).close.apply(
    lambda x: calculate_drawdowns((1 + x.pct_change()).cumprod()))
stock_dd = stock_dd.reset_index().set_index(["stock", "date"])

strategy_info = pd.read_csv('equity_curve.csv')
strategy_info = strategy_info.set_index("date")
strategy_return = strategy_info.returns
strategy_cum_return = strategy_info.equity_curve
strategy_drawdown = calculate_drawdowns(strategy_cum_return)

orders = pd.read_csv('all.csv', index_col=0)
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

csi_data = pd.read_csv('000800.csv')
csi_data.date = pd.to_datetime(csi_data.date)
csi_return = csi_data.set_index("date").close.pct_change()
csi_cum_return = (1 + csi_return).cumprod().dropna(
    axis=0)
csi_drawdown = calculate_drawdowns(csi_cum_return)

weights = strategy_info.apply(lambda x: x.apply(lambda y: y / (x.total - x.cash)), axis=1).iloc[:, :-5].dropna(
    axis=0)
weights_array = np.array(weights)
stocks = weights.columns.to_list()

if __name__ == "__main__":

    # rp_dict = dict()
    # ddp_dict = dict()

    rp_list = []
    ddp_list = []
    dates = weights.index.to_list()
    start_date = dates[0]

    for i in range(len(weights)):

        date = dates[i]
        print(date)
        stocks_index = np.where(weights_array[0] != 0)[0]
        weight_beta = 0
        weight_alpha = 0
        weight_epsilon = 0

        weight_beta_dd = 0
        weight_alpha_dd = 0
        weight_epsilon_dd = 0
        for j in stocks_index:
            stock = stocks[j]

            x = stock_return.loc[stock][start_date:date]
            ones = pd.DataFrame(np.ones(len(x)), index=x.index)
            x = pd.concat([ones, x], axis=1)
            y = csi_return[start_date:date]

            result = np.linalg.lstsq(x, y, rcond=None)

            x_dd = stock_dd.loc[stock][start_date:date]
            ones = pd.DataFrame(np.ones(len(x)), index=x_dd.index)
            x_dd = pd.concat([ones, x_dd], axis=1)
            y_dd = csi_drawdown[start_date:date]
            result_dd = np.linalg.lstsq(x, y, rcond=None)

            # single_dict = dict()
            # single_dict["alpha"] = result[0][0]
            # single_dict["beta"] = result[0][1]
            # single_dict["epsilon"] = result[1][0]
            # stock_coefs[stock] = single_dict

            stock_weight = weights.loc[date, stock]
            weight_alpha += stock_weight * result[0][0]
            weight_beta += stock_weight * result[0][1]
            if len(result[1]) != 0:
                weight_epsilon += stock_weight * result[1][0]

            weight_alpha_dd += stock_weight * result_dd[0][0]
            weight_beta_dd += stock_weight * result_dd[0][1]
            if len(result_dd[1]) != 0:
                weight_epsilon_dd += stock_weight * result_dd[1][0]

        rp_list.append([weight_alpha + weight_beta * (-0.05) + weight_epsilon,
                        weight_alpha + weight_beta * (-0.1) + weight_epsilon])

        ddp_list.append([weight_alpha_dd + weight_beta_dd * (-0.2) + weight_epsilon_dd,
                         weight_alpha_dd + weight_beta_dd * (-0.3) + weight_epsilon_dd,
                         weight_alpha_dd + weight_beta_dd * (-0.5) + weight_epsilon_dd])

    rp = pd.DataFrame(data=np.array(rp_list, dtype=object), index=dates, columns=["-0.05", "-0.1"]).iloc[0:-2,:]
    ddp = pd.DataFrame(data=np.array(ddp_list, dtype=object), index=dates, columns=["-0.2", "-0.3", "-0.5"]).iloc[0 :-2,:]
    print(rp)
    print(ddp)
    rp.plot(figsize=(12,6))
    plt.savefig("rp.jpg")

    ddp.plot(figsize=(12, 6))
    plt.savefig("ddp.jpg")
    rp.to_csv('scenario_analysis_rp.csv')
    ddp.to_csv('scenario_analysis_ddp.csv')
