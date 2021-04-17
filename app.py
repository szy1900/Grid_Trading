import tushare as ts
import pprint
import queue
import pandas as pd
import numpy as np
from data import HistoricDataHandler
from portfolio import Portfolio
from performance_visulization import plot_performance
if __name__ == '__main__':
    print('请去Tushare注册并更换Token的内容')
    ts.set_token('4563b71d2582929f061585a3b075a0bbca4a1ee1c6616259ef668fde')
    # pro = ts.pro_api()
    symbol_list = ['601318.SH']
    events = queue.Queue()
    inital_capital = 1000000
    start_date = '20180101'
    end_date = '20211231'
    my_portfolio = Portfolio(start_date=start_date, symbol_list=symbol_list,
                             initial_capital=inital_capital)
    base_line = None
    downgrid = None
    upgrid = None
    # upgrids=[]
    orders = []
    buy_sell_percent = 0.1
    data_handler = HistoricDataHandler(events, ts, symbol_list, start_date=start_date, end_date=end_date)
    i = 0
    while True:
        i += 1
        print(i)
        if data_handler.continue_backtest:
            data_handler.update_bars()  # Trigger a market event
        else:
            break
        while True:
            try:
                event = events.get(False)  ##Get an event from the Queue
            except queue.Empty:
                break
            else:
                if event is not None:
                    if event.type == 'MARKET':
                        for symbol in symbol_list:
                            data = data_handler.get_latest_bars(symbol, 100)
                            df_close = pd.DataFrame(
                                [{**{'trade_date': ele[0]}, **dict(ele[1])} for ele in data]).set_index('trade_date')
                            # {'index':data[0],data[1]}
                            ma = 10
                            df_close['ma_' + str(ma)] = df_close['close'].rolling(ma).mean()
                            df_close['std_' + str(ma)] = df_close['close'].rolling(ma).std()
                            df_close['ma-1std'] = df_close['ma_' + str(ma)] - df_close['std_' + str(ma)]
                            df_close['ma+1std'] = df_close['ma_' + str(ma)] + df_close['std_' + str(ma)]
                            df_show = df_close[['close', 'ma_' + str(ma), 'ma-1std', 'ma+1std']]
                            # if df_show.shape[0] == 100:
                            #     df_show.plot()
                            #     plt.show()
                            latest_data = df_show.tail(1).to_dict("records")[0]
                            date = pd.to_datetime(df_show.tail(1).index.values[0])
                            if latest_data['close'] < latest_data['ma-1std'] and my_portfolio.current_positions[
                                symbol_list[0]] == 0:
                                print(f"开始建仓 14%，初始建仓价格{latest_data['close']}")
                                quantity = np.floor(
                                    inital_capital * buy_sell_percent / latest_data['close'] / 100) * 100
                                filled_order = my_portfolio.update_positions_holdings_from_fill(date, symbol_list[0],
                                                                                                buy_or_sell='BUY',
                                                                                                fill_price=latest_data[
                                                                                                    'close'],
                                                                                                quantity=quantity)
                                orders.append(filled_order)
                                my_portfolio.current_positions['averaged_cost'] = latest_data['close']
                                print(f"{symbol_list[0]} 平均持仓成本: {latest_data['close']}")
                                print(f'买入的最新一单价格{base_line}')
                                base_line = orders[-1]['fill_price']
                                downgrid = base_line * 0.98
                                upgrid = base_line * 1.03

                                print('建仓完成')
                            elif not pd.isnull(base_line):
                                if latest_data['close'] < downgrid:
                                    print(f'当前触发条件{downgrid}')
                                    quantity = np.floor(
                                        inital_capital * buy_sell_percent / latest_data['close'] / 100) * 100
                                    filled_order = my_portfolio.update_positions_holdings_from_fill(date,
                                                                                                    symbol_list[0],
                                                                                                    buy_or_sell='BUY',
                                                                                                    fill_price=
                                                                                                    latest_data[
                                                                                                        'close'],
                                                                                                    quantity=quantity)
                                    orders.append(filled_order)

                                    # my_portfolio.update_timeindex(latest_datetime=date, latest_price=row['close'])
                                    if my_portfolio.current_positions[symbol_list[0]] > 0:
                                        total_position = 0
                                        costs_returns = 0
                                        for order in orders:
                                            total_position += order['quantity']
                                            costs_returns += order['quantity'] * order['fill_dir'] * order['fill_price']
                                        my_portfolio.current_positions['averaged_cost'] = costs_returns / total_position
                                        print(f"{symbol_list[0]} 平均持仓成本: {costs_returns / total_position}")
                                        print("更具新的持仓成本，重新规划网格！")
                                        base_line = orders[-1]['fill_price']
                                        downgrid = base_line * 0.97
                                        upgrid = base_line * 1.035
                                    print('加仓14%完成')
                                if latest_data['close'] > upgrid:
                                    print(f'当前触发条件{upgrid}')
                                    print(f"要卖了手上有{my_portfolio.current_positions[symbol_list[0]]}")
                                    quantity = np.floor(
                                        inital_capital * buy_sell_percent / latest_data['close'] / 100) * 100
                                    filled_order = my_portfolio.update_positions_holdings_from_fill(date,
                                                                                                    symbol_list[0],
                                                                                                    buy_or_sell='SELL',
                                                                                                    fill_price=
                                                                                                    latest_data[
                                                                                                        'close'],
                                                                                                    quantity=quantity)
                                    orders.append(filled_order)
                                    if my_portfolio.current_positions[symbol_list[0]] > 0:
                                        total_position = 0
                                        costs_returns = 0
                                        for order in orders:
                                            total_position += order['quantity']
                                            costs_returns += order['quantity'] * order['fill_dir'] * order['fill_price']
                                        print(f"{symbol_list[0]} 平均持仓成本: {costs_returns / total_position}")
                                        base_line = orders[-1]['fill_price']
                                        downgrid = base_line * 0.97
                                        upgrid = base_line * 1.035
                                    print('卖出14%完成')
                                my_portfolio.update_timeindex(latest_datetime=date, latest_price=latest_data['close'])

                            print('date completed')
                        # self.strategy.calculate_signals(event)  ## Trigger a Signal event #
                        # self.portfolio.update_timeindex()

                    # elif event.type == 'SIGNAL':
                    #     self.signals += 1
                    #     self.portfolio.update_signal(
                    #         event)  # Transfer Signal Event to order Event and trigger an order event
                    # elif event.type == 'ORDER':
                    #     self.orders += 1
                    #     self.execution_handler.execute_order(event)
                    # elif event.type == 'FILL':  # finish the order by updating the position. This is quite naive, further extention is required.
                    #     self.fills += 1
                    #     self.portfolio.update_fill(event)

        # time.sleep(self.heartbeat)
    # df_stock = pro.daily(ts_code='601318.SH', start_date='20180101', end_date='20210718')
    # df_stock = ts.pro_bar(ts_code=symbol_list[0], adj='qfq', start_date='20180101', end_date='20210718')
    # df_stock['trade_date'] = pd.to_datetime(df_stock['trade_date'], format="%Y%m%d")
    # df_close = df_stock[['trade_date', 'close']].sort_values(by=['trade_date'], ascending=True).reset_index().drop(
    #     ['index'], axis=1).set_index('trade_date')

    my_portfolio.create_equity_curve_dateframe()
    stats = my_portfolio.output_summary_stats()
    print("Creating summary stats...")
    pprint.pprint(stats)
    my_plot = plot_performance(my_portfolio.equity_curve,
                               data_handler.symbol_data[symbol_list[0]],
                               pd.DataFrame(orders))
    # my_plot.plot_equity_curve()
    my_plot.plot_stock_curve()
