# discount.py

class DiscountStrategy:
    def calculate_discount(self, price):
        pass

class NoDiscount(DiscountStrategy):
    def calculate_discount(self, price):
        return price

class PercentageDiscount(DiscountStrategy):
    def calculate_discount(self, price):
        if price > 1000:
            return price - (price * 0.10)
        elif price > 500:
            return price - (price * 0.05)
        return price

class SpecialDiscount(DiscountStrategy):
    def calculate_discount(self, price):
        if price > 2000:
            return price - (price * 0.15)
        return price

class BulkDiscount(DiscountStrategy):
    def calculate_discount(self, price, quantity):
        if price * quantity > 1500:
            return price - (price * 0.08)
        return price