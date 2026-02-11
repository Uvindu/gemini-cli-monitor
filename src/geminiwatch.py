#!/usr/bin/env python3
import argparse
import sys
import os
import time
import json
import csv
import db
from datetime import datetime

VERSION = "1.1.0"

def format_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)

def print_report():
    db.sync_from_gemini()
    stats = db.get_stats()
    model_counts = db.get_model_stats()
    recent = db.get_recent_requests(limit=10)

    # Quotas
    DAILY_TOKEN_QUOTA = 10_000_000 
    REQ_QUOTA_PER_MODEL = 500 # Approximation based on /stats
    
    print(f"\033[1;36mGeminiWatch v{VERSION} - Monitoring Report\033[0m")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Today's Stats
    today_total = stats['today_input_tokens'] + stats['today_output_tokens'] + stats['today_thought_tokens']
    quota_pct = (today_total / DAILY_TOKEN_QUOTA) * 100
    
    # Cost estimation (Flash-centric default)
    # Billable input = input - cached
    billable_in = max(0, stats['today_input_tokens'] - stats['today_cached_tokens'])
    cost_in = (billable_in / 1_000_000) * 0.10
    cost_cached = (stats['today_cached_tokens'] / 1_000_000) * 0.025
    cost_out = (stats['today_output_tokens'] / 1_000_000) * 0.40
    total_cost = cost_in + cost_cached + cost_out

    print(f"\033[1;33mToday's Usage:\033[0m")
    print(f"  Input:         {format_tokens(stats['today_input_tokens'])} (Billable: {format_tokens(billable_in)}, Cached: {format_tokens(stats['today_cached_tokens'])})")
    print(f"  Output:        {format_tokens(stats['today_output_tokens'])}")
    print(f"  Thoughts:      {format_tokens(stats['today_thought_tokens'])}")
    print(f"  Est. Cost:     ${total_cost:.4f}")
    
    quota_color = "\033[1;32m" if quota_pct < 80 else ("\033[1;33m" if quota_pct < 90 else "\033[1;31m")
    print(f"  Token Quota:   {quota_color}{quota_pct:.1f}%\033[0m (of {format_tokens(DAILY_TOKEN_QUOTA)})")
    
    print(f"\n\033[1;33mModel Request Usage (Today):\033[0m")
    print(f"{'Model':<25} {'Reqs':<10} {'Usage Left':<15}")
    print("-" * 50)
    for model, count in model_counts.items():
        used_pct = (count / REQ_QUOTA_PER_MODEL) * 100
        left_pct = max(0, 100 - used_pct)
        color = "\033[1;32m" if left_pct > 20 else "\033[1;31m"
        print(f"{model:<25} {count:<10} {color}{left_pct:.1f}%\033[0m")

    print(f"\n\033[1;33mTotal Usage:\033[0m")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Lifetime Tokens: {format_tokens(stats['total_input_tokens'] + stats['total_output_tokens'] + stats['total_thought_tokens'])}")
    
    print(f"\n\033[1;33mRecent Activity:\033[0m")
    print(f"{'Time':<20} {'Model':<20} {'In/Out/Cache':<20}")
    print("-" * 65)
    for r in recent:
        # row indices based on new schema:
        # 0:id, 1:ts, 2:session, 3:msg, 4:model, 5:in, 6:out, 7:cached, 8:thought, 9:total
        ts = r[1][:19].replace("T", " ")
        model = (r[4][:17] + "...") if len(r[4]) > 17 else r[4]
        tokens = f"{format_tokens(r[5])}/{format_tokens(r[6])}/{format_tokens(r[7])}"
        print(f"{ts:<20} {model:<20} {tokens:<20}")

def live_dashboard():
    try:
        while True:
            os.system('clear')
            print_report()
            print("\nRefreshing every 5s... (Ctrl+C to stop)")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nExiting dashboard.")

def main():
    parser = argparse.ArgumentParser(prog="geminiwatch", description="Monitor Gemini CLI usage")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show current usage report")
    subparsers.add_parser("dashboard", help="Start live monitoring dashboard")
    subparsers.add_parser("sync", help="Force sync from Gemini session files")
    
    exp = subparsers.add_parser("export", help="Export data")
    exp.add_argument("--format", choices=["json", "csv"], default="json")

    args = parser.parse_args()

    if args.command == "status" or args.command is None:
        print_report()
    elif args.command == "dashboard":
        live_dashboard()
    elif args.command == "sync":
        new = db.sync_from_gemini()
        print(f"Synced {new} new records.")
    elif args.command == "export":
        db.sync_from_gemini()
        stats = db.get_recent_requests(limit=10000)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(db.PROJECT_ROOT, "data", f"export_{timestamp}.{args.format}")
        
        with open(filename, 'w') as f:
            if args.format == 'json':
                data = []
                for r in stats:
                    data.append({
                        "timestamp": r[1],
                        "session_id": r[2],
                        "message_id": r[3],
                        "model": r[4],
                        "input_tokens": r[5],
                        "output_tokens": r[6],
                        "cached_tokens": r[7],
                        "thought_tokens": r[8],
                        "total_tokens": r[9]
                    })
                json.dump(data, f, indent=2)
            elif args.format == 'csv':
                writer = csv.writer(f)
                writer.writerow(["id", "timestamp", "session_id", "message_id", "model", "input", "output", "cached", "thought", "total"])
                writer.writerows(stats)
        
        print(f"Data exported to: {filename}")

if __name__ == "__main__":
    main()
