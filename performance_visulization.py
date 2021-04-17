from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from matplotlib.dates import date2num
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import copy


class plot_performance(object):
    def __init__(self, equity_curve, stock_curve, summary_recording):
        self.equity_data = equity_curve
        self.stock_data = stock_curve
        self.summary_recording = copy.deepcopy(summary_recording)
        # close_price = self.stock_data.loc[self.summary_recording['date_time'], :]['close']
        self.summary_recording.set_index('date_time', inplace=True)
        # self.summary_recording['close_price'] = close_price
        # self.fig = plt.figure()
        # self.fig.patch.set_facecolor('white')

    def plot_equity_curve(self):
        ax1 = self.fig.add_subplot(111, ylabel='Portfolio value: %')
        self.equity_data['equity_curve'].plot(ax=ax1, color='red', lw=2., rot=45)
        plt.grid(True)
        plt.show()

    def plot_stock_curve(self):
        self.fig = plt.figure()
        # self.fig.patch.set_facecolor('white')
        ax2 = self.fig.add_subplot(111, ylabel='Stock value: %')
        # self.stock_data['adj_close'].plot(ax=ax2, color='blue', lw=2.)
        ohlc = self.stock_data[['open', 'high', 'low', 'close']]
        ohlc = ohlc.reset_index().values
        date = date2num(ohlc[:, 0])
        ohlc[:, 0] = date
        # tem_date_num = date2num(le['date_time'])
        # le.loc[:,'date_time'] = tem_date_num
        le_y = self.summary_recording[self.summary_recording['fill_dir'] == 1]['fill_price']
        le_x = self.summary_recording[self.summary_recording['fill_dir'] == 1].index.to_list()
        le_x_value = date2num(le_x)
        le_y_value = le_y.values

        lexit_y = self.summary_recording[self.summary_recording['fill_dir'] == -1]['fill_price']
        lexit_x = self.summary_recording[self.summary_recording['fill_dir'] == -1].index.to_list()
        lexit_x_value = date2num(lexit_x)
        lexit_y_value = lexit_y.values
        # mpl.plot(ax2, ohlc, width=0.4, colorup='red', colordown='green')
        candlestick_ohlc(ax2, ohlc, width=0.4, colorup='red', colordown='green')
        for label in ax2.xaxis.get_ticklabels():
            label.set_rotation(45)
        ax2.plot(le_x_value, le_y_value, '^', color='lime', markersize=8,
                 label='long enter')
        for index in range(len(le_x_value)):
            plt.text(le_x_value[index], le_y_value[index], "Buy", ha='center', va='bottom', fontsize=8)

        ax2.plot(lexit_x_value, lexit_y_value, 'v', color='red', markersize=8,
                 label='Exit')
        for index in range(len(lexit_x_value)):
            plt.text(lexit_x_value[index], lexit_y_value[index], "Sell", ha='center', va='bottom', fontsize=8)
        # plt.text(lexit_x_value[0], lexit_y_value[0], "Sell", ha='center', va='bottom', fontsize=8)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mticker.MaxNLocator(10))

        plt.grid(True)
        plt.show()

    def show_all_plot(self):
        pass
