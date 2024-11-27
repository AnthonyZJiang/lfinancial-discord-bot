import time
from datetime import datetime
import os
from logging import getLogger

import pandas as pd
import yfinance as yf
import mplfinance as mpf


class FinanceToolkit:
    
    def __init__(self):
        self.stocks: dict[str, yf.Ticker] = {}
        if not os.path.exists('.temp'):
            os.makedirs('.temp')
        self.logger = getLogger('lfbot.FinanceToolkit')
        
    def get_stock(self, stock_symbol: str):
        if stock_symbol in self.stocks:
            stock = self.stocks[stock_symbol]
        stock = yf.Ticker(stock_symbol)
        self.stocks[stock_symbol] = stock
        stock.downloaded_data = {
            'last_day_bar': {'time': 0, 'bar': None},
            'intraday_bars': {'time': 0, 'bars': None}
        }
        return stock
    
    def download_stock_last_day_bar(self, stock_symbol: str, allowed_cache_time=1) -> pd.DataFrame:
        stock = self.get_stock(stock_symbol)
        if stock.downloaded_data['last_day_bar']['bar'] is None or time.time() - stock.downloaded_data['last_day_bar']['time'] > allowed_cache_time:
            try:
                data = stock.history(period='1d', interval='1d',prepost=True)
                if data is None or data.empty:
                    self.logger.error(f'Failed to download last day bar for {stock_symbol}. Data is {'None' if data is None else 'empty'}')
                    return None
                stock.downloaded_data['last_day_bar']['bar'] = data
            except Exception:
                self.logger.error(f'Exception occurred. Failed to download last day bar for {stock_symbol}', exc_info=True)
                return None
            stock.downloaded_data['last_day_bar']['time'] = time.time()
            self.logger.info(f'Downloaded last day bar for {stock_symbol}')
        return stock.downloaded_data['last_day_bar']['bar']
    
    def download_stock_intraday_min_bars(self, stock_symbol: str, allowed_cache_time=1) -> pd.DataFrame:
        stock = self.get_stock(stock_symbol)
        if stock.downloaded_data['intraday_bars']['bars'] is None or time.time() - stock.downloaded_data['intraday_bars']['time'] > allowed_cache_time:
            start = int(time.time() - 10*3600)
            try:
                data = stock.history(period='1d', interval='5m',prepost=True, start=start)
                if data is None or data.empty:
                    self.logger.error(f'Failed to download intraday min bars for {stock_symbol}. Data is {'None' if data is None else 'empty'}')
                    return None
                stock.downloaded_data['intraday_bars']['bars'] = data
            except Exception:
                self.logger.error(f'Exception occurred. Failed to download intraday min bars for {stock_symbol}', exc_info=True)
                return None
            stock.downloaded_data['intraday_bars']['time'] = time.time()
            self.logger.info(f'Downloaded intraday min bars for {stock_symbol}')
        return stock.downloaded_data['intraday_bars']['bars']
    
    def get_stock_last_price(self, stock_symbol: str) -> float:
        data = self.download_stock_last_day_bar(stock_symbol)
        if data is None:
            self.logger.error(f'Couldn not get last price for {stock_symbol}.')
            return None
        return data.iloc[-1]['Close']
    
    def get_stock_intraday_chart(self, stock_symbol: str) -> tuple[str, float]:
        data = self.download_stock_intraday_min_bars(stock_symbol)
        if data is None:
            self.logger.error(f'Couldn not generate intraday chart for {stock_symbol}.')
            return None, None
        filename = f'.temp/generated_{stock_symbol}_{datetime.strftime(data.iloc[-1].name, '%Y%M%d%H%m%S')}.png'
        mpf.plot(data, type='candle', style='yahoo', savefig=filename, volume=True, tight_layout=True)
        self.logger.info(f'Generated intraday chart for {stock_symbol}')
        return filename, data.iloc[-1]['Close']
