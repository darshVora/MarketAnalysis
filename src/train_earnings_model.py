import polars as pl
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd

def train_earnings_model():
    data_path = r"d:\Project\MarketAnalysis\src\Data\earnings_model_data.parquet"
    
    print("1. Loading Event-Study Corporate Earnings Dataset...")
    df = pl.read_parquet(data_path).to_pandas()
    
    # Sort chronologically to prevent lookahead bias in training
    df.sort_values('event_date', inplace=True)
    df.dropna(inplace=True)
    
    # Exclude extreme infinity outliers gracefully
    df = df[(df['profit_yoy_growth'] < 100) & (df['profit_yoy_growth'] > -100)]
    df = df[(df['rev_yoy_growth'] < 100) & (df['rev_yoy_growth'] > -100)]
    
    print(f"Total usable earnings events: {len(df)}")
    
    print("\n2. Defining Factor Features & Target...")
    features = ['profit_yoy_growth', 'rev_yoy_growth', 'pre_runup_20d_%']
    target = 'forward_drift_20d_%'
    
    X = df[features]
    y = df[target]
    
    print("3. Executing Strict Chronological Data Split...")
    # Train on first 80% of history, test strictly out-of-sample on recent 20%
    split_idx = int(len(df) * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"Training on {len(X_train)} historical earnings events up to {df['event_date'].iloc[split_idx-1].date()}")
    print(f"Testing entirely blind on {len(X_test)} recent reports starting from {df['event_date'].iloc[split_idx].date()}")
    
    print("\n4. Training XGBoost Factor Regression Model...")
    model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    print("\n5. Evaluating Theoretical Accuracy...")
    predictions = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, predictions)
    # Convert back to actual percentages for display
    print(f"Mean Absolute Error: {mae:.2f}%")
    
    print("\n6. Autonomously Discovered Factor Importances:")
    # Print what actually drives the stock prices
    importance = pd.DataFrame({
        'Feature/Attribute': features,
        'Predictive Weight': model.feature_importances_
    }).sort_values(by='Predictive Weight', ascending=False)
    
    print(importance.to_string(index=False))

if __name__ == "__main__":
    train_earnings_model()
