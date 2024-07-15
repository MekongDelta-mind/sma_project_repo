# sma_project_repo
```
The repo which contains all the artifacts used for capstone project for the course "Stock Market Analytics Zoomcamp 2024"
```
# Problem Statement

We want to create a portofolio of 10 stocks from the NIFTY 50 index list of stocks to maximize the profit. The aim is to get a return of atleast 14 % in Indian markets by investing in few stocks which would give a high growth to the invested corpus.

This is a mere analysis of shorts and can be extended to any period of time. 
The period choosen for the analysis is from 1st April, 2009( just after the financial crisis ) to 31st March,2024. 

It is assumed as if we have the data from 1st April, 2009 onwards upto <u>31st March,2023</u>. And since 1st april, 2023, we are investing $1200 in total in both SBI NIFTY 50 ETF (SYMBOL-> NSE:SETFNIF50 ) and the portfolio of stocks we would decide for next 12 months.
So we would be investing $100 in both ETF and our pre-analysed-portfolio(consisting of few stocks), every month , from 1st April,2023 to 31st March, 2024. At the end of the 1 year, that is 1st April,2024, we would compare the growth in investment between ETF and pre-analysed-portfolio: whether it beats the ETF or not or remains same.

The charges considered are as per the Zerodha's Equity delivery charges:

1. [a]Brokerage= 0
2. [b]STT/CTT = 0.1 %  on buy and sell
3. [c]Transaction CHarges( NSE )  = 0.00322%
4. [d]SEBI Charges = Rs.10 upto 1 crore
5. GST = 18% ( [a] + [b] + [d])


NOTE: 
1. We are only buy and hold would only sell after the 1 year, as to avoid the short term capital gain tax.
2. As we are going long on the stocks and ETF, holding it for almost 1 year, the trading simulation done would be very different than the way it was dicussed on the course. 

# folder and it's significance 

`scripts/data_repo.py` ---> get the data from the respective resources

`scripts/transform.py` ---> transforming the data to be suitable enough to be used for the modelling

`scripts/train.py` ---> training the data based on the best parameters


`script_test.ipynb` ---> Testing each script before using it in the main python file.


`main.py` ---> to be used for direct execution for cron jobs


# how to run the repo 