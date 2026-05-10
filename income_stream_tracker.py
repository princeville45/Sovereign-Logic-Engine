"""
Income Stream Tracker
Sovereign Logic Engine

Tracks multiple income streams, calculates monthly totals, 
percentage contributions, and flags streams below targets.
"""

def track_income(income_data, targets=None):
    """
    Analyzes monthly income streams.
    
    Args:
        income_data (dict): Stream names and their monthly amounts.
        targets (dict): Target amounts for each stream.
        
    Returns:
        dict: Detailed financial intelligence report.
    """
    total_income = sum(income_data.values())
    report = {
        "total_monthly_income": total_income,
        "contributions": {},
        "underperforming_streams": [],
        "summary": "Stable"
    }
    
    for stream, amount in income_data.items():
        # Calculate % contribution
        percentage = (amount / total_income) * 100 if total_income > 0 else 0
        report["contributions"][stream] = {
            "amount": amount,
            "percentage": f"{percentage:.1f}%"
        }
        
        # Check against target
        if targets and stream in targets:
            target = targets[stream]
            if amount < target:
                report["underperforming_streams"].append({
                    "stream": stream,
                    "actual": amount,
                    "target": target,
                    "gap": target - amount
                })
                
    if len(report["underperforming_streams"]) > len(income_data) / 2:
        report["summary"] = "Action Required"
        
    return report

def display_report(report):
    """Prints a professional financial intelligence report."""
    print("="*45)
    print(" FINANCIAL INTELLIGENCE REPORT ")
    print("="*45)
    print(f"TOTAL MONTHLY INCOME: ${report['total_monthly_income']:,.2f}")
    print(f"FINANCIAL STATUS: {report['summary']}")
    print("-" * 45)
    print(f"{'STREAM':<15} | {'AMOUNT':<12} | {'CONTRIBUTION':<12}")
    print("-" * 45)
    for stream, data in report["contributions"].items():
        print(f"{stream:<15} | ${data['amount']:<11,.2f} | {data['percentage']:<12}")
        
    if report["underperforming_streams"]:
        print("-" * 45)
        print("ALERT: UNDERPERFORMING STREAMS")
        for s in report["underperforming_streams"]:
            print(f" [!] {s['stream']}: ${s['actual']:,.2f} (Target: ${s['target']:,.2f} | Gap: -${s['gap']:,.2f})")
    else:
        print("-" * 45)
        print("All income streams are hitting targets.")
    print("="*45)

if __name__ == "__main__":
    # Sample Financial Data
    current_income = {
        "Salary": 3500,
        "Freelance": 1200,
        "Crypto": 450,
        "Content": 200
    }
    
    income_targets = {
        "Salary": 3500,
        "Freelance": 1500,
        "Crypto": 500,
        "Content": 500
    }
    
    report = track_income(current_income, income_targets)
    display_report(report)
