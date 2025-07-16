import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta

class EqualWeightScoringStrategy(bt.Strategy):
    def __init__(self):
        self.bought = False
        self.data_names = [d._name for d in self.datas]
        self.orders = []
        print(f"initial: {self.data_names}")

    def next(self):
        if not self.bought:
            total_value = self.broker.getvalue()
            weight = 1.0 / len(self.datas)
            print(f"first day: ${total_value:,.2f}, weight: {weight:.2%}")
            

            self.orders = []
            
            for i, d in enumerate(self.datas):
                current_price = d.close[0]
                print(f"check {d._name}: price={current_price}")
                
                if current_price > 0 and not pd.isna(current_price):  
                    target_value = total_value * weight
                    size = int(target_value / current_price)  
                    
                    if size > 0:
                        order = self.buy(data=d, size=size)
                        self.orders.append(order)
                        actual_value = size * current_price
                        print(f"buy {d._name}: price=${current_price:.2f}, quantity={size}, price=${actual_value:,.2f}")
                    else:
                        print(f" {d._name} 0")
                else:
                    print(f" {d._name} price fail: {current_price}")
            
            self.bought = True
        
        
        if len(self.datas) > 0:
            current_date = self.datas[0].datetime.date(0)
            total_value = self.broker.getvalue()
            cash = self.broker.getcash()
            
            if hasattr(self, 'last_print_date') and self.last_print_date == current_date:
                return
            self.last_print_date = current_date
            
            
            position_value = 0
            for d in self.datas:
                pos = self.getposition(d)
                if pos.size > 0:
                    pos_value = pos.size * d.close[0]
                    position_value += pos_value
                    print(f"  {d._name}: have{pos.size}shares, price${d.close[0]:.2f}, value${pos_value:,.2f}")
            
            print(f"{current_date}: total=${total_value:,.2f}, cash=${cash:,.2f}, values=${position_value:,.2f}")