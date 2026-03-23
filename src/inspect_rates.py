import pandas as pd
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def inspect_rates():
    yield_path = os.path.join(_DATA_DIR, "Macro", "Interest Rates on Central and State Government Dated Securities.xlsx")
    repo_path = os.path.join(_DATA_DIR, "Macro", "Major Monetary Policy Rates and Reserve Requirements - Bank Rate, LAF (Repo, Reverse Repo, SDF and MSF) Rates, CRR & SLR.xlsx")
    
    with open('rates_inspect.txt', 'w') as f:
        f.write("--- 10-Year Yield ---\n")
        try:
            df_y = pd.read_excel(yield_path, header=None)
            f.write(df_y.head(30).to_string())
        except Exception as e:
            f.write(str(e))
            
        f.write("\n\n--- RBI Repo Rate ---\n")
        try:
            df_r = pd.read_excel(repo_path, header=None)
            f.write(df_r.head(30).to_string())
        except Exception as e:
            f.write(str(e))

if __name__ == "__main__":
    inspect_rates()
