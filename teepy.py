import pandas as pd
import sys
import os

def convert_excel_to_json(excel_path, json_path=None):
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)

        # Define default JSON output path
        if json_path is None:
            json_path = os.path.splitext(excel_path)[0] + '.json'

        # Convert to JSON and save
        df.to_json(json_path, orient='records', indent=4)
        print(f"✅ Successfully converted '{excel_path}' to '{json_path}'")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    
    convert_excel_to_json('cs.xlsx', 'cs.json')
