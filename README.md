# Indian Market Analysis

This project is designed to fetch, analyze, and visualize data from the Indian stock market (NSE/BSE). It provides a structured foundation for financial data analysis.

## Features
- Fetch historical market data using `yfinance`
- Calculate key technical indicators (e.g., Moving Averages, Daily Returns)
- Modular structure for easy extension

## Project Structure
- `src/`: Core Python modules (`data_fetcher.py`, `analyzer.py`).
- `notebooks/`: Directory for Jupyter notebooks (EDA and visualization).
- `data/`: Directory to store downloaded or generated data (add to `.gitignore`).
- `requirements.txt`: Python package dependencies.
- `main.py`: Example entry point to run the analysis.

## Setup Instructions

1. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the main analysis script:
```bash
python main.py
```

Note: To fetch data for Indian stocks via Yahoo Finance, append `.NS` for National Stock Exchange (NSE) or `.BO` for Bombay Stock Exchange (BSE) to the ticker symbol. For example, Reliance Industries on NSE is `RELIANCE.NS`.
