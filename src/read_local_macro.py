import pandas as pd
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def inspect_local_files():
    cpi_path = os.path.join(_DATA_DIR, "Macro", "Consumer Price Index - Annual Variation.xlsx")
    gdp_path = os.path.join(_DATA_DIR, "Macro", "Quarterly Estimates of Gross Domestic Product (At Constant Prices) New Series (Base _ 2011-12).xlsx")
    
    print("--- CPI Data ---")
    try:
        df_cpi = pd.read_excel(cpi_path)
        print("Columns:", df_cpi.columns.tolist())
        print(df_cpi.head(10))
    except Exception as e:
        print(f"Error reading CPI data: {e}")
        
    print("\n--- GDP Data ---")
    try:
        df_gdp = pd.read_excel(gdp_path)
        print("Columns:", df_gdp.columns.tolist())
        print(df_gdp.head(10))
    except Exception as e:
        print(f"Error reading GDP data: {e}")

if __name__ == "__main__":
    inspect_local_files()
