import asyncio
import asyncio
import pandas as pd
from binance import AsyncClient, BinanceSocketManager

with open('access_key.txt', 'r') as key_file:
	key_str = [line for line in key_file]

# set access key
ACCESS_KEY = key_str[0]
SECRET_ACCESS_KEY = key_str[1]
COIN_PRICE_SOCKET = "wss://fstream.binance.com/ws/!miniTicker@arr"
COIN_NAME_MAP = "https://api.binance.com/api/v3/exchangeInfo"

async def main():
	pass
