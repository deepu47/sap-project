import pandas as pd
import os
from functools import lru_cache

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

@lru_cache(maxsize=1)
def get_orders_data():
    path = os.path.join(DATA_DIR, 'Orders_and_shipments.csv')
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path, encoding='latin1')
    # Strip whitespace from column names just in case
    df.columns = df.columns.str.strip()
    
    # We want to aggregate by Product Name and Date (Order Year, Order Month, Order Day)
    if 'Order Year' not in df.columns or 'Product Name' not in df.columns:
        return []
        
    df['date'] = pd.to_datetime(
        df['Order Year'].astype(str) + '-' + 
        df['Order Month'].astype(str) + '-' + 
        df['Order Day'].astype(str), 
        errors='coerce'
    )
    df = df.dropna(subset=['date', 'Product Name', 'Order Quantity'])
    
    # Group by Product Name and Date, sum Order Quantity
    agg_df = df.groupby(['Product Name', 'date'])['Order Quantity'].sum().reset_index()
    agg_df = agg_df.rename(columns={'Product Name': 'sku', 'Order Quantity': 'demand_qty'})
    
    # Format date as YYYY-MM-DD
    agg_df['date'] = agg_df['date'].dt.strftime('%Y-%m-%d')
    
    # Get top 5 products by total demand for the demo to avoid loading too much
    top_products = agg_df.groupby('sku')['demand_qty'].sum().nlargest(5).index
    agg_df = agg_df[agg_df['sku'].isin(top_products)]
    
    # Sort by date
    agg_df = agg_df.sort_values(by=['sku', 'date'])
    
    return agg_df.to_dict(orient='records')

@lru_cache(maxsize=1)
def get_inventory_data():
    path = os.path.join(DATA_DIR, 'Inventory.csv')
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    
    # Get the latest 'Year Month' for each product to show current inventory
    df = df.sort_values(by=['Year Month'], ascending=False)
    latest_inv = df.drop_duplicates(subset=['Product Name'])
    
    # Pick top 20 for the UI
    latest_inv = latest_inv.head(20)
    
    return latest_inv[['Product Name', 'Warehouse Inventory', 'Inventory Cost Per Unit']].to_dict(orient='records')

@lru_cache(maxsize=1)
def get_fulfillment_data():
    path = os.path.join(DATA_DIR, 'Fulfillment.csv')
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    
    # Pick top 20 for UI
    df = df.head(20)
    
    # Rename column for easier access in JS
    if 'Warehouse Order Fulfillment (days)' in df.columns:
         df = df.rename(columns={'Warehouse Order Fulfillment (days)': 'fulfillment_days'})
         
    return df[['Product Name', 'fulfillment_days']].to_dict(orient='records')
