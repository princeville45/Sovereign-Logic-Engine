"""
Sovereign Logic Engine: Net Worth Velocity Calculator
Vibe: Financial-Noir | Logic: Asset Accumulation Speed

In the shadows of the market, speed is the only metric that doesn't lie.
This script calculates the Velocity of Net Worth (VNW) - how fast your assets
are outrunning your liabilities in the compounding race.
"""

class SovereignEngine:
    def __init__(self, assets, liabilities, annual_growth_rate):
        self.assets = assets
        self.liabilities = liabilities
        self.growth_rate = annual_growth_rate

    def calculate_velocity(self, years):
        """
        Calculates the projected net worth and the velocity of accumulation.
        The goal is total financial sovereignty.
        """
        print("Initiating Sovereign Logic Scan...")
        results = []
        current_assets = self.assets
        for year in range(1, years + 1):
            # Compound growth applied to assets
            current_assets *= (1 + self.growth_rate)
            net_worth = current_assets - self.liabilities
            velocity = (net_worth / self.assets) * 100
            results.append({"year": year, "net_worth": round(net_worth, 2), "velocity": round(velocity, 2)})
        
        return results

if __name__ == "__main__":
    # Example: Initial Assets: 10M, Liabilities: 2M, Growth: 15%
    engine = SovereignEngine(10_000_000, 2_000_000, 0.15)
    intelligence = engine.calculate_velocity(5)
    
    for entry in intelligence:
        print(f"Year {entry['year']}: Net Worth Strategy at {entry['net_worth']} | Velocity: {entry['velocity']}%")
