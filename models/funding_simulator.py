# Stochastic Funding Simulator
# Logic: Monte Carlo simulation to predict laptop funding date (Target: N1.2M)
import random
import datetime

def run_simulation(target=1200000, current_savings=0, avg_daily_rev=45000, volatility=0.3, iterations=1000):
    results = []
    
    for _ in range(iterations):
        balance = current_savings
        days = 0
        while balance < target:
            days += 1
            # Simulate daily revenue with a normal distribution based on volatility
            daily_gain = random.normalvariate(avg_daily_rev, avg_daily_rev * volatility)
            balance += max(daily_gain, 0) # No negative revenue at the depot
        results.append(days)
    
    results.sort()
    
    # Statistical Outcomes
    p50_days = results[int(iterations * 0.5)]
    p90_days = results[int(iterations * 0.9)]
    
    today = datetime.date.today()
    p50_date = today + datetime.timedelta(days=p50_days)
    p90_date = today + datetime.timedelta(days=p90_days)
    
    return {
        "p50": {"days": p50_days, "date": p50_date},
        "p90": {"days": p90_days, "date": p90_date},
        "target": target
    }

if __name__ == "__main__":
    print("--- Stochastic Funding Simulator: Run 1.0 ---")
    # Using current user context: Target N1.2M, Avg Daily Rev ~48k based on sync
    projection = run_simulation(target=1200000, avg_daily_rev=48000)
    
    print(f"Target Asset Value: N{projection['target']:,}")
    print(f"[P50 - High Probability]: {projection['p50']['date']} ({projection['p50']['days']} days)")
    print(f"[P90 - Conservative/Safe]: {projection['p90']['date']} ({projection['p90']['days']} days)")
