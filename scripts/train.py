import pandas as pd
import numpy as np
import os
import joblib


from scripts.transform import TransformData

# ML models and utils
from sklearn.tree import DecisionTreeClassifier
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score
# from sklearn.metrics import precision_score


class TrainModel:
  transformed_df: pd.DataFrame #input dataframe from the Transformed piece 
  df_full: pd.DataFrame #full dataframe with DUMMIES

  # Dataframes for ML
  train_df:pd.DataFrame
  test_df: pd.DataFrame
  valid_df: pd.DataFrame
  train_valid_df:pd.DataFrame

  X_train:pd.DataFrame
  X_valid:pd.DataFrame
  X_test:pd.DataFrame
  X_train_valid:pd.DataFrame
  X_all:pd.DataFrame
  
  # feature sets
  GROWTH: list
  OHLCV: list
  CATEGORICAL: list
  TO_PREDICT: list
  TECHNICAL_INDICATORS: list 
  TECHNICAL_PATTERNS: list
  MACRO: list
  NUMERICAL: list
  CUSTOM_NUMERICAL: list
  DUMMIES: list


  def __init__(self, transformed:TransformData):
    ''' constructor to instanciate the class 
    transformed: takes the transformed object using the TransformData class
    '''
    # init transformed_df
    self.transformed_df = transformed.transformed_df.copy(deep=True)
    self.transformed_df['ln_volume'] = self.transformed_df.Volume.apply(lambda x: np.log(x) if x >0 else np.nan)
    # self.transformed_df['Date'] = pd.to_datetime(self.transformed_df['Date']).dt.strftime('%Y-%m-%d')
    
  def _define_feature_sets(self):
    self.GROWTH = [g for g in self.transformed_df if (g.find('growth_')==0)&(g.find('future')<0)]
    self.OHLCV = ['Open','High','Low','Close','Adj Close','Volume']
    self.CATEGORICAL = ['Month', 'Weekday', 'Ticker']
    self.TO_PREDICT = [g for g in self.transformed_df.keys() if (g.find('future')>=0)]
    self.CUSTOM_NUMERICAL = ['vix_adj_close','SMA10', 'SMA20', 'growing_moving_average', 'high_minus_low_relative','volatility', 'ln_volume']
    
    # artifacts from joins and/or unused original vars
    self.TO_DROP = ['Year','Date'] + self.CATEGORICAL + self.OHLCV
    
    self.NUMERICAL = self.GROWTH + self.CUSTOM_NUMERICAL
    
    # CHECK: NO OTHER INDICATORS LEFT
    self.OTHER = [k for k in self.transformed_df.keys() if k not in self.OHLCV + self.CATEGORICAL + self.NUMERICAL + self.TO_DROP + self.TO_PREDICT]
    return

  def _define_dummies(self):
    # dummy variables can't be generated from Date and numeric variables ==> convert to STRING (to define groups for Dummies)
    # self.transformed_df.loc[:,'Month'] = self.transformed_df.Month_x.dt.strftime('%B')
    self.transformed_df.loc[:,'Month'] = self.transformed_df.Month.astype(str)
    self.transformed_df['Weekday'] = self.transformed_df['Weekday'].astype(str)  

    # Generate dummy variables (no need for bool, let's have int32 instead)
    dummy_variables = pd.get_dummies(self.transformed_df[self.CATEGORICAL], dtype='int32')
    self.df_full = pd.concat([self.transformed_df, dummy_variables], axis=1)
    # get dummies names in a list
    self.DUMMIES = dummy_variables.keys().to_list()

  def _perform_temporal_split(self, df:pd.DataFrame, min_date_df, max_date_df, train_prop=0.7, val_prop=0.15, test_prop=0.15):
    """
    Splits a DataFrame into three buckets based on the temporal order of the 'Date' column.

    Args:
        df (DataFrame): The DataFrame to split.
        min_date_df (str or Timestamp): Minimum date in the DataFrame.
        max_date_df (str or Timestamp): Maximum date in the DataFrame.

    Returns:
        DataFrame: The input DataFrame with a new column 'split' indicating the split for each row.
    """

    # Calculate the training end date (end_date - 2 years)
    train_end = max_date_df - pd.DateOffset(years=2)

    # Calculate the validation end date (end_date - 1 year)
    val_end = max_date_df - pd.DateOffset(years=1)

    print(f'The training period is from {min_date_df} to {train_end} \n')
    print(f'The validtion period is from {train_end} to {val_end} \n')
    print(f'The test period is from {val_end} to {max_date_df} \n')

    # Assign split labels based on date ranges
    split_labels = []
    for date in df['Date']:
        if date <= train_end:
            split_labels.append('train')
        elif (date > train_end)  & (date <= val_end):
            split_labels.append('validation')
        else:
            split_labels.append('test')

    # Add 'split' column to the DataFrame
    df['split'] = split_labels

    return df


  def _define_dataframes_for_ML(self):

    features_list = self.NUMERICAL+ self.DUMMIES
    # What we're trying to predict?
    to_predict = 'is_positive_growth_5d_future'

    self.train_df = self.df_full[self.df_full.split.isin(['train'])].copy(deep=True)
    self.valid_df = self.df_full[self.df_full.split.isin(['validation'])].copy(deep=True)
    self.train_valid_df = self.df_full[self.df_full.split.isin(['train','validation'])].copy(deep=True)
    self.test_df =  self.df_full[self.df_full.split.isin(['test'])].copy(deep=True)

    # Separate numerical features and target variable for training and testing sets
    self.X_train = self.train_df[features_list+[to_predict]]
    self.X_valid = self.valid_df[features_list+[to_predict]]
    self.X_train_valid = self.train_valid_df[features_list+[to_predict]]
    self.X_test = self.test_df[features_list+[to_predict]]
    # this to be used for predictions and join to the original dataframe new_df
    self.X_all =  self.df_full[features_list+[to_predict]].copy(deep=True)

    # Clean from +-inf and NaNs:

    self.X_train = self._clean_dataframe_from_inf_and_nan(self.X_train)
    self.X_valid = self._clean_dataframe_from_inf_and_nan(self.X_valid)
    self.X_train_valid = self._clean_dataframe_from_inf_and_nan(self.X_train_valid)
    self.X_test = self._clean_dataframe_from_inf_and_nan(self.X_test)
    self.X_all = self._clean_dataframe_from_inf_and_nan(self.X_all)


    self.y_train = self.X_train[to_predict]
    self.y_valid = self.X_valid[to_predict]
    self.y_train_valid = self.X_train_valid[to_predict]
    self.y_test = self.X_test[to_predict]
    self.y_all =  self.X_all[to_predict]

    # remove y_train, y_test from X_ dataframes
    del self.X_train[to_predict]
    del self.X_valid[to_predict]
    del self.X_train_valid[to_predict]
    del self.X_test[to_predict]
    del self.X_all[to_predict]

    print(f'length: X_train {self.X_train.shape},  X_validation {self.X_valid.shape}, X_test {self.X_test.shape}')
    print(f'  X_train_valid = {self.X_train_valid.shape},  all combined: X_all {self.X_all.shape}')     

  def _clean_dataframe_from_inf_and_nan(self, df:pd.DataFrame):
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    return df   

  def prepare_dataframe(self):
    print("Prepare the dataframe: define feature sets, add dummies, temporal split")
    self._define_feature_sets()
    # get dummies and df_full
    self._define_dummies()
    
    # temporal split
    min_date_df = self.df_full.Date.min()
    max_date_df = self.df_full.Date.max()
    self._perform_temporal_split(self.df_full, min_date_df=min_date_df,max_date_df=max_date_df)

    # define dataframes for ML
    self._define_dataframes_for_ML()

    return
  
  # THIS SHOULD BE CHANGED TO train_decision_forest and the respective best parameters
  def train_model(self, max_depth=10):
    # https://scikit-learn.org/stable/modules/ensemble.html#random-forests-and-other-randomized-tree-ensembles
    print('Training the best model (DecisionTreeClassifier(max_depth=10, random_state=42))')
    self.model = DecisionTreeClassifier(max_depth=max_depth,
                               random_state=42)

    self.model = self.model.fit(self.X_train_valid, self.y_train_valid)

  def persist(self, data_dir:str):
    '''Save dataframes to files in a local directory 'dir' '''
    os.makedirs(data_dir, exist_ok=True)      

    # Save the model to a file
    model_filename = 'random_forest_model.joblib'
    path = os.path.join(data_dir,model_filename)
    joblib.dump(self.model, path)

  def load(self, data_dir:str):
    """Load files from the local directory"""
    os.makedirs(data_dir, exist_ok=True)   
    # Save the model to a file
    model_filename = 'random_forest_model.joblib'
    path = os.path.join(data_dir,model_filename)

    self.model  = joblib.load(path)

  def make_inference(self, pred_name:str):
    # https://scikit-learn.org/stable/modules/ensemble.html#random-forests-and-other-randomized-tree-ensembles
    print('Making inference')
    
    y_pred_all = self.model.predict_proba(self.X_all)
    y_pred_all_class1 = [k[1] for k in y_pred_all] #list of predictions for class "1"
    y_pred_all_class1_array = np.array(y_pred_all_class1) # (Numpy Array) np.array of predictions for class "1" , converted from a list

    self.df_full[pred_name] = y_pred_all_class1_array
    
    # define rank of the prediction
    self.df_full[f"{pred_name}_rank"] = self.df_full.groupby("Date")[pred_name].rank(method="first", ascending=False)