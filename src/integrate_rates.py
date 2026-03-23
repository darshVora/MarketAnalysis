import pandas as pd
import numpy as np
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def integrate_rates():
    macro_path = os.path.join(_DATA_DIR, "macro_data.csv")
    yield_path = os.path.join(_DATA_DIR, "Macro", "Interest Rates on Central and State Government Dated Securities.xlsx")
    repo_path = os.path.join(_DATA_DIR, "Macro", "Major Monetary Policy Rates and Reserve Requirements - Bank Rate, LAF (Repo, Reverse Repo, SDF and MSF) Rates, CRR & SLR.xlsx")
    
    print("Reading macro_data.csv...")
    macro_df = pd.read_csv(macro_path)
    macro_df['date'] = pd.to_datetime(macro_df['date'])
    macro_df.sort_values('date', inplace=True)
    
    print("Parsing 10-Year Annual Yield Excel...")
    # --- 10Y Yield ---
    df_y = pd.read_excel(yield_path, header=None)
    y_data = df_y.iloc[8:, [1, 3]].copy()
    y_data.columns = ['Year_Str', 'IN10Y_Yield_Annual']
    y_data.dropna(subset=['Year_Str'], inplace=True)
    
    def parse_fy_start(ys):
        # "2024-25" -> 2024-04-01
        try:
            yr = int(str(ys).split('-')[0])
            return pd.Timestamp(year=yr, month=4, day=1)
        except:
            return pd.NaT
            
    y_data['date'] = pd.to_datetime(y_data['Year_Str'].apply(parse_fy_start))
    y_data.dropna(subset=['date'], inplace=True)
    y_data['IN10Y_Yield_Annual'] = pd.to_numeric(y_data['IN10Y_Yield_Annual'], errors='coerce')
    y_data.sort_values('date', inplace=True)
    
    print("Parsing RBI Repo Rate Excel...")
    # --- Repo Rate ---
    df_r = pd.read_excel(repo_path, header=None)
    r_data = df_r.iloc[8:, [1, 3]].copy()
    r_data.columns = ['date', 'Repo_Rate']
    r_data['date'] = pd.to_datetime(r_data['date'], errors='coerce')
    r_data['Repo_Rate'] = pd.to_numeric(r_data['Repo_Rate'], errors='coerce')
    r_data.dropna(subset=['date', 'Repo_Rate'], inplace=True)
    r_data.sort_values('date', inplace=True)
    
    print("Merging features sequentially to prevent look-ahead bias...")
    # Standardize datetime precision to ns to bypass pandas merge resolution errors
    macro_df['date'] = macro_df['date'].astype('datetime64[ns]')
    y_data['date'] = y_data['date'].astype('datetime64[ns]')
    r_data['date'] = r_data['date'].astype('datetime64[ns]')
    
    # Drop pre-existing empty columns from previous faulty run
    if 'IN10Y_Yield_Annual' in macro_df.columns:
        macro_df.drop(columns=['IN10Y_Yield_Annual'], inplace=True)
    if 'Repo_Rate' in macro_df.columns:
        macro_df.drop(columns=['Repo_Rate'], inplace=True)
    
    # Merge AsOf
    macro_df = pd.merge_asof(macro_df, y_data[['date', 'IN10Y_Yield_Annual']], on='date', direction='backward')
    macro_df = pd.merge_asof(macro_df, r_data[['date', 'Repo_Rate']], on='date', direction='backward')
    
    macro_df.to_csv(macro_path, index=False)
    print("Successfully integrated Yield and Repo Rates!")
    
    # Display the tail to prove it worked
    print("\nSample of integrated rates:")
    print(macro_df[['date', 'Repo_Rate', 'IN10Y_Yield_Annual']].dropna().tail(10))

if __name__ == "__main__":
    integrate_rates()
