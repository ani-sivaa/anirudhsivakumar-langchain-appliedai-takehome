"""
Test script to trigger the auto-heal loop.
This imports pandas which is likely not installed.
"""

import pandas as pd

# Create a simple dataframe
data = {"name": ["Alice", "Bob", "Charlie"], "age": [25, 30, 35]}
df = pd.DataFrame(data)

print("Auto-heal worked! Here's the dataframe:")
print(df)
print("\nSuccess! The agent automatically installed pandas and ran the script.")

