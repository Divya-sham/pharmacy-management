from discount import NoDiscount
from med_availability import AvailableState,NotAvailableState
from datetime import datetime, timedelta

class Medicine:
    def __init__(self, name, stock, price, expiration_date,category,discount_strategy=None):
        self.name = name
        self.stock = stock
        self.price = price
        self.expiration_date = expiration_date
        self.category=category
        self.discount_strategy = discount_strategy or NoDiscount()
        self.state = AvailableState() if stock > 0 else NotAvailableState()
        self.stockobservers = []
        self.expiryobservers = []

    def add_stockobserver(self, observer):
        self.stockobservers.append(observer)

    def remove_stockobserver(self, observer):
        self.stockobservers.remove(observer)

    def notify_stockobservers(self, message):
        for observer in self.stockobservers:
            observer.update(message)
    
    def add_expiryobserver(self, observer):
        self.expiryobservers.append(observer)

    def remove_expiryobserver(self, observer):
        self.expiryobservers.remove(observer)

    def notify_expiryobservers(self, message):
        for observer in self.expiryobservers:
            observer.update(message)

    def update_stock(self, quantity):
        self.stock += quantity
        if self.stock <= 0:
            self.notify_stockobservers(f"Alert: {self.name} is out of stock!")
            self.set_state(NotAvailableState())
        else:
            self.set_state(AvailableState())

    def check_expiration(self):
        today = datetime.now().date()
        if self.expiration_date - today < timedelta(days=30):
            self.notify_expiryobservers(f"Alert: {self.name} is about to expire!")
    
    def calculate_discounted_price(self,qty):
        total_price = self.price * qty
        return self.discount_strategy.calculate_discount(total_price)

    def apply_discount_strategy(self, discount_strategy):
        self.discount_strategy = discount_strategy

    @property
    def has_discount(self):
        return bool(self.discount_strategy)
    
    def set_state(self, state):
        self.state = state

    def display_state(self):
        return self.state.display_state()
    
    def create_medicine(self,  category_factory):
        return category_factory.create_medicine(self.name, self.stock, self.price, self.expiration_date,discount_strategy=self.discount_strategy
        )