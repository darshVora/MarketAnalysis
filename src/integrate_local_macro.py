import pandas as pd
import numpy as np
import os

def integrate_macro():
    cpi_path = r"d:\Project\MarketAnalysis\src\Data\Macro\Consumer Price Index - Annual Variation.xlsx"
    gdp_path = r"d:\Project\MarketAnalysis\src\Data\Macro\Quarterly Estimates of Gross Domestic Product (At Constant Prices) New Series (Base _ 2011-12).xlsx"
    macro_path = r"d:\Project\MarketAnalysis\src\Data\macro_data.csv"
    
    print("Parsing CPI Excel File...")
    # 1. Parse CPI
    df_cpi = pd.read_excel(cpi_path, header=None)
    # The months are on row index 5 (6th row), starting col 4
    months = df_cpi.iloc[5, 4:16].tolist()
    # The data starts at row index 7 (8th row)
    cpi_data = df_cpi.iloc[7:].copy()
    cpi_data = cpi_data.iloc[:, [3] + list(range(4, 16))]
    cpi_data.columns = ['Year'] + months
    cpi_data['Year'] = cpi_data['Year'].ffill()
    # Remove rows where Year is not like 2011-12
    cpi_data = cpi_data[cpi_data['Year'].astype(str).str.contains('-')]
    
    # Melt to long format
    cpi_long = cpi_data.melt(id_vars=['Year'], var_name='Month', value_name='CPI_YoY')
    
    # Clean '-' values
    cpi_long['CPI_YoY'] = pd.to_numeric(cpi_long['CPI_YoY'], errors='coerce')
    cpi_long.dropna(subset=['CPI_YoY'], inplace=True)
    
    # Create Date
    # Year is '2011-12'. If Month is APR to DEC, year is 2011. If JAN to MAR, year is 2012.
    def parse_cpi_date(row):
        year_start = int(str(row['Year']).split('-')[0])
        month_str = str(row['Month']).strip().replace('.', '').upper()
        # map month to number
        month_map = {'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6, 'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10, 'NOV':11, 'DEC':12}
        m = month_map.get(month_str, 1)
        y = year_start if m >= 4 else year_start + 1
        return pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthEnd(0)
        
    cpi_long['date'] = cpi_long.apply(parse_cpi_date, axis=1)
    cpi_long = cpi_long[['date', 'CPI_YoY']].sort_values('date')
    
    print("Parsing GDP Excel File...")
    # 2. Parse GDP
    df_gdp = pd.read_excel(gdp_path, header=None)
    # Target column 1 (Year), 2 (Quarter), 11 (GDP)
    gdp_data = df_gdp.iloc[6:, [1, 2, 11]].copy()
    gdp_data.columns = ['Year', 'Quarter', 'GDP']
    gdp_data['Year'] = gdp_data['Year'].ffill()
    gdp_data.dropna(subset=['Quarter', 'GDP'], inplace=True)
    gdp_data = gdp_data[gdp_data['Quarter'].astype(str).str.startswith('Q')]
    
    def parse_gdp_date(row):
        year_start = int(str(row['Year']).split('-')[0])
        q = str(row['Quarter']).upper().strip()
        # Q1 in India financial year is Apr-Jun, ends Jun 30
        if q == 'Q1': return pd.Timestamp(year=year_start, month=6, day=30)
        elif q == 'Q2': return pd.Timestamp(year=year_start, month=9, day=30)
        elif q == 'Q3': return pd.Timestamp(year=year_start, month=12, day=31)
        elif q == 'Q4': return pd.Timestamp(year=year_start+1, month=3, day=31)
        return None
        
    gdp_data['date'] = gdp_data.apply(parse_gdp_date, axis=1)
    gdp_data = gdp_data[['date', 'GDP']].sort_values('date')
    gdp_data['GDP'] = pd.to_numeric(gdp_data['GDP'], errors='coerce')
    
    # Calculate GDP YoY Growth
    gdp_data['GDP_YoY'] = gdp_data['GDP'].pct_change(periods=4) * 100
    
    print("Merging features into macro_data.csv using backward alignment...")
    # 3. Merge with macro_data.csv
    macro_df = pd.read_csv(macro_path)
    macro_df['date'] = pd.to_datetime(macro_df['date'])
    macro_df = macro_df.sort_values('date')
    
    # Use merge_asof to forward-fill CPI and GDP to the daily dates
    macro_df = pd.merge_asof(macro_df, cpi_long, on='date', direction='backward')
    macro_df = pd.merge_asof(macro_df, gdp_data[['date', 'GDP_YoY']], on='date', direction='backward')
    
    macro_df.to_csv(macro_path, index=False)
    
    print("Integration complete!")
    print(macro_df[['date', 'CPI_YoY', 'GDP_YoY']].tail(10))

if __name__ == "__main__":
    integrate_macro()
