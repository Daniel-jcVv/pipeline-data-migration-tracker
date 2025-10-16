"""Generate test csv files for pipeline testing."""

import os
import csv
from datetime import datetime, timedelta
import random

OUTPUT_DIR = 'data/raw'
os.makedirs(OUTPUT_DIR, exist_ok=True)

customers = [f'CUST_{i:05d}' for i in range(1, 101)]
regions = ['NORTH', 'SOUTH', 'EAST', 'WEST']
products = [f'PROD_{i:03d}' for i in range(1, 51)]


def generate_orders_csv(filename, num_rows=1000):
    filepath = os.path.join(OUTPUT_DIR, filename)
    base_date = datetime(2024, 1, 1)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'order_id', 'customer_id', 'order_date', 'region', 
            'product_id', 'quantity', 'unit_price', 'total_amount'
        ])
        writer.writeheader()
        for i in range(num_rows):
            order_date = base_date + timedelta(days=random.randint(0, 90))
            quantity = random.randint(1, 100)
            unit_price = round(random.uniform(10, 1000), 2)
            writer.writerow({
                'order_id': f'ORD_{i:06d}',
                'customer_id': random.choice(customers),
                'order_date': order_date.strftime('%Y-%m-%d'),
                'region': random.choice(regions),
                'product_id': random.choice(products),
                'quantity': quantity,
                'unit_price': unit_price,
                'total_amount': round(quantity * unit_price, 2)
            })
    print(f"✓ {filename} ({num_rows} rows)")

def generate_sales_csv(filename, num_rows=500):
    filepath = os.path.join(OUTPUT_DIR, filename)
    base_date = datetime(2024, 1, 1)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'sale_id', 'date', 'region', 'sales_amount', 'discount', 'net_sales'
        ])
        writer.writeheader()
        for i in range(num_rows):
            sale_date = base_date + timedelta(days=random.randint(0, 90))
            sales = round(random.uniform(100, 5000), 2)
            discount = round(random.uniform(0, 0.2) * sales, 2)
            writer.writerow({
                'sale_id': f'SALE_{i:05d}',
                'date': sale_date.strftime('%Y-%m-%d'),
                'region': random.choice(regions),
                'sales_amount': sales,
                'discount': discount,
                'net_sales': round(sales - discount, 2)
            })
    print(f"✓ {filename} ({num_rows} rows)")

def generate_customers_csv(filename, num_rows=200):
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'customer_id', 'name', 'email', 'region', 'signup_date'
        ])
        writer.writeheader()
        for i in range(num_rows):
            signup_date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
            writer.writerow({
                'customer_id': f'CUST_{i:05d}',
                'name': f'Customer_{i}',
                'email': f'customer_{i}@example.com',
                'region': random.choice(regions),
                'signup_date': signup_date.strftime('%Y-%m-%d')
            })
    print(f"✓ {filename} ({num_rows} rows)")

if __name__ == '__main__':
    print("Generating 40 test CSV files...\n")
    
    for month in range(1, 13):
        for week in range(1, 3):
            generate_orders_csv(f'orders_2024_{month:02d}_w{week}.csv', 800)
    
    for quarter in range(1, 5):
        for month in range(1, 3):
            generate_sales_csv(f'sales_q{quarter}_m{month}.csv', 600)
    
    for batch in range(1, 6):
        generate_customers_csv(f'customers_batch_{batch}.csv', 150)
    
    print(f"\n✅ 40 files created in {OUTPUT_DIR}")
