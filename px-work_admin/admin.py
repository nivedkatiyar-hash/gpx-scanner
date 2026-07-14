#!/usr/bin/env python3
"""
gpx-admin: Automated client administration for developers.
Tracks time, generates status reports, and builds invoices instantly.
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Paths
ADMIN_DIR = Path.home() / ".local" / "share" / "gpx" / "admin"

# UI Colors
C_GREEN = "\033[92m"
C_BLUE = "\033[94m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"

def get_client_file(client_name):
    return ADMIN_DIR / f"{client_name.lower().replace(' ', '_')}.json"

def init_client(name):
    """Creates a new client tracking file."""
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)
    file_path = get_client_file(name)
    
    if file_path.exists():
        print(f"{C_YELLOW}Client '{name}' already exists.{C_RESET}")
        sys.exit(1)
        
    data = {
        "client_name": name,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "logs": []
    }
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"{C_GREEN}✔ Client workspace for '{name}' initialized!{C_RESET}")

def log_work(name, hours, task):
    """Logs time and task descriptions to the client file."""
    file_path = get_client_file(name)
    if not file_path.exists():
        print(f"{C_YELLOW}Client '{name}' not found. Run 'init' first.{C_RESET}")
        sys.exit(1)
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "hours": float(hours),
        "task": task,
        "billed": False
    }
    
    data["logs"].append(entry)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"{C_GREEN}✔ Logged {hours}h for '{name}': {task}{C_RESET}")

def generate_report(name):
    """Auto-generates a professional status email based on unbilled work."""
    file_path = get_client_file(name)
    if not file_path.exists():
        print(f"{C_YELLOW}Client '{name}' not found.{C_RESET}")
        sys.exit(1)
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    unbilled_logs = [log for log in data["logs"] if not log.get("billed")]
    
    if not unbilled_logs:
        print(f"{C_BLUE}No new updates to report for {name}.{C_RESET}")
        return

    print(f"\n{C_DIM}--- COPY AND PASTE THIS EMAIL ---{C_RESET}\n")
    print(f"Subject: Project Update - {name} - {datetime.now().strftime('%b %d')}\n")
    print(f"Hi Team,\n")
    print("Here is a quick summary of the work completed recently:\n")
    
    total_hours = 0
    for log in unbilled_logs:
        print(f"  • {log['task']} ({log['hours']}h)")
        total_hours += log['hours']
        
    print(f"\nTotal hours this cycle: {total_hours}h")
    print("\nLet me know if you have any questions or priorities for next week.")
    print("\nBest regards,")
    print("[Your Name]")
    print(f"\n{C_DIM}---------------------------------{C_RESET}\n")

def generate_invoice(name, rate, mark_billed):
    """Calculates unbilled hours, generates an invoice, and optionally marks as billed."""
    file_path = get_client_file(name)
    if not file_path.exists():
        print(f"{C_YELLOW}Client '{name}' not found.{C_RESET}")
        sys.exit(1)
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    unbilled_logs = [log for log in data["logs"] if not log.get("billed")]
    
    if not unbilled_logs:
        print(f"{C_BLUE}No unbilled hours found for {name}.{C_RESET}")
        return
        
    total_hours = sum(log['hours'] for log in unbilled_logs)
    total_due = total_hours * rate
    
    print(f"\n{C_BLUE}===================================={C_RESET}")
    print(f"{C_BLUE}              INVOICE               {C_RESET}")
    print(f"{C_BLUE}===================================={C_RESET}")
    print(f"Client: {name}")
    print(f"Date:   {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Rate:   ${rate:.2f} / hr")
    print(f"{C_BLUE}------------------------------------{C_RESET}")
    print(f"TASK DESCRIPTION             HOURS  ")
    print(f"{C_BLUE}------------------------------------{C_RESET}")
    
    for log in unbilled_logs:
        # Truncate task to 25 chars to keep table neat
        task_str = (log['task'][:22] + '...') if len(log['task']) > 25 else log['task'].ljust(25)
        print(f"{task_str} {log['hours']:>5.2f}h")
        
    print(f"{C_BLUE}------------------------------------{C_RESET}")
    print(f"TOTAL HOURS:                 {total_hours:>5.2f}h")
    print(f"{C_GREEN}TOTAL DUE:                   ${total_due:>7.2f}{C_RESET}")
    print(f"{C_BLUE}===================================={C_RESET}\n")
    
    if mark_billed:
        for log in data["logs"]:
            log["billed"] = True
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"{C_GREEN}✔ These hours have now been marked as BILLED.{C_RESET}")
    else:
        print(f"{C_DIM}Run with --bill to mark these hours as paid/invoiced.{C_RESET}")

def main():
    parser = argparse.ArgumentParser(description="gpx-admin: Client Administration Automator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init
    init_p = subparsers.add_parser("init", help="Setup a new client")
    init_p.add_argument("client", help="Name of the client")

    # Log
    log_p = subparsers.add_parser("log", help="Log hours and work done")
    log_p.add_argument("client", help="Name of the client")
    log_p.add_argument("hours", type=float, help="Number of hours (e.g., 1.5)")
    log_p.add_argument("task", help="Description of work completed")

    # Report
    report_p = subparsers.add_parser("report", help="Generate a status update email")
    report_p.add_argument("client", help="Name of the client")

    # Invoice
    invoice_p = subparsers.add_parser("invoice", help="Generate an invoice for unbilled hours")
    invoice_p.add_argument("client", help="Name of the client")
    invoice_p.add_argument("rate", type=float, help="Hourly rate (USD)")
    invoice_p.add_argument("--bill", action="store_true", help="Mark these hours as billed so they don't show up next time")

    args = parser.parse_args()

    if args.command == "init":
        init_client(args.client)
    elif args.command == "log":
        log_work(args.client, args.hours, args.task)
    elif args.command == "report":
        generate_report(args.client)
    elif args.command == "invoice":
        generate_invoice(args.client, args.rate, args.bill)

if __name__ == "__main__":
    main()
