#!/usr/bin/env python3
"""
Export git history of pricing data to JSON files suitable for static web hosting.
Generates one JSON file per item with complete price history.
"""

import git
import json
import datetime
import os
from pathlib import Path
from collections import defaultdict

def export_price_history(repo_path='.',
                         file_path='horde.json',
                         start_date=None,
                         output_dir='prices/history'):
    """
    Export price history from git commits.
    
    Args:
        repo_path: Path to git repository
        file_path: Path to JSON file within repo
        start_date: Start date for history (datetime.datetime). None = all history
        output_dir: Output directory for price history JSON files
    """
    
    if start_date is None:
        start_date = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    
    print(f"Exporting price history from {repo_path}/{file_path}")
    print(f"Start date: {start_date}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Open repository
    repo = git.Repo(repo_path)
    
    # Dictionary to store price history by item ID
    price_history = defaultdict(list)
    item_info = {}
    
    # Iterate through commits
    commit_count = 0
    for commit in repo.iter_commits('main', paths=file_path):
        commit_date = commit.committed_datetime.replace(tzinfo=datetime.timezone.utc)
        
        if commit_date >= start_date:
            commit_count += 1
            try:
                # Get file content at this commit
                blob = commit.tree / file_path
                file_content = blob.data_stream.read().decode('utf-8')
                data = json.loads(file_content)
                
                # Process each item
                for item in data.get('pricing_data', []):
                    item_id = item.get('itemId')
                    
                    # Store item info
                    if item_id not in item_info:
                        item_info[item_id] = {
                            'itemId': item_id,
                            'itemName': item.get('itemName', 'Unknown')
                        }
                    
                    # Store price point
                    price_history[item_id].append({
                        'date': commit_date.isoformat(),
                        'timestamp': int(commit_date.timestamp()),
                        'minBuyout': item.get('minBuyout'),
                        'marketValue': item.get('marketValue'),
                        'quantity': item.get('quantity'),
                        'numAuctions': item.get('numAuctions')
                    })
                    
            except Exception as e:
                print(f"Error processing commit {commit.hexsha}: {e}")
    
    print(f"Processed {commit_count} commits")
    
    # Write price history files
    files_written = 0
    for item_id in sorted(price_history.keys()):
        # Sort by date
        prices = sorted(price_history[item_id], key=lambda x: x['date'])
        
        # Remove duplicates (same date and same price)
        unique_prices = []
        prev_price = None
        for price_point in prices:
            current = (price_point['date'], price_point['minBuyout'])
            if current != prev_price:
                unique_prices.append(price_point)
                prev_price = current
        
        # Create output data
        output_data = {
            'itemId': item_id,
            'itemName': item_info[item_id]['itemName'],
            'priceHistory': unique_prices,
            'dataPoints': len(unique_prices),
            'dateRange': {
                'start': unique_prices[0]['date'] if unique_prices else None,
                'end': unique_prices[-1]['date'] if unique_prices else None
            }
        }
        
        # Write file
        output_file = os.path.join(output_dir, f'{item_id}.json')
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        files_written += 1
        if files_written % 100 == 0:
            print(f"  Written {files_written} files...")
    
    print(f"\nSuccessfully exported {files_written} items to {output_dir}/")
    
    # Create index file listing all items
    index_data = {
        'totalItems': len(item_info),
        'items': [
            {
                'itemId': item_id,
                'itemName': item_info[item_id]['itemName'],
                'dataFile': f'{item_id}.json'
            }
            for item_id in sorted(item_info.keys())
        ]
    }
    
    index_file = os.path.join(output_dir, 'index.json')
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"Created index file: {index_file}")

if __name__ == '__main__':
    # Export with default settings
    export_price_history()
    
    # Or customize:
    # export_price_history(
    #     repo_path='.',
    #     file_path='horde.json',
    #     start_date=datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc),
    #     output_dir='prices/history'
    # )
