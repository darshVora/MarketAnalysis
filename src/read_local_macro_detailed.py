import pandas as pd

def inspect_advanced():
    cpi_path = r"d:\Project\MarketAnalysis\src\Data\Macro\Consumer Price Index - Annual Variation.xlsx"
    gdp_path = r"d:\Project\MarketAnalysis\src\Data\Macro\Quarterly Estimates of Gross Domestic Product (At Constant Prices) New Series (Base _ 2011-12).xlsx"
    
    with open('macro_inspect.txt', 'w') as f:
        f.write("--- CPI ---\n")
        try:
            df_cpi = pd.read_excel(cpi_path, header=None)
            f.write(df_cpi.head(20).to_string())
        except Exception as e:
            f.write(str(e))
            
        f.write("\n\n--- GDP ---\n")
        try:
            df_gdp = pd.read_excel(gdp_path, header=None)
            f.write(df_gdp.head(20).to_string())
        except Exception as e:
            f.write(str(e))

if __name__ == "__main__":
    inspect_advanced()
