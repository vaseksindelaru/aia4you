"""
save_detection_results.py - Module for saving Shakeout strategy detection results to database (autonomous detect version)

This module provides functionality to save key candle detection results from the
Shakeout strategy to the binance_lob database for further analysis and visualization.

Adapted for the standalone 'detect' module.
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
import json
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Use the local Detector from the detect folder
from detect import Detector

class DetectionResultSaver:
    """
    Class for saving Shakeout strategy detection results to the binance_lob database.
    This class handles the database connection and provides methods to save
    detection results, including key candle data and detection parameters.
    """
    def __init__(self, host=None, user=None, password=None, database=None):
        load_dotenv()
        self.db_config = {
            'host': host or os.getenv('MYSQL_HOST', 'localhost'),
            'user': user or os.getenv('MYSQL_USER', 'root'),
            'password': password or os.getenv('MYSQL_PASSWORD', ''),
            'database': database or os.getenv('MYSQL_DATABASE', 'binance_lob')
        }
        print(f"Database configuration: host={self.db_config['host']}, user={self.db_config['user']}, database={self.db_config['database']}")
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                print(f"Connected to MySQL database: {self.db_config['database']}")
                return True
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            return False

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def create_tables(self):
        self.connect()
        # Table creation SQLs (same as original)
        session_table = '''CREATE TABLE IF NOT EXISTS detection_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(32),
            timeframe VARCHAR(16),
            csv_file VARCHAR(255),
            detection_time DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;'''
        self.cursor.execute(session_table)
        params_table = '''CREATE TABLE IF NOT EXISTS detection_params (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT,
            volume_threshold INT,
            body_threshold INT,
            lookback INT,
            num_candles INT,
            FOREIGN KEY (session_id) REFERENCES detection_sessions(id)
        )'''
        key_candles_table = '''CREATE TABLE IF NOT EXISTS key_candles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT,
            candle_index INT,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume FLOAT,
            volume_percentile FLOAT,
            body_percentage FLOAT,
            is_key_candle BOOLEAN,
            FOREIGN KEY (session_id) REFERENCES detection_sessions(id)
        )'''
        for sql in [session_table, params_table, key_candles_table]:
            self.cursor.execute(sql)
        self.connection.commit()

    def save_session(self, symbol, timeframe, csv_file):
        sql = '''INSERT INTO detection_sessions (symbol, timeframe, csv_file) VALUES (%s, %s, %s)'''
        try:
            self.cursor.execute(sql, (symbol, timeframe, csv_file))
            self.connection.commit()
            return self.cursor.lastrowid
        except mysql.connector.Error as e:
            # Manejo automático si la columna csv_file no existe
            if e.errno == 1054 and "csv_file" in str(e):
                print("Columna 'csv_file' no existe en detection_sessions. Intentando agregarla automáticamente...")
                self.cursor.execute("ALTER TABLE detection_sessions ADD COLUMN csv_file VARCHAR(255)")
                self.connection.commit()
                # Reintenta la inserción
                self.cursor.execute(sql, (symbol, timeframe, csv_file))
                self.connection.commit()
                return self.cursor.lastrowid
            else:
                raise

    def save_params(self, session_id, volume_threshold, body_threshold, lookback, num_candles):
        sql = '''INSERT INTO detection_params (session_id, volume_threshold, body_threshold, lookback, num_candles) VALUES (%s, %s, %s, %s, %s)'''
        # Verifica el esquema de la tabla detection_params y agrega todas las columnas faltantes antes de intentar la inserción
        self.cursor.execute("SHOW COLUMNS FROM detection_params")
        existing_cols = set(row[0] for row in self.cursor.fetchall())
        required_cols = {"volume_threshold": "INT", "body_threshold": "INT", "lookback": "INT", "num_candles": "INT"}
        missing_cols = [f"ADD COLUMN {col} {coltype}" for col, coltype in required_cols.items() if col not in existing_cols]
        if missing_cols:
            print(f"Columnas faltantes en detection_params: {missing_cols}. Intentando agregarlas automáticamente...")
            for alter in missing_cols:
                try:
                    self.cursor.execute(f"ALTER TABLE detection_params {alter}")
                except mysql.connector.Error as e2:
                    if e2.errno == 1060:  # Duplicate column name
                        continue
                    else:
                        raise
            self.connection.commit()
        # Ahora sí intenta la inserción normalmente
        self.cursor.execute(sql, (session_id, volume_threshold, body_threshold, lookback, num_candles))
        self.connection.commit()

    def save_key_candles(self, session_id, key_candles):
        sql = '''INSERT INTO key_candles (session_id, candle_index, open, high, low, close, volume, volume_percentile, body_percentage, is_key_candle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        for candle in key_candles:
            self.cursor.execute(sql, (
                session_id,
                int(candle['index']),
                float(candle['open']),
                float(candle['high']),
                float(candle['low']),
                float(candle['close']),
                float(candle['volume']),
                float(candle['volume_percentile']),
                float(candle['body_percentage']),
                bool(candle['is_key_candle'])
            ))
        self.connection.commit()

    def save_all(self, detector, symbol, timeframe, csv_file):
        self.create_tables()
        # Eliminar sesiones previas para symbol, timeframe y csv_file
        self.cursor.execute("SELECT id FROM detection_sessions WHERE symbol=%s AND timeframe=%s AND csv_file=%s", (symbol, timeframe, csv_file))
        old_sessions = self.cursor.fetchall()
        if old_sessions:
            old_session_ids = [row[0] for row in old_sessions]
            format_ids = ','.join(['%s']*len(old_session_ids))
            # Borra primero key_candles y detection_params, luego la sesión
            self.cursor.execute(f"DELETE FROM key_candles WHERE session_id IN ({format_ids})", tuple(old_session_ids))
            self.cursor.execute(f"DELETE FROM detection_params WHERE session_id IN ({format_ids})", tuple(old_session_ids))
            self.cursor.execute(f"DELETE FROM detection_sessions WHERE id IN ({format_ids})", tuple(old_session_ids))
            self.connection.commit()
        params = detector.detection_params
        key_candles = detector.results
        # Save session
        session_id = self.save_session(symbol, timeframe, csv_file)
        # Save params
        num_candles = len(detector.data) if hasattr(detector, 'data') and detector.data is not None else 0
        self.save_params(session_id, params.get('volume_percentile_threshold', 80), params.get('body_percentage_threshold', 30), params.get('lookback_candles', 50), num_candles)
        # Save key candles
        self.save_key_candles(session_id, key_candles)
        print(f"Detection results saved to DB. Session ID: {session_id}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Save Shakeout detection results to DB (detect version)")
    parser.add_argument('--csv', type=str, required=True, help='Path to CSV file')
    parser.add_argument('--symbol', type=str, required=True, help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--timeframe', type=str, required=True, help='Timeframe (e.g., 5m)')
    parser.add_argument('--volume_threshold', type=int, default=80, help='Volume percentile threshold')
    parser.add_argument('--body_threshold', type=int, default=30, help='Body percentage threshold')
    parser.add_argument('--lookback', type=int, default=20, help='Lookback candles')
    args = parser.parse_args()

    detector = Detector(csv_path=args.csv)
    detector.set_detection_params(
        volume_percentile_threshold=args.volume_threshold,
        body_percentage_threshold=args.body_threshold,
        lookback_candles=args.lookback
    )
    # Procesa el CSV y guarda los resultados en detector.results para compatibilidad con formato Binance (timestamp al inicio)
    detector.results = detector.process_csv()
    saver = DetectionResultSaver()
    saver.save_all(detector, args.symbol, args.timeframe, args.csv)
    saver.close()
    print("Done.")
