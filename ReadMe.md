# Event-driven back testing system

[TOC]

### Data Source 
Ricequant

## Development Target

1. avoid look-ahead bias, 
2. reuse, 
3. output trading records, metrics and net value curve.

 

## Components

- Queue Builder, 
- Data handler,
- Strategy factory, 
- Portfolio calculator, 
- Simulated executor, 
- Performance class, 
- Backtesting controller.
- Main

In the overall system, a queue of events is used to drive the system. Data handler provides market event, reminds later parts to retrieve data, strategy module triggered by a market event and generates the signal event. The portfolio module further processes the signal event into an order event; moreover, it processes the fill event generates by the executioner after dealing with the order event. Later on, the performance module conquers the measurement of the strategy, including metrics and equity curve.

 ### Data Handler

​	The data handler processes the original dataset into dictionaries of data frames using stock symbols as the key. The data handler provides interfaces for further operations such as returning one or more bars in turn, returning the latest dates, etc. It is also supporting to trigger the system by daily or monthly frequency.

 ### Strategy Factory

The strategy module getsthe current state, calculating order signals, and adding some stopping limits if needed. I created a smart beta class here to read some local order files and RMS signals, and generate signal events with date, stock symbol and weighting information.

 ### Portfolio

Functions can be split into two parts: signal events to order events and fill events to holding records. To process the fill events,  the positions and holdings are calculated by recording the cash, cost, and commission, calculated from the series of free cash, order price, and quantity. To be specific, I use backward split adjusted price here.

### Execution  

The execution module implemented the transform from order events to the fill events.

### Performance

The performance module is consists of five independent functions to calculate metrics such as annual return, Sharpe ratio, and maximum drawdown and the correlation between our strategy and the indexes. The benchmark class loads data of indexes and calculate its daily and cumulative returns.  And the Performance class aggregates functions above, receive the overall portfolio information, calculate the metrics and plot the equity curve. Here I use a package named highcharts to produce an interactive net value curve.

### Backtest controller

The backtest controller is the most central part of the overall project. It uses an outer loop to feed data and an inner loop to process the event queue, construct execution records. 

### Main

The main function inputs local data sets, and call the backtest function to fun the controller.

## Outputs
- equity.csv: portfolio information
- PnL.html: PnL curve
- Execution_summary: execution records
- metrics printed in the console
