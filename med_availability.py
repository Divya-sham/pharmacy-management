class MedicineState:
    def display_state(self):
        pass

class AvailableState(MedicineState):
    def display_state(self):
        return "Available"

class NotAvailableState(MedicineState):
    def display_state(self):
        return "Not available"