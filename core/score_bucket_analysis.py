"""
Score Bucket Expectancy Analysis

Analyzes trading performance across different score ranges (buckets)
to understand expected profitability at each confidence level.

Score Buckets:
- Ultra-Strong: score >= 0.50 (rare, high confidence)
- Very Strong: 0.30 to 0.49 (strong signal)
- Strong: 0.15 to 0.29 (good signal)
- Moderate: 0.05 to 0.14 (moderate signal)
- Weak: -0.05 to 0.04 (weak signal, avoid)
- Moderate Negative: -0.14 to -0.05
- Strong Negative: -0.29 to -0.15 (good bearish signal)
- Very Strong Negative: -0.49 to -0.30
- Ultra Strong Negative: <= -0.50

For each bucket, we track:
- Entry count
- Win rate (%)
- Avg win size
- Avg loss size
- Risk/Reward ratio
- Expectancy (%)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from collections import defaultdict


@dataclass
class BucketMetrics:
    """Metrics for a single score bucket"""
    bucket_name: str
    score_range: tuple  # (min_score, max_score)
    entry_count: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_win_size: float = 0.0
    avg_loss_size: float = 0.0
    risk_reward_ratio: float = 0.0
    expectancy: float = 0.0  # (win_rate * avg_win - (1 - win_rate) * avg_loss)
    total_profit: float = 0.0
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.entry_count == 0:
            return
        
        self.win_rate = (self.wins / self.entry_count) * 100 if self.entry_count > 0 else 0
        
        if self.avg_loss_size != 0:
            self.risk_reward_ratio = self.avg_win_size / abs(self.avg_loss_size)
        
        # Expectancy calculation: Expected value per trade
        if self.wins > 0 and self.losses > 0:
            win_prob = self.wins / self.entry_count
            loss_prob = self.losses / self.entry_count
            self.expectancy = (win_prob * self.avg_win_size) - (loss_prob * abs(self.avg_loss_size))
    
    def __str__(self) -> str:
        """Pretty print bucket metrics"""
        return (
            f"{self.bucket_name:25} | "
            f"Entries: {self.entry_count:3} | "
            f"Win%: {self.win_rate:6.2f}% | "
            f"RR: {self.risk_reward_ratio:5.2f} | "
            f"Expect: {self.expectancy:+7.2f}%"
        )


class ScoreBucketAnalyzer:
    """Analyzes trading results grouped by score buckets"""
    
    # Define score buckets
    SCORE_BUCKETS = [
        (0.50, 1.00, "Ultra-Strong Bullish"),
        (0.30, 0.49, "Very Strong Bullish"),
        (0.15, 0.29, "Strong Bullish"),
        (0.05, 0.14, "Moderate Bullish"),
        (-0.05, 0.04, "Weak/Neutral"),
        (-0.14, -0.05, "Moderate Bearish"),
        (-0.29, -0.15, "Strong Bearish"),
        (-0.49, -0.30, "Very Strong Bearish"),
        (-1.00, -0.50, "Ultra-Strong Bearish"),
    ]
    
    def __init__(self):
        self.buckets: Dict[str, BucketMetrics] = {}
        self._initialize_buckets()
    
    def _initialize_buckets(self):
        """Initialize empty metrics for all buckets"""
        for min_score, max_score, bucket_name in self.SCORE_BUCKETS:
            bucket_key = self._get_bucket_key(min_score)
            self.buckets[bucket_key] = BucketMetrics(
                bucket_name=bucket_name,
                score_range=(min_score, max_score)
            )
    
    def _get_bucket_key(self, score: float) -> str:
        """Find which bucket a score belongs to"""
        for min_score, max_score, bucket_name in self.SCORE_BUCKETS:
            if min_score <= score < max_score:
                return f"{min_score}_{max_score}"
        # Ultra-strong negative
        return "-1.00_-0.50"
    
    def add_trade_result(self, score: float, is_win: bool, win_size: float = 0.0, loss_size: float = 0.0):
        """
        Record a trade result in the appropriate bucket
        
        Args:
            score: Final score of the trade
            is_win: Whether trade was profitable
            win_size: Profit size if win
            loss_size: Loss size if loss (should be positive)
        """
        bucket_key = self._get_bucket_key(score)
        bucket = self.buckets[bucket_key]
        
        bucket.entry_count += 1
        
        if is_win:
            bucket.wins += 1
            bucket.avg_win_size = (
                (bucket.avg_win_size * (bucket.wins - 1) + win_size) / bucket.wins
            )
            bucket.total_profit += win_size
        else:
            bucket.losses += 1
            bucket.avg_loss_size = (
                (bucket.avg_loss_size * (bucket.losses - 1) - loss_size) / bucket.losses
            )
            bucket.total_profit -= loss_size
        
        bucket.calculate_metrics()
    
    def add_multiple_results(self, results: List[Dict]):
        """
        Add multiple trade results at once
        
        Expected dict format:
        {
            'final_score': float,
            'profitable': bool or 'win'/'loss',
            'pnl': float (profit/loss amount),
        }
        """
        for result in results:
            score = result.get('final_score', 0)
            is_win = result.get('profitable') or result.get('status') == 'win'
            pnl = result.get('pnl', 0)
            
            if is_win:
                self.add_trade_result(score, True, win_size=pnl)
            else:
                self.add_trade_result(score, False, loss_size=abs(pnl))
    
    def get_bucket_metrics(self) -> Dict[str, BucketMetrics]:
        """Get metrics for all buckets"""
        return self.buckets
    
    def get_best_buckets(self, n: int = 3) -> List[BucketMetrics]:
        """Get top N buckets by expectancy"""
        buckets_list = [b for b in self.buckets.values() if b.entry_count > 0]
        return sorted(buckets_list, key=lambda x: x.expectancy, reverse=True)[:n]
    
    def get_worst_buckets(self, n: int = 3) -> List[BucketMetrics]:
        """Get worst N buckets by expectancy"""
        buckets_list = [b for b in self.buckets.values() if b.entry_count > 0]
        return sorted(buckets_list, key=lambda x: x.expectancy)[:n]
    
    def get_actionable_buckets(self, min_expectancy: float = 2.0) -> List[BucketMetrics]:
        """Get buckets with positive expectancy above threshold"""
        return [
            b for b in self.buckets.values()
            if b.entry_count > 0 and b.expectancy >= min_expectancy
        ]
    
    def print_summary(self):
        """Print formatted summary of all buckets"""
        print("\n" + "=" * 100)
        print("SCORE BUCKET EXPECTANCY ANALYSIS")
        print("=" * 100)
        print()
        
        # Print header
        print(
            f"{'Bucket':25} | "
            f"{'Entries':10} | "
            f"{'Win Rate':10} | "
            f"{'Risk/Reward':10} | "
            f"{'Expectancy':15}"
        )
        print("-" * 100)
        
        # Print each bucket (ordered by score range)
        for min_score, max_score, _ in self.SCORE_BUCKETS:
            bucket_key = f"{min_score}_{max_score}"
            bucket = self.buckets[bucket_key]
            
            if bucket.entry_count > 0:
                print(bucket)
        
        print()
        print("=" * 100)
        print(f"Total trades analyzed: {sum(b.entry_count for b in self.buckets.values())}")
        print()
        
        # Print best and worst performers
        best = self.get_best_buckets(3)
        worst = self.get_worst_buckets(3)
        
        if best:
            print("TOP 3 PERFORMING BUCKETS:")
            for bucket in best:
                print(f"  {bucket}")
        
        print()
        
        if worst:
            print("WORST 3 PERFORMING BUCKETS:")
            for bucket in worst:
                print(f"  {bucket}")
        
        print()


def analyze_existing_results(csv_path: str) -> ScoreBucketAnalyzer:
    """
    Analyze existing CSV results file and generate bucket analysis
    
    CSV should have columns: final_score, profitable (or similar)
    """
    import csv
    
    analyzer = ScoreBucketAnalyzer()
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    score = float(row.get('final_score', 0))
                    is_win = row.get('profitable', '').lower() in ['yes', 'true', '1', 'win']
                    
                    analyzer.add_trade_result(score, is_win)
                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        print(f"Warning: CSV file not found: {csv_path}")
    
    return analyzer


# Example usage:
if __name__ == "__main__":
    # Create analyzer
    analyzer = ScoreBucketAnalyzer()
    
    # Simulate some trading results
    test_results = [
        {'final_score': 0.75, 'profitable': True, 'pnl': 500},
        {'final_score': 0.65, 'profitable': True, 'pnl': 450},
        {'final_score': 0.35, 'profitable': True, 'pnl': 300},
        {'final_score': 0.25, 'profitable': False, 'pnl': -200},
        {'final_score': 0.10, 'profitable': False, 'pnl': -150},
        {'final_score': -0.20, 'profitable': True, 'pnl': 250},
        {'final_score': -0.50, 'profitable': True, 'pnl': 400},
    ]
    
    analyzer.add_multiple_results(test_results)
    analyzer.print_summary()
