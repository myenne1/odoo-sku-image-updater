"""
This script is used to extract the item names from the image paths in the meta_legacy.csv file.
It then writes the item names to a new file called sku_item_names.txt.
"""
import csv
import os

# Input and output file paths
csv_path = "/Users/muhanadyennes/Documents/Documents - Muhanad’s MacBook Pro/Developer/Scraping-Project copy/meta_legacy.csv"
output_path = "/Users/muhanadyennes/Documents/Documents - Muhanad’s MacBook Pro/Developer/Scraping-Project copy/sku_item_names.txt"

def extract_item_name(img_path):
    # Get the filename without the directory
    filename = os.path.basename(img_path)
    # Remove the file extension
    name, _ = os.path.splitext(filename)
    # Replace dashes and underscores with spaces
    item_name = name.replace("-", " ").replace("_", " ")
    return item_name

with open(csv_path, newline='', encoding='utf-8') as csvfile, open(output_path, 'w', encoding='utf-8') as outfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        sku = row['sku']
        img_src = row['img_src']
        item_name = extract_item_name(img_src)
        outfile.write(f"Sku: {sku} | {item_name}\n")

print(f"Output written to {output_path}")
