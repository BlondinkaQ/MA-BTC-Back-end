from binance.client import Client
import json
import asyncio
from binance import AsyncClient, BinanceSocketManager
from datetime import datetime, timedelta


with open('config.json') as f:
    data_key = json.load(f)

СURRENCY_CRYPTO = 'BTCUSDT'
BTC_FOR_TRADE = 0.000312
actual_api_key = data_key['TEST_API_KEY']
actual_secret_key = data_key['TEST_SECRET_KEY']

client_syn = Client(actual_api_key, actual_secret_key)

client_syn.API_URL = 'https://testnet.binance.vision/api'



def datetime_range(start, end, delta):
    current = start
    while current < end:
        yield current
        current += delta

def buy_sell_crypto(trade, count_btc):
    if trade == 'buy':
        order = client_syn.create_order(
            symbol='BTCUSDT',
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=round(count_btc, 6))

    elif trade == 'sell':
        order = client_syn.create_order(
            symbol='BTCUSDT',
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=round(count_btc, 6))

    print(order)
    info = client_syn.get_asset_balance(asset='BTC')
    print(info)


async def kline_listener(client):
    bm = BinanceSocketManager(client)
    async with bm.kline_socket(symbol=СURRENCY_CRYPTO, interval='5m') as stream:
        data_check_buy = []
        while True:
            res = await stream.recv()
            klines_nine_ago = client_syn.get_historical_klines(СURRENCY_CRYPTO, Client.KLINE_INTERVAL_5MINUTE, "50 min ago UTC")
            date_kyiv = datetime.fromtimestamp(int(res['E']) / 1000).strftime('%d.%m.%Y %H:%M:%S')
            date_kyiv_not_formated = datetime.fromtimestamp(int(res['E']) // 1000)
            date_not_formated_year = datetime.fromtimestamp(int(res['E']) / 1000).year
            date_not_formated_month = datetime.fromtimestamp(int(res['E']) / 1000).month
            date_not_formated_day = datetime.fromtimestamp(int(res['E']) / 1000).day
            date_not_formated_hour = datetime.fromtimestamp(int(res['E']) / 1000).hour
            dts = [dt for dt in
                   datetime_range(datetime(date_not_formated_year, date_not_formated_month, date_not_formated_day, date_not_formated_hour), datetime(date_not_formated_year, date_not_formated_month, date_not_formated_day, date_not_formated_hour+1, 1),
                                  timedelta(minutes=5))]

            print(date_kyiv_not_formated, date_kyiv_not_formated-timedelta(seconds=1), date_kyiv_not_formated-timedelta(seconds=2))
            print(date_not_formated_year, date_not_formated_month, date_not_formated_day, date_not_formated_hour)
            print(dts)
            print(date_kyiv, ':', res['k']['c'])
            print('MA: ',sum(float(klines_nine_ago[i][4]) for i in range(9)) / 9)
            moving_average = sum(float(klines_nine_ago[i][4]) for i in range(9)) / 9

            if data_check_buy == []:
                info_order = 'NO DATA ORDER'
            elif len(data_check_buy) == 1:
                info_order = data_check_buy[0]
            else:
                info_order = data_check_buy[-1]

            print(info_order)

            if info_order == 'NO DATA ORDER' or info_order == 'Close position':
                if (date_kyiv_not_formated or date_kyiv_not_formated - timedelta(
                        seconds=1) or date_kyiv_not_formated - timedelta(seconds=2)) in dts:
                    print('BYU BTC OR SELL interval 5m')
                    if float(res['k']['c']) > moving_average:
                        buy_sell_crypto('sell', BTC_FOR_TRADE)
                        print('продаем заданный обьем ВТС')
                        data_check_buy.append('Open sell BTC')
                    elif float(res['k']['c']) < moving_average:
                        buy_sell_crypto('buy', BTC_FOR_TRADE)
                        print('покупаем заданный объём ВТС')
                        data_check_buy.append('Open buy BTC')
            elif info_order == 'Open sell BTC':
                print('Пробуєм закупить заданный объём ВТС для закрытия позиции')
                if float(res['k']['c']) - 100 <= moving_average <= float(res['k']['c']) + 100: #Close position #інтервал для закриття обраткі
                    buy_sell_crypto('byu', BTC_FOR_TRADE)
                    print('Закрыли позицию, ждем новый оредер')
                    data_check_buy.append('Close position')
            elif info_order == 'Open buy BTC':
                print('Пробуєм продать заданный обьем ВТС для закрытия позиции')
                if float(res['k']['c']) - 100 <= moving_average <= float(res['k']['c']) + 100: #Close position #інтервал для закриття обраткі
                    buy_sell_crypto('byu', BTC_FOR_TRADE)
                    print('Закрыли позицию, ждем новый оредер')
                    data_check_buy.append('Close position')


async def main():
    client = await AsyncClient.create()
    await kline_listener(client)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


