import numpy as np

import pandas as pd
import yfinance as yf

from tqdm import tqdm
from datetime import datetime, timedelta

import time
import os
import pandas_datareader as pdr



# TO BE UPDATED EVERY QUARTER OR HALF_YEARLY TO CHECK IF THE RANK OF INDUSTRIES IS SAME
# https://www.equitymaster.com/india-markets/nse-replica.asp?order=researchText.no_shares_act%20desc

company_names_yahoo_api = ['IOC.NS','ONGC.NS','ITC.NS','TATASTEEL.NS','NTPC.NS','POWERGRID.NS','SBIN.NS',
                           'HDFCBANK.NS','ICICIBANK.NS', 'RELIANCE.NS','COALINDIA.NS','BHARTIARTL.NS','WIPRO.NS',
                           'BPCL.NS','INFY.NS','TCS.NS','TATAMTRDVR.NS','AXISBANK.NS','HCLTECH.NS','JSWSTEEL.NS',
                           'SUNPHARMA.NS','HINDUNILVR.NS','HINDALCO.NS','ADANIPORTS.NS','HDFCLIFE.NS','KOTAKBANK.NS',
                           'BAJAJFINSV.NS','LT.NS','M&M.NS','ADANIENT.NS','SBILIFE.NS','TECHM.NS','NESTLEIND.NS','ASIANPAINT.NS',
                           'TATACONSUM.NS','TITAN.NS','CIPLA.NS','INDUSINDBK.NS','GRASIM.NS','BAJFINANCE.NS','SHRIRAMFIN.NS',
                           'MARUTI.NS','LTIM.NS','ULTRACEMCO.NS','BAJAJ-AUTO.NS','EICHERMOT.NS','DIVISLAB.NS','HEROMOTOCO.NS',
                           'DRREDDY.NS','APOLLOHOSP.NS',]



class DataRepository:
  ticker_df: pd.DataFrame
  indexes_df: pd.DataFrame
  # macro_df: pd.DataFrame 							NOT USING MACROS in the analysis

  start_date: str
  end_date: str
  
  ALL_TICKERS: list[str] = company_names_yahoo_api

  def __init__(self):
    self.ticker_df = None
    self.indexes_df = None
    # self.macro_df = None

  def _get_growth_df(self, df:pd.DataFrame, prefix:str)->pd.DataFrame:
    '''Help function to produce a df with growth columns'''
    for i in [1,3,7,30,90,180,365]: # adding the 180 days into the mix 
      df['growth_'+prefix+'_'+str(i)+'d'] = df['Adj Close'] / df['Adj Close'].shift(i)
      GROWTH_KEYS = [k for k in df.keys() if k.startswith('growth')]
    return df[GROWTH_KEYS]
    
  def fetch(self, start_date = None, end_date = None):
    '''Fetch all data from APIs'''

    print('Fetching Tickers info from YFinance')
    self.fetch_tickers(start_date=start_date, end_date = end_date)
    print('Fetching Indexes info from YFinance')
    self.fetch_indexes(start_date=start_date, end_date = end_date)
    # print('Fetching Macro info from FRED (Pandas_datareader)')
    # self.fetch_macro(min_date=min_date)
  
  def fetch_tickers(self, start_date=None, end_date = None):
    '''Fetch Tickers data from the Yfinance API'''
    if start_date is None:
      start_date = "2009-04-01" # April 1, 2009
    else:
      start_date = pd.to_datetime(start_date)   

    if end_date is None:
      end_date = "2024-03-31" # March 1, 2024
    else:
      end_date = pd.to_datetime(end_date)   
    
    print(f'Going download data for this tickers: {self.ALL_TICKERS[0:3]}')
    tq = tqdm(self.ALL_TICKERS)

    # DAILY OLHC data for the a set of tickers
    for i,ticker in enumerate(tq):
      tq.set_description(ticker)

      # Download stock prices from YFinance
      historyPrices = yf.download(tickers = ticker,
                          # period = "max",
                          start = start_date,
                          end = end_date,
                          interval = "1d")

      # generate features for historical prices, and what we want to predict
      historyPrices['Ticker'] = ticker
      historyPrices['Year']= historyPrices.index.year
      historyPrices['Month'] = historyPrices.index.month
      historyPrices['Weekday'] = historyPrices.index.weekday
      historyPrices['Date'] = historyPrices.index.date

      # historical returns
      for i in [1,3,7,30,90,180,365]: # adding the 180 days which is half yearly
        historyPrices['growth_'+str(i)+'d'] = historyPrices['Adj Close'] / historyPrices['Adj Close'].shift(i)
      historyPrices['growth_future_5d'] = historyPrices['Adj Close'].shift(-5) / historyPrices['Adj Close']

      # Technical indicators
      # SimpleMovingAverage 10 days and 20 days
      historyPrices['SMA10']= historyPrices['Close'].rolling(10).mean()
      historyPrices['SMA20']= historyPrices['Close'].rolling(20).mean()
      historyPrices['growing_moving_average'] = np.where(historyPrices['SMA10'] > historyPrices['SMA20'], 1, 0)
      historyPrices['high_minus_low_relative'] = (historyPrices.High - historyPrices.Low) / historyPrices['Adj Close']


      # 30d rolling volatility : https://ycharts.com/glossary/terms/rolling_vol_30
      historyPrices['volatility'] =   historyPrices['Adj Close'].rolling(30).std() * np.sqrt(252)

      # what we want to predict
      historyPrices['is_positive_growth_5d_future'] = np.where(historyPrices['growth_future_5d'] > 1, 1, 0)

      # sleep 1 sec between downloads - not to overload the API server
      time.sleep(1)


      if stocks_df.empty:
        stocks_df = historyPrices
      else:
        stocks_df = pd.concat([stocks_df, historyPrices], ignore_index=True)
      
  def fetch_indexes(self, start_date = None, end_date = None):
    '''Fetch Indexes data from the Yfinance API'''

    if start_date is None:
      start_date = "2009-04-01" # April 1, 2009
    else:
      start_date = pd.to_datetime(start_date)   

    if end_date is None:
      end_date = "2024-03-31" # March 1, 2024
    else:
      end_date = pd.to_datetime(end_date)   
    
    # https://finance.yahoo.com/quote/%5ENSEI/
    # NIFTY 50 Index
    nifty_50_df = yf.download(tickers = "^NSEI",
            start=start_date,
            end = end_date,
            interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)
    
    # OTHER INDICATORS

    # VIX - Volatility Index
    # https://finance.yahoo.com/quote/%5EVIX/
    vix = yf.download(tickers = "^VIX",
                      start = start_date,
                      end =end_date,
                      interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)


    # https://finance.yahoo.com/quote/%5EGSPC/
    # SNP - SNP Real Time Price. Currency in USD
    snp500_daily = yf.download(tickers = "^GSPC",
                      start = start_date,
                      end =end_date,
                     interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)

    # https://finance.yahoo.com/quote/%5EDJI?.tsrc=fin-srch
    # Dow Jones Industrial Average
    dji_daily = yf.download(tickers = "^DJI",
                      start = start_date,
                      end =end_date,
                     interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)

    # STXE 600 PR.EUR: https://finance.yahoo.com/quote/%5ESTOXX/
    stoxx600_daily = yf.download(tickers = "^STOXX",
                      start = start_date,
                      end =end_date,
                            interval = "1d")
    time.sleep(1)


    # OTHER ASSEST ( GOLD, CRUDE, BRENT, BTC)

    # GOLD
    # WEB: https://finance.yahoo.com/quote/GC%3DF
    gold = yf.download(tickers = "GC=F",
                      start = start_date,
                      end =end_date,
                      interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)
    
    # WTI Crude Oil
    # WEB: https://uk.finance.yahoo.com/quote/CL=F/
    crude_oil = yf.download(tickers = "CL=F",
                      start = start_date,
                      end =end_date,
                            interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)

    # Brent Oil
    # WEB: https://uk.finance.yahoo.com/quote/BZ=F/
    brent_oil = yf.download(tickers = "BZ=F",
                      start = start_date,
                      end =end_date,
                            interval = "1d")
        # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)

    # BITCOIN Prices
    # https://finance.yahoo.com/quote/BTC-USD/
    btc_usd =  yf.download(tickers = "BTC-USD",
                           start = start_date,
                          end =end_date,
                          interval = "1d")
    # sleep 1 sec between downloads - not to overload the API server
    time.sleep(1)
    
    # Prepare to merge
    nifty_50_to_merge = self.get_growth_df(nifty_50_df,'nifty')
    snp500_daily_to_merge = self._get_growth_df(snp500_daily, 'snp500')
    dji_daily_to_merge = self._get_growth_df(dji_daily, 'dji')
    vix_to_merge = vix.rename(columns={'Adj Close':'vix_adj_close'})[['vix_adj_close']]
    gold_to_merge = self._get_growth_df(gold, 'gold')
    crude_oil_to_merge = self._get_growth_df(crude_oil,'wti_oil')
    brent_oil_to_merge = self._get_growth_df(brent_oil,'brent_oil')
    btc_usd_to_merge = self._get_growth_df(btc_usd,'btc_usd')

    # Merging
    m2 = pd.merge(nifty_50_to_merge,
                  snp500_daily_to_merge,
                  how='left',
                  left_on='Date',
                  right_index=True,
                  validate = "many_to_one"
                  )
    
    m3 = pd.merge(m2,
                  dji_daily_to_merge,
                  left_index=True,
                  right_index=True,
                  how='left',
                  validate='one_to_one')
    
    m4 = pd.merge(m3,
                  vix_to_merge,
                  left_index=True,
                  right_index=True,
                  how='left',
                  validate='one_to_one')
    
    m5 = pd.merge(m4,
                  gold_to_merge,
                  left_index=True,
                  right_index=True,
                  how='left',
                  validate='one_to_one')
    
    m6 = pd.merge(m5,
                  crude_oil_to_merge,
                  left_index=True,
                  right_index=True,
                  how='left',
                  validate='one_to_one')
    
    m7 = pd.merge(m6,
                  brent_oil_to_merge,
                  left_index=True,
                  right_index=True,
                  how='left',
                  validate='one_to_one')    

    m8 = pd.merge(m7,
                  brent_oil_to_merge,
                  left_index=True,
                  right_index=True,
                  how='left',
                  validate='one_to_one')   

    self.indexes_df = m8  # a single df of all the indices and assets data


  def persist(self, data_dir:str):
    '''Save dataframes to files in a local directory 'dir' '''
    os.makedirs(data_dir, exist_ok=True)

    file_name = 'tickers_df.parquet'
    if os.path.exists(file_name):
      os.remove(file_name)
    self.ticker_df.to_parquet(os.path.join(data_dir,file_name), compression='brotli')
  
    file_name = 'indexes_df.parquet'
    if os.path.exists(file_name):
      os.remove(file_name)
    self.indexes_df.to_parquet(os.path.join(data_dir,file_name), compression='brotli')


  def load(self, data_dir:str):
    """Load files from the local directory"""
    self.ticker_df = pd.read_parquet(os.path.join(data_dir,'tickers_df.parquet'))
    self.indexes_df = pd.read_parquet(os.path.join(data_dir,'indexes_df.parquet'))