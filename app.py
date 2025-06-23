from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from indicator import Observer, AlertSystem
from datetime import datetime,timedelta
from discount import PercentageDiscount,SpecialDiscount,BulkDiscount
from get_med import MedicineFactory, AntibioticsFactory, PainkillersFactory
from flask_sqlalchemy import SQLAlchemy
from medicine import Medicine
from dateutil.relativedelta import relativedelta
from medicinedb import MedicineDB,SaleDB
from extensions import db
import json,os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','default-key')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharmacy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db.init_app(app)
with app.app_context():
    db.create_all()
    print("Database path:", os.path.abspath("pharmacy.db"))

##Testing sqlalchemy table
@app.route('/list_medicines')
def list_medicines():
    meds = MedicineDB.query.all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'stock': m.stock,
        'price': m.price,
        'expiration_date': m.expiration_date,
        'category':m.category
    } for m in meds])


def load_medicines_data():
    data={}
    all_medicines=MedicineDB.query.all()

    for med in all_medicines:
        if med.category == 'antibiotics':
            factory = AntibioticsFactory()
        elif med.category == 'painkillers':
            factory = PainkillersFactory()
        else:
            factory = MedicineFactory()
    
        if med.price > 2000:
            discount_strategy =SpecialDiscount() 
        elif med.price > 1500:
            discount_strategy =BulkDiscount() 
        else:
            discount_strategy = PercentageDiscount()
        medicine_object = factory.create_medicine(med.name, med.stock, med.price, med.expiration_date, discount_strategy=discount_strategy)
        data[med.name] = medicine_object
    return data

with app.app_context():
    db.create_all()
    print("Database path:",os.path.abspath("pharmacy.db"))
    medicines_data = load_medicines_data()

customer_data = {}

# Initialize Alert System
alert_system = AlertSystem()

# Add the alert system as an observer for each medicine
for medicine in medicines_data.values():
    medicine.add_stockobserver(alert_system)
    medicine.add_expiryobserver(alert_system)

# Function to calculate total sales for a given time period
def calculate_total_sales(sales_data):
    return sum(entry['total_amount'] for entry in sales_data)

def calculate_total_stock(stock_data):
    return sum(entry.stock for entry in stock_data.values())

# Function to record daily sales
def record_daily_sale(customer_name, phone_number, medicine_name, quantity, price):
    if phone_number not in customer_data:
        customer_data[phone_number] = customer_name

    new_sale = SaleDB(
       customer_name = customer_name,
       phone_number = phone_number,
       doctor_name = session.get('doctor_name',''),
       medicine_name=medicine_name,
       quantity = quantity,
       price_per_unit = price,
       total_amount = quantity * price
    )
    db.session.add(new_sale)
    db.session.commit()


# Route for the index page
@app.route('/')
def index():
    all_medicines = MedicineDB.query.all()
    total_stock = sum(m.stock for m in all_medicines)

    today = datetime.today().date()
    soon = today+timedelta(days=30)
    expiring_soon = [m for m in all_medicines if today <= m.expiration_date <=soon]
    low_stock = [m for m in all_medicines if m.stock < 10]

    return render_template('index.html',total_stock=total_stock,expiring_count=len(expiring_soon),low_stock_count=len(low_stock))


@app.route('/customer_details', methods=['GET', 'POST'])
def customer_details():
    if request.method == 'POST':
        session['customer_name'] = request.form.get('customer_name')
        session['phone_number'] = request.form.get('phone_number')
        session['doctor_name'] = request.form.get('doctor_name')
        alert_system.clear_salerts()
        return redirect(url_for('medicine_details'))

    return render_template('customer_details.html')

# Route for selecting medicine details and inputting quantities
@app.route('/medicine_details', methods=['GET', 'POST'])
def medicine_details():
    # Access the alerts from the alert system
    stock_alerts = []
    sold_items = session.get('sold_items', [])
    all_medicines=MedicineDB.query.all()

    if request.method == 'POST':
        for med in all_medicines:
            quantity = request.form.get(f'quantity_{med.name}')
            
            if quantity and quantity.isdigit():
                quantity = int(quantity)
                if med.stock >= quantity:
                    medicine_obj = medicines_data.get(med.name)
                    if medicine_obj:
                        medicine_obj.update_stock(-quantity)

                    med.stock-=quantity
                    db.session.commit()

                    original_price = quantity * med.price
                    discounted_price =original_price

                    sold_items.append({
                        'name': med.name,
                        'quantity':quantity,
                        'original_price': original_price,
                        'discounted_price': discounted_price
                    })
                    record_daily_sale(
                        session.get('customer_name', ''),
                        session.get('phone_number', ''),
                        med.name,
                        quantity,
                        discounted_price
                    )
                else:
                    stock_alerts.append(f"Not enough stock for {med.name}.")

        if not stock_alerts:
            session['sold_items'] = sold_items.copy()
            return redirect(url_for('generate_invoice'))
    
    return render_template('medicine_details.html', medicines=all_medicines, alerts=stock_alerts)

# Route for adding or updating medicine
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name')
        stock = int(request.form.get('stock'))
        price = float(request.form.get('price'))
        expiration_date = datetime.strptime(request.form.get('expiration_date'), '%Y-%m-%d')
        category = request.form.get('category', 'Default')

       
        med= MedicineDB.query.filter_by(name=medicine_name).first()
        if med:
            med.stock+= stock
            med.price = price
            med.expiration_date = expiration_date
        else:
            med=MedicineDB(
                name=medicine_name,
                stock=stock,
                price=price,
                expiration_date=expiration_date,
                category=category
            )
            db.session.add(med)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('add_medicine.html')

@app.route('/delete_medicine/<int:medicine_id>',methods=['POST'])
def delete_medicine(medicine_id):
    medicine = MedicineDB.query.get(medicine_id)
    db.session.delete(medicine)
    db.session.commit()
    return redirect(url_for('maintain_stock'))

@app.route('/edit_medicine/<int:medicine_id>',methods=['GET','POST'])
def edit_medicine(medicine_id):
    medicine=MedicineDB.query.get(medicine_id)
    if request.method=='POST':
       medicine.name = request.form['name']
       medicine.stock = int(request.form['stock'])

       date_str = request.form['expiration_date']
       medicine.expiration_date = datetime.strptime(date_str,'%Y-%m-%d').date()
       db.session.commit()
       return redirect(url_for('maintain_stock'))
    return render_template('edit_medicine.html',medicine=medicine)
 

# Route for generating invoices
@app.route('/generate_invoice')
def generate_invoice():
    total_amount = 0

    # Retrieve sold_items from the session and clear it
    sold_items = session.pop('sold_items', [])

    # Calculate total_amount only if there are sold_items
    if sold_items:
        for item in sold_items:
            if item['discounted_price']:
                total_amount+=item['discounted_price']
            else:
                total_amount+=item['original_price']

    # Get customer_name and phone_number from query parameters
    customer_name = session.get('customer_name', '')
    phone_number = session.get('phone_number', '')
    doctor_name = session.get('doctor_name', '')
    return render_template('invoice.html', sold_items=sold_items, total_amount=total_amount, customer_name=customer_name, phone_number=phone_number,doctor_name=doctor_name)

@app.route('/reports')
def reports():
    return render_template('reports.html')

# Route for the daily sales report
@app.route('/daily_report')
def daily_report():
    today = datetime.now().date()
    sales = SaleDB.query.filter(db.func.date(SaleDB.timestamp)==today)
    total_stock = calculate_total_stock(medicines_data)
    return render_template('daily_report.html', title='Daily Report', sales=sales, total_stock=total_stock)

@app.route('/weekly_report')
def weekly_report():
    start_date = datetime.now()-relativedelta(months=3)
    end_date = datetime.now()

    weekly_data= []
    current_date = start_date
    while current_date <= end_date:
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start+timedelta(days=6)

        sales = SaleDB.query.filter(
            SaleDB.timestamp >= week_start,
            SaleDB.timestamp <= week_end
        ).all()

        total_sales = sum(s.total_amount for s in sales)

        weekly_data.append({
            'start_date':week_start.strftime('%Y-%m-%d'),
            'end_date':week_end.strftime('%Y-%m-%d'),
            'total_sales':total_sales
        })
        current_date = week_end+timedelta(days=1)
    # Pass the generated data to the template
    return render_template('weekly_report.html', title='Weekly Report', sales_data=weekly_data)

@app.route('/monthly_report')
def monthly_report():
    start_date = datetime.now()-relativedelta(months=6)
    end_date = datetime.now()

    monthly_data= []
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        next_month = (month_start.replace(day=28)+timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)


        sales = SaleDB.query.filter(
            SaleDB.timestamp >= month_start,
            SaleDB.timestamp <= month_end
        ).all()

        total_sales = sum(s.total_amount for s in sales)

        monthly_data.append({
            'month':month_start.strftime('%Y-%m'),
            'total_sales':total_sales
        })
        current_date = next_month

    # Pass the generated data to the template
    return render_template('monthly_report.html', title='Monthly Report', sales_data=monthly_data)

# Route for the annual report
@app.route('/annual_report')
def annual_report():
    current_year = datetime.now().year
    year_start = datetime(current_year,1,1)
    year_end = datetime(current_year,12,31)

    sales = SaleDB.query.filter(
        SaleDB.timestamp>=year_start,
        SaleDB.timestamp<=year_end
    ).all()

    total_sales = sum(s.total_amount for s in sales)
    annual_data = [{
        'year':current_year,
        'total_sales':total_sales
    }]

    # Pass the generated data to the template
    return render_template('annual_report.html', title='Annual Report', sales_data=annual_data)

def get_all_medicines_details_from_dict(medicines_data):
    medicines_details = {}
    for medicine_name, medicine in medicines_data.items():
        medicines_details[medicine_name] = {
            'Availability': medicine.display_state(),
            'Stock':medicine.stock,
            'Expiration_date': medicine.expiration_date.strftime('%Y-%m-%d')
        }
    return medicines_details

@app.route('/maintain_stock')
def maintain_stock():
    alert_system.clear_ealerts()
    medicines_data=load_medicines_data()

    for medicine in medicines_data.values():
        if medicine.expiration_date:
           medicine.check_expiration()
    all_medicines = MedicineDB.query.all()
    return render_template('maintain_stock.html', medicines_details=all_medicines,alerts=alert_system.ealerts)

if __name__ == '__main__':
    app.run(debug=True)
