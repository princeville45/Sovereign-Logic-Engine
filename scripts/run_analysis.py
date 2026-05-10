from core.engine import TradespaceEvaluator

def main():
    print("--- Sovereign Logic Engine: Tradespace Analysis ---")
    # Example: Analyze current stats
    architect = TradespaceEvaluator(daily_revenue=48500, script_quota=4, study_hours=3)
    score = architect.evaluate_architecture()
    print(f"Mission Efficiency Score: {score}/10")

if __name__ == "__main__":
    main()
