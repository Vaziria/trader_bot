import socket
import threading
import json
from datetime import datetime,timedelta
import time
from binance.client import Client
import sys
import pause


def getConfig():

    try:
        cf = open('Config.json', 'r')
        conf = json.load(cf)
        cf.close()
    except:
        cf = open('Config.json', 'w')
        conf = {"PubApi": '', "PrvApi": '', "EntryMargin": '', "MaxMargin":  '', "Leverage": '', "Tp": '', "Sl": '', "NextCoefficient": ''}
        json.dump(conf, cf)
        cf.close()

    return conf


def show(msg):
    f = open('Trading.txt', 'a')
    f.write(f'{str(datetime.now()).split(".")[0]}: ' + msg + '\n')
    f.close()
    print(msg)


class Botser:

    def __init__(self):

        self.conf = getConfig()

        if self.conf['EntryMargin']:
            try:

                self.client = Client(self.conf['PubApi'], self.conf['PrvApi'])
                self.client.get_asset_balance('USDT', recvWindow=59990)
                self.pubclient = Client()
                self.open = False
                self.rn = True
                self.balance = None
                self.s = socket.socket()
                self.port = 80

            except:
                print("Api Keys Not Valid")
                del self

        else:
            print("There's no configuration")
            del self

    def getFilters(self):

        for symbol in Client().futures_exchange_info()['symbols']:
            if symbol['symbol'] == self.symbol:
                for filter in symbol['filters']:

                    if filter['filterType'] == 'LOT_SIZE':
                        qtyFilter = float(filter['stepSize'])
                    if filter['filterType'] == 'PRICE_FILTER':
                        priceFilter = float(filter['tickSize'])

                return qtyFilter, priceFilter

    def precision(self, amount, step):
        return round(int(amount / step) * step, 6)

    def getBalance(self):

        for each in self.client.futures_account_balance(recvWindow=59990):
            if each['asset'] == 'USDT':
                #return float(each['availableBalance'])
                return float(each['balance'])

    def ordersCheck(self, profitOrder, stopOrder):

        while self.open:
            pl = self.getBalance() - self.balance
            last_order = self.client.futures_get_order(symbol=self.symbol, orderId=profitOrder, recvWindow=59990)
            if last_order['status'] == 'FILLED':
                self.client.futures_cancel_order(symbol=self.symbol, orderId=stopOrder, recvWindow=59990)
                self.open = False
                pl = self.getBalance() - self.balance
                show(f'{self.symbol}: Hit Take Profit, Cuan = {pl} USDT')
                
                # now = datetime.now()
                # print(now)
                # session_break = now.replace(hour=7, minute=0, second=0, microsecond=0)
                # sleep_ = (timedelta(hours=24) - (now - session_break)).total_seconds() % (24 * 3600)
                # if session_break < now:
                #     session_break = now.replace(now.year, now.month, now.day+1,hour=7, minute=0, second=0, microsecond=0)
                #     sleep_ = (timedelta(hours=24) - (now - session_break)).total_seconds() % (24 * 3600)
                # print(f'Last Trade is Profit, Bot Closed Until {session_break}')
                # while now < session_break:
                #     sys.exit()
                    #self.s.close()
                # time.sleep(sleep_)
                
                
                break
                

            last_order = self.client.futures_get_order(symbol=self.symbol, orderId=stopOrder, recvWindow=59990)
            if last_order['status'] == 'FILLED':
                try:
                    self.client.futures_cancel_order(symbol=self.symbol, orderId=profitOrder, recvWindow=59990)
                    self.open = False
                except:
                    self.open = False
                    pass
                pl = self.getBalance() - self.balance
                show(f'{self.symbol}: Hit Stop Loss, Minus = {pl} USDT')
                
                break

            time.sleep(2)
    
    def closePosition(self):

        try:
            pos = float(self.client.futures_position_information(symbol=self.symbol)[0]['positionAmt'])
            
            if self.side == 'BUY':

                if pos < 0.0:
                    qty = self.precision(pos.__abs__(), self.qtyFilter)
                    orderId = self.client.futures_create_order(symbol=self.symbol, side='BUY', type='MARKET', quantity=qty, reduceOnly=True, recvWindow=59990)['orderId']
                    self.client.futures_cancel_all_open_orders(symbol=self.symbol, recvWindow=59990)
                    self.open = False

                    last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
                    while last_order['status'] != 'FILLED':
                        last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
                        time.sleep(0.5)

                    trade_price = float(last_order['avgPrice'])
                    pl = self.getBalance() - self.balance
                    show(f'{self.symbol}: Close Short Position Price = {trade_price}, Cuan = {pl} USDT')

            elif self.side == 'SELL':

                if pos > 0.0:
                    qty = self.precision(pos, self.qtyFilter)
                    orderId = self.client.futures_create_order(symbol=self.symbol, side='SELL', type='MARKET', quantity=qty, reduceOnly=True, recvWindow=59990)['orderId']
                    self.client.futures_cancel_all_open_orders(symbol=self.symbol, recvWindow=59990)
                    self.open = False

                    last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
                    while last_order['status'] != 'FILLED':
                        last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
                        time.sleep(0.5)

                    trade_price = float(last_order['avgPrice'])
                    pl = self.getBalance() - self.balance
                    show(f'{self.symbol}: Close Long Position Price = {trade_price}, Cuan = {pl} USDT')
            
            return qty,trade_price

        except Exception as ce:
            show(f'{self.symbol}: Close Error:> {ce}')

    def openPosition(self, qty):

        self.conf = getConfig()

        try:
            self.client.futures_change_leverage(symbol=self.symbol, leverage=self.conf['Leverage'], recvWindow=59990)
        except:
            pass
        qty = self.precision(qty, self.qtyFilter)
        orderId = self.client.futures_create_order(symbol=self.symbol, side=self.side, type='MARKET', quantity=qty, recvWindow=59990)['orderId']
        try:
            self.open = True

            last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
            while last_order['status'] != 'FILLED':
                last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
                time.sleep(0.5)

            trade_price = float(last_order['avgPrice'])
            openQty = float(last_order['origQty'])
            msg = f'{self.symbol}: Open {"Long" if self.side == "BUY" else "Short"} Position Qty = {openQty} | Price = {trade_price}'
            show(msg)
            return trade_price, openQty

        except Exception as oe:
            show(f'{self.symbol}: Open Error:> {oe}')
            last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
            # while last_order['status'] != 'FILLED':
                # last_order = self.client.futures_get_order(symbol=self.symbol, orderId=orderId)
                # time.sleep(0.5)

            trade_price = float(last_order['avgPrice'])
            openQty = float(last_order['origQty'])
            msg = f'{self.symbol}: Open {"Long" if self.side == "BUY" else "Short"} Position Qty = {openQty} | Price = {trade_price}'
            show(msg)
            return trade_price, openQty

    def placeTP(self, price, qty):

        self.conf = getConfig()

        try:
            if self.side == 'BUY':
                side = 'SELL'
                target = price + (price * self.conf['Tp'] / 100)
            elif self.side == 'SELL':
                side = 'BUY'
                target = price - (price * self.conf['Tp'] / 100)

            target = self.precision(target, self.priceFilter)

            orderId = self.client.futures_create_order(symbol=self.symbol, side=side, type='LIMIT', price=target, quantity=qty, reduceOnly=True,
                                                       timeInForce='GTC', recvWindow=59990)['orderId']
            show(f'{self.symbol}: Place TP Price = {target}')
            return orderId
        except Exception as te:
            show(f'{self.symbol}: TP Error:> {te}')

    def placeSL(self, price, qty):

        self.conf = getConfig()

        try:

            if self.side == 'BUY':
                side = 'SELL'
                target = price - (price * self.conf['Sl'] / 100)
            elif self.side == 'SELL':
                side = 'BUY'
                target = price + (price * self.conf['Sl'] / 100)

            target = self.precision(target, self.priceFilter)
            orderId = self.client.futures_create_order(symbol=self.symbol, side=side, type='STOP', stopPrice=target, price=target, quantity=qty, reduceOnly=True,
                                                       timeInForce='GTC', recvWindow=59990)['orderId']
            show(f'{self.symbol}: Place SL Price = {target}')
            return orderId
        except Exception as se:
            show(f'{self.symbol}: SL Error:> {se}')

    def alert(self, conn):
        try:
            data = conn.recv(1024)
            alert_tv = None
            if data != b'':
                #try:
                    ndata = b'{' + data.split(b'{')[1]
                    alert_tv = json.loads(ndata)
                    show('\n')
                    show('=================Trade Open======================')
                    print(alert_tv)
            conn.close()
                # except:
                #     pass
        except:
            sys.exit()
        if not alert_tv:
            sys.exit()

        self.symbol = alert_tv['pair'].upper()
        self.side = alert_tv['side'].upper()
        self.conf = getConfig()
        self.qtyFilter, self.priceFilter = self.getFilters()

        # check for open position
        #self.closePosition()
        pos = float(self.client.futures_position_information(symbol=self.symbol)[0]['positionAmt'])

        
            # sedang tidak ada trade dan mulai calculate amount
            #else:
        currentBalance = self.getBalance()
        if self.balance is None:
            self.balance = currentBalance
        if (currentBalance > self.balance):
            pl = currentBalance - self.balance
            
            now = datetime.now()
            print(now)
            session_break = now.replace(hour=7, minute=0, second=0, microsecond=0)
            sleep_ = (timedelta(hours=24) - (now - session_break)).total_seconds() % (24 * 3600)
            if session_break < now:
                session_break = now.replace(now.year, now.month, now.day+1,hour=7, minute=0, second=0, microsecond=0)
                sleep_ = (timedelta(hours=24) - (now - session_break)).total_seconds() % (24 * 3600)
            print(f'Last Trade is Profit {pl} USDT')
            print(f'Bot Closed Until {session_break}')
            while now < session_break:
                sys.exit()
            if now > session_break:
                self.balance = currentBalance
                print ('Saldo Reseted')
        

        pl = self.getBalance() - self.balance
        
        
        if currentBalance >= self.balance:
            self.balance = currentBalance
            amount = self.conf['EntryMargin']

        else:
            amount = self.balance - currentBalance + self.conf['EntryMargin']
            if amount < self.conf['EntryMargin']:
                amount = self.conf['EntryMargin']
            if amount >= self.conf['MaxMargin']:
                amount = self.conf['MaxMargin']
            
        
        #logic di balik , logic ke 2 di taruh ke nomor 1 
        # if (self.side == 'BUY' and pos < 0.0) or (self.side == 'SELL' and pos > 0.0):
            
        #     self.closePosition()
        #     curPrice = float(self.pubclient.get_klines(symbol=self.symbol, interval='1m', limit=1)[0][4])
        #     qty = round(amount /(curPrice*0.0001) / 100, 3)
        #     openPrice, openQty = self.openPosition(qty)
        #     profitOrder = self.placeTP(openPrice, openQty)
        #     stopOrder = self.placeSL(openPrice, openQty)
        if (self.side == 'BUY' and pos > 0.0) or (self.side == 'SELL' and pos < 0.0):
            print('Lagi ada trade bro, ntar ya')
            sys.exit()
        else:
            try:
                self.closePosition()
                amount = self.balance - currentBalance + self.conf['EntryMargin']
            except:
                print('There is no trade bro.')
            
            show(f'Kondisi saat ini {currentBalance} - {self.balance} = {pl} USDT')
            show(f'Amount = {amount} USDT')
            curPrice = float(self.pubclient.get_klines(symbol=self.symbol, interval='1m', limit=1)[0][4])
            qty = round(amount /(curPrice*0.0001) / 100, 3)
            openPrice, openQty = self.openPosition(qty)

            profitOrder = self.placeTP(openPrice, openQty)
            stopOrder = self.placeSL(openPrice, openQty)

        threading.Thread(target=self.ordersCheck, args=(profitOrder, stopOrder), daemon=True).start()

    def start(self):

        try:
            self.s.bind(('0.0.0.0', self.port))            
            self.s.listen(1024)
            self.balance = self.getBalance()
            print(f'Saldo Pembukaan {self.balance}')
            print("Bot Started")
            while self.rn:
                try:
                    c, addr = self.s.accept()
                    threading.Thread(target=self.alert, args=(c,), daemon=True).start()
                except:
                    pass
        except Exception as see:
            print(f'Please Check Configuration!!\n{see}')
            time.sleep(5)

    def stop(self):
        self.rn = False
        self.s.close()
        print('Bot Stoped')


bot = Botser()
bot.start()
