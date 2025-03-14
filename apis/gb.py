# gb.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score

def train_gradient_boosting(data):
    df = pd.DataFrame(data)
    df['Candle_Type'] = df['Candle_Type'].map({'Bullish': 1, 'Bearish': 0})
    features = df[['Candle_Type', 'VWAP']]
    label = df['Rebound_Success']
    X_train, X_test, y_train, y_test = train_test_split(features, label, test_size=0.2, random_state=42)
    model = GradientBoostingClassifier()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    return {"model": model, "accuracy": accuracy}