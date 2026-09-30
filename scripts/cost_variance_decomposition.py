"""
Cost Variance Decomposition Framework
Decomposes total cost variance into:
- Price variance (supplier cost changes)
- Quantity variance (over/under consumption)
- Timing variance (early/late purchases)
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

class CostVarianceAnalyzer:
    """Analyze cost overruns into root causes"""
    
    def __init__(self, budget_data: pd.DataFrame, actual_data: pd.DataFrame):
        """
        Args:
            budget_data: Original budget (material, qty, unit_price)
            actual_data: Actual spend (material, qty, unit_price)
        """
        self.budget = budget_data
        self.actual = actual_data
    
    def decompose_variance(self) -> Dict:
        """
        Decompose total variance into components
        
        Returns:
            {
                'total_variance': float,
                'price_variance': float (supplier cost changes),
                'quantity_variance': float (over/under-consumption),
                'timing_variance': float (early/late purchases),
                'percentage_breakdown': dict
            }
        """
        # Implementation here
        pass
    
    def generate_report(self) -> pd.DataFrame:
        """Create summary report for steering committee"""
        pass

# Example Usage
if __name__ == "__main__":
    budget = pd.read_csv('data/budget.csv')
    actual = pd.read_csv('data/actual.csv')
    
    analyzer = CostVarianceAnalyzer(budget, actual)
    variance = analyzer.decompose_variance()
    
    print(f"Total variance: ${variance['total_variance']:,.0f}")
    print(f"  Price component: {variance['price_variance']:,.0f}")
    print(f"  Quantity component: {variance['quantity_variance']:,.0f}")
