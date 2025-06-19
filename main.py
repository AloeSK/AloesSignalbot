import os
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from telegram import Bot

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID") or "5731928017"

bot = Bot(token=TELEGRAM_TOKEN)

# List of Forex pairs
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCHF=X"]

# Strategy Parameters
MA_PERIOD = 14
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

def get_data(pair):
    try:
        df = yf.download(tickers=pair, interval="1m", period="30m")
        return df
    except:
        return None

def calculate_indicators(df):
    df["MA"] = df["Close"].rolling(window=MA_PERIOD).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=RSI_PERIOD).mean()
    avg_loss = loss.rolling(window=RSI_PERIOD).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def detect_candle_pattern(df):
    last = df.iloc[-2]  # second last completed candle
    body = abs(last["Open"] - last["Close"])
    range_total = last["High"] - last["Low"]
    
    if body < range_total * 0.3:
        return "Doji"
    elif last["Close"] > last["Open"] and last["Open"] < last["Low"] + 0.3 * range_total:
        return "Bullish Engulfing"
    elif last["Close"] < last["Open"] and last["Open"] > last["High"] - 0.3 * range_total:
        return "Bearish Engulfing"
    else:
        return None

def analyze(pair):
    df = get_data(pair)
    if df is None or len(df) < MA_PERIOD:
        return None
    df = calculate_indicators(df)
    last = df.iloc[-1]
    candle = detect_candle_pattern(df)

    signal = None
    if (
        last["Close"] > last["MA"]
        and last["RSI"] < RSI_OVERBOUGHT
        and candle == "Bullish Engulfing"
    ):
        signal = "UP"
    elif (
        last["Close"] < last["MA"]
        and last["RSI"] > RSI_OVERSOLD
        and candle == "Bearish Engulfing"
    ):
        signal = "DOWN"

    return signal

def send_signal(pair, signal):
    now = datetime.utcnow().strftime("%H:%M UTC")
    message = f"\u2705 Signal: {signal}\nPair: {pair}\nTime: {now}"
    bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)

def main():
    print("Bot started...")
    while True:
        for pair in PAIRS:
            signal = analyze(pair)
            if signal:
                send_signal(pair, signal)
        time.sleep(180)  # wait 3 minutes

if __name__ == "__main__":
    main()
# Redeploy trigger
