import csv
import random
from datetime import datetime, timedelta

random.seed(42)

regions = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
categories = ["Electronics", "Furniture", "Office Supplies", "Software", "Cloud Services"]
products_by_category = {
    "Electronics": ["Smartphone Pro", "Wireless Headphones", "Ultra HD Monitor", "Mechanical Keyboard"],
    "Furniture": ["Ergonomic Chair", "Standing Desk", "Filing Cabinet", "Conference Table"],
    "Office Supplies": ["Ballpoint Pens (100pk)", "A4 Paper Reams", "Stapler Set", "Sticky Notes Box"],
    "Software": ["Analytics Suite Enterprise", "Security Firewall License", "Project Management Tool", "Design Studio Pro"],
    "Cloud Services": ["Compute Instances (Tier 1)", "Managed Storage 1TB", "API Gateway Pro", "CDN Acceleration"]
}
sales_channels = ["Direct Sales", "Online Portal", "Partner Reseller", "Retail"]

customers = [f"Cust_{100 + i}" for i in range(50)]
customer_names = [
    "Apex Global", "Beacon Logistics", "Cirrus Cloudworks", "Delta Holdings", "Epsilon Dynamics",
    "Falcon Systems", "GigaByte Solutions", "Horizon Media", "Iris Innovations", "Jupiter Retail",
    "Kestrel Capital", "Lumina Health", "Matrix Industrial", "Nexus Financial", "Orion Technologies",
    "Pinnacle Corp", "Quantum Software", "Radiant Energy", "Summit Enterprises", "Titan Manufacturing",
    "Vertex Labs", "Waveform Audio", "Zenith Media", "Acrobat Logistics", "Blaze Interactive"
]

rows = []
base_date = datetime(2023, 1, 1)

for i in range(1, 1001):
    order_id = f"ORD-{20230000 + i}"
    days_offset = random.randint(0, 700)
    order_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
    
    region = random.choice(regions)
    category = random.choice(categories)
    product = random.choice(products_by_category[category])
    
    cust_idx = random.randint(0, len(customer_names) - 1)
    customer_id = customers[cust_idx]
    customer_name = customer_names[cust_idx]
    
    quantity = random.randint(1, 40)
    unit_price = round(random.uniform(20.0, 1500.0), 2)
    
    discount = round(random.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.30]), 2)
    revenue = round(quantity * unit_price * (1 - discount), 2)
    cost = round(revenue * random.uniform(0.4, 0.75), 2)
    profit = round(revenue - cost, 2)
    
    if i in [142, 389, 715]:
        revenue = round(revenue * 8.5, 2)
        profit = round(profit * 8.5, 2)
    elif i in [220, 560]:
        profit = -round(revenue * 1.5, 2)
        
    rows.append({
        "order_id": order_id,
        "order_date": order_date,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "region": region,
        "category": category,
        "product_name": product,
        "sales_channel": random.choice(sales_channels),
        "quantity": quantity,
        "unit_price": unit_price,
        "discount": discount,
        "revenue": revenue,
        "cost": cost,
        "profit": profit
    })

fieldnames = list(rows[0].keys())
with open("/home/ankit/Desktop/Databack/sample_data/sales_data.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

cust_rows = []
for idx, name in enumerate(customer_names):
    cust_rows.append({
        "customer_id": customers[idx],
        "customer_name": name,
        "industry": random.choice(["Finance", "Healthcare", "Technology", "Retail", "Manufacturing", "Energy"]),
        "tier": random.choice(["Enterprise", "Mid-Market", "SMB"]),
        "country": random.choice(["United Kingdom", "United States", "Germany", "France", "Japan", "Australia"]),
        "signup_date": (base_date - timedelta(days=random.randint(100, 1000))).strftime("%Y-%m-%d"),
        "account_manager": random.choice(["Sarah Jenkins", "Alex Rivera", "David Chen", "Emily Watson", "Liam Smith"])
    })

with open("/home/ankit/Desktop/Databack/sample_data/customers.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(cust_rows[0].keys()))
    writer.writeheader()
    writer.writerows(cust_rows)
