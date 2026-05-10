class TradespaceEvaluator:
    """Evaluates mission-critical business decisions."""
    def __init__(self, daily_revenue, script_quota, study_hours):
        self.daily_revenue = daily_revenue
        self.script_quota = script_quota
        self.study_hours = study_hours

    def evaluate_architecture(self):
        # Weightings: Financial (0.4), Equity (0.4), Growth (0.2)
        score = (min(self.daily_revenue / 50000, 1.0) * 4) +                 (min(self.script_quota / 8, 1.0) * 4) +                 (min(self.study_hours / 4, 1.0) * 2)
        return round(score, 2)
