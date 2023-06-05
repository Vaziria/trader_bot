import sys
from datetime import datetime
from binance.client import Client
import socket
import threading
import json
from time import sleep, time
from ta.trend import STCIndicator
import pandas as pd
import requests
import websocket
import subprocess


def log(data):
    msg = f"[{str(datetime.now()).split('.')[0]}]: {data}"
    print(msg)
    f = open('BOTLOG.txt', 'a')
    f.write(msg + "\n")
    f.close()


def getConf():
    cf = open('Config.json', 'r')
    conf = json.load(cf)
    cf.close()
    return conf


class Botser:

    def __init__(self, conf):

        self.conf = getConf()
        self.client = Client(self.conf['PubApi'], self.conf['PrvApi'])
        self.pubclient = Client()
        self.s = socket.socket()
        self.port = 80

        self.qtyFilter = {}
        self.priceFilter = {}
        self.bought = {}
        self.amount = None
        self.sl = None
        self.tp = None
        self.tpCoeff = None
        self.nextTP = None
        self.status = True
        self.stopOrder = {}

        self.BINANCE_END_POINT = "https://api.binance.com/api/v3/userDataStream"
        self.SPOT_STREAM_END_POINT = "wss://stream.binance.com:9443"
        self.TICKERS_STREAM_END_POINT = f'wss://stream.binance.com:9443/ws/!miniTicker@arr'

        self.apiKey = self.conf['PubApi']
        self.create_spot_key()

        self.ws = None
        self.wsList = []
        self.tkwsList = []

        self.allowBuy = {}
        self.openBalance = {}

    def placeSL(self, symbol, price, tpPrice):
        try:
            qty = float(self.client.get_asset_balance(symbol[:-4], recvWindow=59990)['free'])
            qty = self.precision(qty, self.qtyFilter[symbol])
            sellPrice = price
            sellPrice = self.precision(sellPrice, self.priceFilter[symbol])
            self.stopOrder[symbol] = \
                self.client.create_order(symbol=symbol, side='SELL', type='STOP_LOSS_LIMIT', quantity=qty, price=sellPrice,
                                         stopPrice=price,
                                         timeInForce='GTC', recvWindow=59990)['orderId']
            log(f'SL Placed = {price} | Wait TP = {tpPrice} | QTY = {qty}')
        except Exception as sle:
            if 'would trigger immediately' in str(sle):
                self.stopOrder[symbol] = self.client.create_order(symbol=symbol, side='SELL', type='MARKET', quantity=qty)['orderId']
                log(f'SL Placed = {price} | QTY = {qty}')
            else:
                log(f'STOP Error:> {sle}')

    def initBuy(self, symbol):
        sleep(self.sleepDelay)
        self.allowBuy[symbol] = True

    def alert(self, conn):
        data = conn.recv(10000)
        alert = None
        if data != b'':
            try:
                ndata = b'{' + data.split(b'{')[1]
                alert = json.loads(ndata)
                log(alert)
            except:
                pass
        conn.close()
        if not alert:
            sys.exit()

        # example: {"pair": "ETHUSDT", "pin": "PASSWORD"}

        try:
            symbol = alert['pair'].upper()
            try:
                symbol = symbol.split('PERP')[0]
            except:
                pass
            pin = alert['pin'].upper()
        except:
            symbol = None
            pin = None

        if symbol is not None and pin is not None and not self.allowBuy.__contains__(symbol) or self.allowBuy[symbol]:

            if pin == self.pinCode:
                # sleep(0.5)
                if not self.bought.__contains__(symbol):

                    orders = self.client.get_open_orders(symbol=symbol, recvWindow=59990)
                    if len(orders) == 0:

                        amount = self.amount
                        try:
                            self.oldBalance = float(self.client.get_asset_balance(symbol[-4:])['free'])
                            orderId = self.client.order_market_buy(symbol=symbol, quoteOrderQty=amount, recvWindow=59990)['orderId']

                            last_order = self.client.get_order(symbol=symbol, orderId=orderId)
                            while last_order['status'] != 'FILLED':
                                last_order = self.client.get_order(symbol=symbol, orderId=orderId)
                                sleep(1)

                            tradePrice = float(last_order['cummulativeQuoteQty']) / float(last_order['origQty'])
                            qty = float(last_order['origQty'])

                            msg = f'{symbol} Buy = {tradePrice} | QTY = {qty}'
                            log(msg)
                            self.bought[symbol] = tradePrice, qty
                            self.allowBuy[symbol] = False
                            self.openBalance[symbol] = float(last_order['cummulativeQuoteQty'])

                            slPrice = tradePrice - (tradePrice * self.sl / 100)
                            slPrice = self.precision(slPrice, self.priceFilter[symbol])
                            tpPrice = tradePrice + (tradePrice * (self.tp if not self.nextTP else self.nextTP) / 100)
                            tpPrice = self.precision(tpPrice, self.priceFilter[symbol])

                            self.placeSL(symbol, slPrice, tpPrice)
                        except Exception as be:
                            log(f'BUY Error:> {be}')
            else:
                log(f'WRONG PASSWORD: {pin}')
    "---------------------------------------------WS User Data---------------------------------------------"

    def stream_user(self):
        spot_connection_url = f"{self.SPOT_STREAM_END_POINT}/ws/{self.listenKey}"
        self.ws = websocket.WebSocketApp(url=spot_connection_url, on_open=self.on_open, on_message=self.on_message,
                                         on_error=self.on_error, on_close=self.on_close)
        self.ws.run_forever(ping_interval=60 * 10)

    def on_message(self, ws, message):
        msg = json.loads(message)
        if str(msg['e']).upper() == 'executionReport'.upper():

            status = msg['X']
            orderId = msg['i']

            if str(status).upper() == 'FILLED'.upper():
                if self.bought.__contains__(msg['s']):
                    if list(self.stopOrder.values()).__contains__(orderId):
                        self.orderFilled(msg)
                    else:
                        sleep(1)
                        if list(self.stopOrder.values()).__contains__(orderId):
                            self.orderFilled(msg)

    def on_open(self, ws):
        self.wsList.append(ws)
        if len(self.wsList) > 1:
            self.wsList[0].close()
            self.wsList.pop(0)

    def on_error(self, ws, error):
        log(f"ErrorWS: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        log(f"User Stream Closed")
        try:
            self.wsList.remove(ws)
        except:
            pass
        if len(self.wsList) == 0:
            threading.Thread(target=self.stream_user, daemon=True).start()

    def closeStream(self):
        requests.delete(url=self.BINANCE_END_POINT, json={"listenKey": self.listenKey})
        self.ws.close()

    def orderFilled(self, message):

        # try:
        order = message
        symbol = order['s']
        price = float(order['L']) if float(order['L']) > 0 else float(order['p'])
        qty = self.bought[symbol][1]

        # balance = float(self.client.get_asset_balance(symbol[-4:])['free'])
        loss = round(self.openBalance[symbol] - (qty * price), 2)
        msg = f'{symbol} SL-FILLED = {price} | Loss = {loss} $'
        log(msg)

        self.allowBuy[symbol] = True
        threading.Thread(target=self.initBuy, args=(symbol,), daemon=True).start()
        self.nextTP = self.tp * self.tpCoeff

        self.bought.pop(symbol)
        try:
            self.stopOrder.pop(symbol)
        except:
            pass

    "---------------------------------------------End WS User Data---------------------------------------------"

    "--------------------------------------------- WS Ticker  ---------------------------------------------"

    def sortTickers(self, ticker):
        return ticker[0]

    def getTickerPrice(self, symbol):

        currentTicker = self.tickers
        priceCall = lambda tickers: self.checkTickerPrice(symbol, tickers)
        priceList = list(map(priceCall, currentTicker))
        priceList.sort(reverse=True)
        return priceList[0]

    def tickerUpdate(self, ws, message):

        msg = json.loads(message)
        self.tickers = msg

        for symbol in self.bought:
            curPrice = self.getTickerPrice(symbol)
            if curPrice > 0:
                sPrice = self.bought[symbol][0] + (self.bought[symbol][0] * (self.tp if not self.nextTP else self.nextTP) / 100)
                sPrice = self.precision(sPrice, self.priceFilter[symbol])
                # log(f'{symbol}: {curPrice} | SELL = {sPrice}')
                if curPrice >= sPrice:

                    log(f'{symbol}: Placing TP order')
                    if self.stopOrder.__contains__(symbol):

                        try:
                            self.client.cancel_order(symbol=symbol, orderId=self.stopOrder[symbol], recvWindow=59990)
                            self.stopOrder.pop(symbol)
                            log(f'{symbol}: SL Canceled')
                        except:
                            pass

                    try:
                        bal = self.client.get_asset_balance(symbol[:-4], recvWindow=59990)
                        qty = float(bal['free'])
                        qty = self.precision(qty, self.qtyFilter[symbol])
                        locked = float(bal['locked'])
                        locked = self.precision(locked, self.qtyFilter[symbol])

                        if locked > 0 and self.stopOrder.__contains__(symbol):

                            log(f'{symbol}: Free = {qty} | Locked = {locked}')
                            try:
                                self.client.cancel_order(symbol=symbol, orderId=self.stopOrder[symbol],
                                                         recvWindow=59990)
                                self.stopOrder.pop(symbol)
                                log(f'{symbol}: SL Canceled')
                                bal = self.client.get_asset_balance(symbol[:-4], recvWindow=59990)
                                qty = float(bal['free'])
                                qty = self.precision(qty, self.qtyFilter[symbol])
                            except:
                                pass

                        if qty > self.qtyFilter[symbol]: # untuk jual asset
                            orderId = self.client.order_limit_sell(symbol=symbol, quantity=qty, price=sPrice, recvWindow=59990)['orderId']

                            last_order = self.client.get_order(symbol=symbol, orderId=orderId)
                            while last_order['status'] != 'FILLED':
                                last_order = self.client.get_order(symbol=symbol, orderId=orderId)
                                sleep(1)
                            try:
                                tradePrice = float(last_order['cummulativeQuoteQty']) / float(last_order['origQty'])
                                qty = float(last_order['origQty'])
                                msg = f'{symbol} TP-SELL = {tradePrice} | QTY = {qty}'
                                total = float(last_order['cummulativeQuoteQty'])
                            except:
                                tradePrice = float(last_order['price'])
                                qty = float(last_order['origQty'])
                                msg = f'{symbol} TP-SELL = {tradePrice} | QTY = {qty}'
                                total = tradePrice * qty

                            # balance = float(self.client.get_asset_balance(symbol[-4:])['free'])
                            profit = round(total - self.openBalance[symbol], 2)
                            log(msg+f' | Profit = {profit} $')
                            self.nextTP = 0

                        threading.Thread(target=self.initBuy, args=(symbol,), daemon=True).start()

                        self.bought.pop(symbol)
                        try:
                            self.stopOrder.pop(symbol)
                        except:
                            pass

                    except Exception as te:
                        if 'quantity' in str(te):
                            log(f'TP Error:> QTY = {qty} | {te}')
                            self.allowBuy[symbol] = False
                            threading.Thread(target=self.initBuy, args=(symbol,), daemon=True).start()

                            self.bought.pop(symbol)
                            try:
                                self.stopOrder.pop(symbol)
                            except:
                                pass
                        else:
                            log(f'TP Error:> {te}')

    def tickerStreamOpen(self, ws):
        self.tkwsList.append(ws)
        if len(self.tkwsList) > 1:
            self.tkwsList[0].close()
            self.tkwsList.pop(0)

    def stream_ticker(self):

        self.tws = websocket.WebSocketApp(self.TICKERS_STREAM_END_POINT, on_message=self.tickerUpdate, on_open=self.tickerStreamOpen, on_error=self.tickerError, on_close=self.tickerClose)
        self.tws.run_forever(ping_interval=60 * 5)

    def checkTickerPrice(self, symbol, ticker):

        if ticker['s'] == symbol:
            return float(ticker['c'])
        else:
            return 0

    def tickerError(self, ws, error):
        pass

    def tickerClose(self, ws, close_status_code, close_msg):
        try:
            self.tkwsList.remove(ws)
        except:
            pass
        if len(self.tkwsList) == 0:
            threading.Thread(target=self.stream_ticker, daemon=True).start()

    "---------------------------------------------End WS Ticker---------------------------------------------"

    def renewKey(self):
        while self.status:
            sleep(23 * 60 * 60)
            threading.Thread(target=self.stream_user, daemon=True).start()

    def create_spot_key(self):
        self.listenKey = requests.post(url=self.BINANCE_END_POINT, headers={'X-MBX-APIKEY': self.apiKey}).json()[
            'listenKey']
        return self.listenKey

    def keepAlive(self):
        while self.status:
            sleep(60 * 10)
            re = requests.put(url=self.BINANCE_END_POINT, headers={'X-MBX-APIKEY': self.apiKey},
                              data={"listenKey": self.listenKey})
            # log(f'Send Ping: {re.json()}')

    def get_qty_step(self):
        for each in self.pubclient.get_exchange_info()['symbols']:
            for filter in each['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    stepSize = float(filter['stepSize'])
                    self.qtyFilter[each['symbol'].upper()] = stepSize

    def get_price_step(self):
        for each in self.pubclient.get_exchange_info()['symbols']:
            for filter in each['filters']:
                if filter['filterType'] == 'PRICE_FILTER':
                    stepSize = float(filter['tickSize'])
                    self.priceFilter[each['symbol'].upper()] = stepSize

    def precision(self, amount, step):
        return round(int(amount / step) * step, 8)

    def updateFilter(self):
        while self.status:
            self.get_qty_step()
            self.get_price_step()
            sleep(600)

    def updateConfig(self):
        while self.status:
            try:

                self.conf = getConf()
                self.status = self.conf["run"]
                self.amount = self.conf['Amount']
                self.sl = self.conf["SL"]
                self.tp = self.conf["TP"]
                self.tpCoeff = self.conf["TPcoeff"]
                self.sleepDelay = self.conf["Sleep"]
                self.pinCode = self.conf["Pin"]

                if self.status:
                    sleep(1)

            except Exception as ge:
                log(f'Global Error:> {ge}')
                sleep(1)

    def run(self):

        self.conf = getConf()
        self.status = self.conf["run"]
        self.amount = self.conf['Amount']
        self.sl = self.conf["SL"]
        self.tp = self.conf["TP"]
        self.tpCoeff = self.conf["TPcoeff"]
        self.sleepDelay = self.conf["Sleep"]
        self.pinCode = self.conf["Pin"]

        threading.Thread(target=self.renewKey, daemon=True).start()
        threading.Thread(target=self.keepAlive, daemon=True).start()
        threading.Thread(target=self.updateConfig, daemon=True).start()
        threading.Thread(target=self.updateFilter, daemon=True).start()
        threading.Thread(target=self.stream_user, daemon=True).start()
        threading.Thread(target=self.stream_ticker, daemon=True).start()

        sleep(3)
        self.s.bind(('', self.port))
        self.s.listen()
        log(f'START TRADING')

        self.start = True

        while self.status:

            try:
                c, addr = self.s.accept()
                threading.Thread(target=self.alert, args=(c,), daemon=True).start()
            except:
                pass

        self.s.close()

 
cf = open('Config.json', 'r')
conf = json.load(cf)
cf.close()

bot1 = Botser(conf)
bot1.run()
