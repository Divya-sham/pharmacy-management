# observer.py

from discount import DiscountStrategy, NoDiscount
from med_availability import AvailableState,NotAvailableState
from medicine import Medicine

class Observer:
    def update(self, message):
        pass

class AlertSystem(Observer):
    def __init__(self):
        self.salerts = []
        self.ealerts = []

    def update(self, message):
        print(f"Alert: {message}")
        self.salerts.append(message)
    
    def clear_salerts(self):
        self.salerts = []
    
    def clear_ealerts(self):
        self.ealerts = []
    
    def clear_alerts_for_medicine(self, medicine):
        # Filter out alerts related to the specified medicine
        self.ealerts = [alert for alert in self.ealerts if medicine.name not in alert]
