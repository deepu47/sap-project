import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'D:/my pc stuff/sap-ml project/sap-project/src'))

from classification import classify_abc_xyz
from replenishment_logic import calculate_reorder_point_advanced

# Set seed for reproducibility
np.random.seed(42)

# 1. Create Synthetic Demand History (for ABC/XYZ classification)
# SKU_AX: High value (100 avg), Stable (low std)
ax_demand = pd.DataFrame({'sku': 'SKU_AX', 'demand_qty': np.random.normal(100, 5, 100)})
# SKU_CZ: Low value (avg ~1), Erratic (lots of zeros, high CV)
cz_demand = pd.DataFrame({'sku': 'SKU_CZ', 'demand_qty': [0]*90 + [10]*10})

history = pd.concat([ax_demand, cz_demand])

# 2. Classify SKUs
sku_metadata = classify_abc_xyz(history)
print("--- Classification Results ---")
print(sku_metadata)

# 3. Create Forecast Data (Daily avg)
forecast_data = pd.DataFrame([
    {'sku': 'SKU_AX', 'site': 'DC1', 'forecast_qty': 100},
    {'sku': 'SKU_CZ', 'site': 'DC1', 'forecast_qty': 1}
])

# 4. Create Lead Time Data (Site-specific)
lt_data = pd.DataFrame([
    {'sku': 'SKU_AX', 'site': 'DC1', 'lt_avg': 3, 'sigma_lt': 0.1}, # Fast, reliable
    {'sku': 'SKU_CZ', 'site': 'DC1', 'lt_avg': 10, 'sigma_lt': 3.0} # Slow, unreliable
])

# 5. Calculate Advanced ROP
# We use a 1-day review period
rop_results = calculate_reorder_point_advanced(forecast_data, sku_metadata, lt_data, review_period_days=1)

print("\n--- Advanced ROP Results ---")
print(rop_results[['sku', 'abc_xyz_segment', 'z_score', 'safety_stock', 'reorder_point']])

# 6. Demonstration of Safety Stock Logic
print("\nAnalysis:")
print("- SKU_AX (High Value/Stable) has a high Z-score (1.96) for service, but low volatility keeps SS manageable.")
print("- SKU_CZ (Low Value/Erratic) has a lower Z-score (1.04) to save cost, but high lead-time volatility still forces a buffer.")
