from discount import PercentageDiscount
class MedicineFactory:
    def create_medicine(self, name, stock, price, expiration_date,discount_strategy=None):
        raise NotImplementedError

class AntibioticsFactory(MedicineFactory):
    def create_medicine(self, name, stock, price, expiration_date,discount_strategy=None):
        from medicine import Medicine
        return Medicine(name, stock, price, expiration_date, category='Antibiotics',discount_strategy=discount_strategy)

class PainkillersFactory(MedicineFactory):
    def create_medicine(self, name, stock, price, expiration_date,discount_strategy=None):
        from medicine import Medicine
        return Medicine(name, stock, price, expiration_date, category='Painkillers',discount_strategy=discount_strategy)
