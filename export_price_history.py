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
from statistics import mean, stdev

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
    
    # Generate frontpage statistics
    generate_statistics(output_dir, price_history, item_info)

def generate_statistics(output_dir, price_history, item_info):
    """
    Generate cool statistics for the frontpage.
    
    Args:
        output_dir: Directory containing price history files
        price_history: Dictionary of item_id -> list of price points
        item_info: Dictionary of item_id -> item metadata
    """
    print("\nGenerating frontpage statistics...")
    
    stats = {
        'generatedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'marketSummary': {},
        'topExpensive': [],
        'topGainers': [],
        'topLosers': [],
        'mostVolatile': [],
        'mostTraded': [],
        'recentTrends': {}
    }
    
    # Calculate statistics for each item
    item_stats = {}
    total_market_value = 0
    total_quantity = 0
    total_auctions = 0
    
    for item_id, prices in price_history.items():
        if not prices:
            continue
        
        # Sort by date
        sorted_prices = sorted(prices, key=lambda x: x['date'])
        latest = sorted_prices[-1]
        earliest = sorted_prices[0]
        
        # Calculate metrics
        current_price = latest.get('marketValue') or latest.get('minBuyout', 0)
        earliest_price = earliest.get('marketValue') or earliest.get('minBuyout', 0)
        
        # Price change percentage
        price_change_pct = 0
        if earliest_price > 0:
            price_change_pct = ((current_price - earliest_price) / earliest_price) * 100
        
        # Volatility (standard deviation of prices)
        price_values = [p.get('marketValue') or p.get('minBuyout', 0) for p in sorted_prices if p.get('marketValue') or p.get('minBuyout')]
        volatility = 0
        if len(price_values) > 1:
            try:
                volatility = stdev(price_values)
            except:
                volatility = 0
        
        # Total traded quantity
        total_qty = sum(p.get('quantity', 0) for p in sorted_prices)
        total_auc = sum(p.get('numAuctions', 0) for p in sorted_prices)
        
        item_stats[item_id] = {
            'itemId': item_id,
            'itemName': item_info[item_id]['itemName'],
            'currentPrice': current_price,
            'earliestPrice': earliest_price,
            'priceChangePct': price_change_pct,
            'volatility': volatility,
            'totalQuantity': total_qty,
            'totalAuctions': total_auc,
            'dataPoints': len(sorted_prices)
        }
        
        total_market_value += current_price
        total_quantity += total_qty
        total_auctions += total_auc
    
    # Market summary
    stats['marketSummary'] = {
        'totalItems': len(item_stats),
        'totalMarketValue': total_market_value,
        'averagePrice': total_market_value / len(item_stats) if item_stats else 0,
        'totalQuantityTraded': total_quantity,
        'totalAuctions': total_auctions
    }
    
    # Top 10 most expensive
    stats['topExpensive'] = sorted(
        item_stats.values(),
        key=lambda x: x['currentPrice'],
        reverse=True
    )[:10]
    
    # Top 10 biggest gainers
    stats['topGainers'] = sorted(
        [x for x in item_stats.values() if x['priceChangePct'] > 0],
        key=lambda x: x['priceChangePct'],
        reverse=True
    )[:10]
    
    # Top 10 biggest losers
    stats['topLosers'] = sorted(
        [x for x in item_stats.values() if x['priceChangePct'] < 0],
        key=lambda x: x['priceChangePct']
    )[:10]
    
    # Most volatile
    stats['mostVolatile'] = sorted(
        item_stats.values(),
        key=lambda x: x['volatility'],
        reverse=True
    )[:10]
    
    # Most traded (by quantity)
    stats['mostTraded'] = sorted(
        item_stats.values(),
        key=lambda x: x['totalQuantity'],
        reverse=True
    )[:10]
    
    # Recent trends (7-day and 30-day changes)
    now = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago = now - datetime.timedelta(days=7)
    thirty_days_ago = now - datetime.timedelta(days=30)
    
    recent_stats = {'sevenDay': [], 'thirtyDay': []}
    
    for item_id, item_stat in item_stats.items():
        prices = price_history[item_id]
        
        # 7-day trend
        recent_7d = [p for p in prices if datetime.datetime.fromisoformat(p['date']) >= seven_days_ago]
        if len(recent_7d) >= 2:
            start_7d = recent_7d[0].get('marketValue') or recent_7d[0].get('minBuyout', 0)
            end_7d = recent_7d[-1].get('marketValue') or recent_7d[-1].get('minBuyout', 0)
            if start_7d > 0:
                change_7d = ((end_7d - start_7d) / start_7d) * 100
                recent_stats['sevenDay'].append({
                    'itemId': item_id,
                    'itemName': item_stat['itemName'],
                    'changePct': change_7d,
                    'startPrice': start_7d,
                    'endPrice': end_7d
                })
        
        # 30-day trend
        recent_30d = [p for p in prices if datetime.datetime.fromisoformat(p['date']) >= thirty_days_ago]
        if len(recent_30d) >= 2:
            start_30d = recent_30d[0].get('marketValue') or recent_30d[0].get('minBuyout', 0)
            end_30d = recent_30d[-1].get('marketValue') or recent_30d[-1].get('minBuyout', 0)
            if start_30d > 0:
                change_30d = ((end_30d - start_30d) / start_30d) * 100
                recent_stats['thirtyDay'].append({
                    'itemId': item_id,
                    'itemName': item_stat['itemName'],
                    'changePct': change_30d,
                    'startPrice': start_30d,
                    'endPrice': end_30d
                })
    
    # Sort and limit recent trends
    recent_stats['sevenDay'] = sorted(recent_stats['sevenDay'], key=lambda x: x['changePct'], reverse=True)[:10]
    recent_stats['thirtyDay'] = sorted(recent_stats['thirtyDay'], key=lambda x: x['changePct'], reverse=True)[:10]
    stats['recentTrends'] = recent_stats
    
    # Write statistics file
    stats_file = os.path.join(output_dir, 'statistics.json')
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Created statistics file: {stats_file}")
    print(f"  - Total items tracked: {stats['marketSummary']['totalItems']}")
    print(f"  - Total market value: {stats['marketSummary']['totalMarketValue']:,.0f}")
    print(f"  - Average price: {stats['marketSummary']['averagePrice']:,.0f}")


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
