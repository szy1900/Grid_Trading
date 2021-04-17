# -*- coding: utf-8 -*-

# portfolio.py


import pandas as pd
from abc import abstractmethod
from performance import create_sharpe_ratio, create_drawdowns


class Portfolio(object):
    def __init__(self, start_date, symbol_list=['601318'], initial_capital=100000):
        self.start_date = start_date
        self.initial_capital = initial_capital
        self.symbol_list = symbol_list
        self.current_positions = dict((k, v) for k, v in \
                                      [(s, 0) for s in self.symbol_list])
        self.all_positions = self.__construct_all_positions()

        self.current_holdings = self.__construct_current_holdings()
        self.all_holdings = self.__construct_all_holdings()

    def __construct_all_positions(self):
        """
        使用start_date来确定时间索引开始的日期来构造所有的持仓列表
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]

    def __construct_current_holdings(self):
        """
        这个函数构造一个字典，保存所有代码的资产组合的当前价值
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def __construct_all_holdings(self):
        """
        这个函数构造一个字典，保存所有的代码的资产组合的startdate的价值
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def update_positions_holdings_from_fill(self, latest_datetime, symbol, buy_or_sell, fill_price, quantity):
        """
        获取一个Fill对象并更新持仓价值矩阵来反映持仓市值
        """
        fill_dir = 0
        if buy_or_sell == 'BUY':
            fill_dir = 1
            if self.current_holdings['cash'] < fill_price * quantity:
                print('no so much money !')
                return {'date_time': latest_datetime, 'fill_dir': fill_dir, 'quantity': 0,
                        'fill_price': fill_price}

        if buy_or_sell == 'SELL':
            fill_dir = -1
            if self.current_positions[symbol] < quantity:
                print(f'{symbol} current positions is {self.current_positions[symbol]}, has been cleaned')
                commission = fill_price * self.current_positions[symbol] * 0.001
                self.current_holdings['cash'] -= (fill_dir * fill_price * self.current_positions[symbol] + commission)
                self.current_holdings[symbol] = 0
                sold_position = self.current_positions[symbol]
                self.current_positions[symbol] = 0
                self.current_holdings['commission'] += commission
                return {'date_time': latest_datetime, 'fill_dir': fill_dir, 'quantity': sold_position,
                        'fill_price': fill_price}

        self.current_positions[symbol] += fill_dir * quantity
        cost = fill_dir * fill_price * quantity
        commission_rate = 5
        if buy_or_sell == 'BUY':
            commission = abs(cost) * commission_rate / 10000
        else:
            commission = 0
        self.current_holdings[symbol] += cost
        # self.current_holdings[symbol] += fill_dir*quantity
        self.current_holdings['commission'] += commission
        self.current_holdings['cash'] -= (cost + commission)
        self.current_holdings['total'] = self.current_holdings['total'] - commission
        return {'date_time': latest_datetime, 'fill_dir': fill_dir, 'quantity': quantity,
                'fill_price': fill_price}

    def update_timeindex(self, latest_datetime, latest_price):
        """
        在持仓矩阵当中根据当前市场数据来增加一条新纪录，它反映了这个阶段所有持仓的市场价值
        """
        # latest_datetime = date
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        self.all_positions.append(dp)

        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            market_value = self.current_positions[s] * latest_price
            dh[s] = market_value
            dh['total'] += market_value
            self.current_holdings[s] = market_value
        self.current_holdings['total'] = dh['total']
        self.all_holdings.append(dh)

    '''新加的需要修改'''

    def create_equity_curve_dateframe(self):
        """
        基于all_holdings创建一个pandas的DataFrame。
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
        """
        Equity_summary
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100)),
                 ("Drawdown Duration", "%d" % dd_duration)]
        # self.equity_curve.to_csv('equity_cureves/equity.csv')
        return stats
