# test_apis.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_calculate_vwap():
    response = client.post("/calculate_vwap/", json=[
        {"open": 100, "close": 105, "high": 110, "low": 95, "volume": 1000},
        {"open": 102, "close": 99, "high": 108, "low": 97, "volume": 800}
    ])
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "VWAP" in response.json()[0]

def test_detect_candlesticks():
    response = client.post("/detect_candlesticks/", json=[
        {"open": 100, "close": 105, "high": 110, "low": 95, "volume": 1000},
        {"open": 102, "close": 99, "high": 108, "low": 97, "volume": 800},
        {"open": 98, "close": 106, "high": 109, "low": 96, "volume": 900}
    ])
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_eval_rebound():
    response = client.post("/evaluation/rebound", json={
        "data": [
            {"open": 100, "close": 105, "high": 110, "low": 95, "volume": 1000},
            {"open": 102, "close": 99, "high": 108, "low": 97, "volume": 800},
            {"open": 98, "close": 106, "high": 109, "low": 96, "volume": 900}
        ],
        "index": 0
    })
    assert response.status_code == 200
    assert "result" in response.json()
    assert response.json()["result"] in [0, 1]

def test_train_gradient_boosting():
    response = client.post("/train_GB/", json=[  # Corregido de /evaluation/train_GB a /train_GB/
        {"Candle_Type": "Bullish", "VWAP": 103, "Rebound_Success": 1},
        {"Candle_Type": "Bearish", "VWAP": 99, "Rebound_Success": 0},
        {"Candle_Type": "Bullish", "VWAP": 107, "Rebound_Success": 1}
    ])
    assert response.status_code == 200
    assert "accuracy" in response.json()
    assert 0 <= response.json()["accuracy"] <= 1

def test_eval_grid_search():
    response = client.post("/evaluation/grid-search", json={
        "data": [
            {"open": 100, "close": 105, "high": 110, "low": 95, "volume": 1000},
            {"open": 102, "close": 99, "high": 108, "low": 97, "volume": 800}
        ],
        "volume_windows": [3, 5],
        "height_windows": [3, 5]
    })
    assert response.status_code == 200
    assert "best_params" in response.json()
    assert "score" in response.json()


def test_eval_clusters():  # Corregido de test_optimize_clusters para claridad
    response = client.post("/optimize_clusters/", json={  # Corregido de /evaluation/cluster a /optimize_clusters/
        "data": [
            {"Candle_Type": 1, "VWAP": 103, "Spread": 10},
            {"Candle_Type": 0, "VWAP": 99, "Spread": 12},
            {"Candle_Type": 1, "VWAP": 107, "Spread": 8}
        ],
        "max_clusters": 5
    })
    assert response.status_code == 200
    assert "optimal_clusters" in response.json()
    assert "inertias" in response.json()
    assert isinstance(response.json()["optimal_clusters"], int)
    assert len(response.json()["inertias"]) <= 5