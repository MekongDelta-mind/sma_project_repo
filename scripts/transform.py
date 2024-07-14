import pandas as pd
from tqdm import tqdm

import os
from scripts.data_repo import DataRepository


class TransformData:
  tickers_df: pd.DataFrame
  transformed_df: pd.DataFrame

  def __init__(self, repo:DataRepository):
    # copy initial dfs from repo
    self.tickers_df = repo.ticker_df.copy(deep=True)
    self.macro_df = repo.macro_df.copy(deep=True)
    self.indexes_df = repo.indexes_df.copy(deep=True)
    
    # init transformed_df
    self.transformed_df = None
  
  def transform(self):
    '''Transform all dataframes from repo'''
    
    # Transform initial tickers_df to one with Tech indicators
    self._transform_tickers()

    # merge tickers (tech.indicators) with macro_df and indexes_df 
    # THERE IS NO MACRO DATA FOR THIS ANALYSIS
    # # there are no transformations related to the Macros so this method if acting as an Overlay
    self._merge_tickers_macro_indexes_df()

    # truncate all data before 2000
    self.transformed_df = self.transformed_df[self.transformed_df.Date>='2000-01-01']

  def _transform_tickers(self):
    '''Transform tickers dataframes from repo'''
    # not implemented
        # TaLib needs inputs of a datatype 'Double' 
    self.tickers_df['Volume'] = self.tickers_df['Volume']*1.0

    for key in ['Open','High','Low','Close','Volume','Adj Close']:
      self.tickers_df.loc[:,key] = self.tickers_df[key].astype('double')

    merged_df = None

    # supress warnings
    pd.options.mode.chained_assignment = None  # default='warn'

    # tickers = tqdm(self.tickers_df.Ticker.unique())

    merged_df = self.tickers_df 

    self.transformed_df = merged_df


  def _merge_tickers_macro_indexes_df(self):
    if self.transformed_df is None:
      return
    
    # assuming non-None transformed_df
    # self.macro_df['Date']= pd.to_datetime(self.macro_df['Date'], utc=True)
    self.indexes_df['Date']= pd.to_datetime(self.indexes_df.index, utc=True)
    
    # self.macro_df.set_index('Date', inplace=True)
    self.indexes_df.set_index('Date', inplace=True)

    self.transformed_df = pd.merge(self.transformed_df,
              self.indexes_df,
              how='left',
              left_on='Date',
              right_index=True,
              validate = "many_to_one"
              )
    
  def persist(self, data_dir:str):
    '''Save dataframes to files in a local directory 'dir' '''
    os.makedirs(data_dir, exist_ok=True)      

    file_name = 'transformed_df.parquet'
    if os.path.exists(file_name):
      os.remove(file_name)
    self.transformed_df.to_parquet(os.path.join(data_dir,file_name), compression='brotli')

  def load(self, data_dir:str):
    """Load files from the local directory"""
    os.makedirs(data_dir, exist_ok=True)      
    self.transformed_df  = pd.read_parquet(os.path.join(data_dir,'transformed_df.parquet'))
    