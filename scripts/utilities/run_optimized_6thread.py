"""
Optimized 6-thread analysis with intelligent fallback
- Largecap: Breeze → yF
- Mid/Small: yF → Breeze → daily
"""
import threading
import queue
import time
from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from data_providers import get_intraday_candles_for

class OptimizedWorker(threading.Thread):
    """Worker with intelligent fallback strategy"""
    
    def __init__(self, thread_id, cap_type, stock_queue, results, lock):
        super().__init__()
        self.thread_id = thread_id
        self.cap_type = cap_type  # 'largecap' or 'midsmall'
        self.stock_queue = stock_queue
        self.results = results
        self.lock = lock
        self.daemon = False
        self.processed = 0
        self.fallbacks = 0
        
    def run(self):
        """Process with intelligent fallback"""
        while True:
            try:
                stock = self.stock_queue.get(timeout=1)
            except queue.Empty:
                break
            
            start = time.time()
            
            if self.cap_type == 'largecap':
                result = self._process_largecap(stock)
            else:
                result = self._process_midsmall(stock)
            
            elapsed = time.time() - start
            result['elapsed_sec'] = elapsed
            
            with self.lock:
                self.results[stock] = result
                self.processed += 1
                
                if self.processed % 20 == 0:
                    print(f"[T{self.thread_id}] {self.processed} processed, "
                          f"fallbacks={self.fallbacks}")
            
            self.stock_queue.task_done()
        
        print(f"[T{self.thread_id}] DONE: {self.processed} processed, "
              f"{self.fallbacks} fallbacks")
    
    def _process_largecap(self, stock):
        """Largecap: Breeze → yF → daily fallback"""
        
        # Try Breeze first (has better coverage for largecap)
        try:
            result = get_intraday_candles_for(
                stock,
                interval='5minute',
                max_bars=200,
                use_yf=False,
                force_yf=False
            )
            
            # Result is tuple: (candles_list, source_name)
            if isinstance(result, tuple):
                candles, source = result
            else:
                candles = result
                source = 'breeze'
            
            if candles and len(candles) >= 10:
                score, conf = self._calc_score(candles)
                return {
                    'stock': stock, 'score': score, 'confidence': conf,
                    'source': 'Breeze', 'candles': len(candles), 'timeframe': '5min'
                }
        except:
            pass
        
        # Fallback 1: yFinance 15-min
        try:
            with self.lock:
                self.fallbacks += 1
            
            result = get_intraday_candles_for(
                stock,
                interval='15min',
                max_bars=200,
                use_yf=True,
                force_yf=True
            )
            
            if isinstance(result, tuple):
                candles, source = result
            else:
                candles = result
                source = 'yf'
            
            if candles and len(candles) >= 10:
                score, conf = self._calc_score(candles)
                return {
                    'stock': stock, 'score': score, 'confidence': conf,
                    'source': 'yFinance', 'candles': len(candles), 'timeframe': '15min'
                }
        except:
            pass
        
        # Fallback 2: Daily data
        try:
            result = get_intraday_candles_for(
                stock,
                interval='1day',
                max_bars=90,
                use_yf=True,
                force_yf=True
            )
            
            if isinstance(result, tuple):
                candles, source = result
            else:
                candles = result
                source = 'yf'
            
            if candles and len(candles) >= 5:
                score, conf = self._calc_score(candles)
                return {
                    'stock': stock, 'score': score, 'confidence': conf,
                    'source': 'yFinance-daily', 'candles': len(candles), 'timeframe': '1day'
                }
        except:
            pass
        
        return {'stock': stock, 'error': 'All fallbacks exhausted', 
               'score': 0, 'confidence': 0}
    
    def _process_midsmall(self, stock):
        """Mid/Small: yF → Breeze (with wait) → daily fallback"""
        
        # Try yFinance first (fast, no rate limits)
        try:
            result = get_intraday_candles_for(
                stock,
                interval='15min',
                max_bars=200,
                use_yf=True,
                force_yf=True
            )
            
            if isinstance(result, tuple):
                candles, source = result
            else:
                candles = result
                source = 'yf'
            
            if candles and len(candles) >= 10:
                score, conf = self._calc_score(candles)
                return {
                    'stock': stock, 'score': score, 'confidence': conf,
                    'source': 'yFinance', 'candles': len(candles), 'timeframe': '15min'
                }
        except:
            pass
        
        # Fallback 1: Breeze (with 2s wait to avoid rate limit)
        try:
            with self.lock:
                self.fallbacks += 1
            
            time.sleep(2)  # Rate limit protection
            
            result = get_intraday_candles_for(
                stock,
                interval='5minute',
                max_bars=200,
                use_yf=False,
                force_yf=False
            )
            
            if isinstance(result, tuple):
                candles, source = result
            else:
                candles = result
                source = 'breeze'
            
            if candles and len(candles) >= 10:
                score, conf = self._calc_score(candles)
                return {
                    'stock': stock, 'score': score, 'confidence': conf,
                    'source': 'Breeze', 'candles': len(candles), 'timeframe': '5min'
                }
        except:
            pass
        
        # Fallback 2: Daily data
        try:
            result = get_intraday_candles_for(
                stock,
                interval='1day',
                max_bars=90,
                use_yf=True,
                force_yf=True
            )
            
            if isinstance(result, tuple):
                candles, source = result
            else:
                candles = result
                source = 'yf'
            
            if candles and len(candles) >= 5:
                score, conf = self._calc_score(candles)
                return {
                    'stock': stock, 'score': score, 'confidence': conf,
                    'source': 'yFinance-daily', 'candles': len(candles), 'timeframe': '1day'
                }
        except:
            pass
        
        return {'stock': stock, 'error': 'All fallbacks exhausted', 
               'score': 0, 'confidence': 0}
    
    @staticmethod
    def _calc_score(candles):
        """Calculate bearness score"""
        if not candles or len(candles) < 2:
            return 0.0, 0.0
        
        closes = [c.get('close', 0) for c in candles]
        
        momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] != 0 else 0
        bearness = -momentum
        confidence = min(abs(momentum) * 100, 100)
        
        return bearness, confidence

def main():
    """Run optimized multi-threaded analysis"""
    
    print("=" * 80)
    print("OPTIMIZED MULTI-THREADED BEARNESS ANALYSIS")
    print("=" * 80)
    print(f"Start: {datetime.now().strftime('%H:%M:%S')}")
    
    # Load stocks
    with open("niftylarge_constituents.txt") as f:
        all_stocks = [s.strip() for s in f if s.strip()]
    
    # Load strategy
    with open("fallback_strategy_config.json") as f:
        config = json.load(f)
    
    largecap = set(config['universes']['largecap'])
    midsmall = set(config['universes']['midsmall'])
    
    print(f"\nStocks to analyze: {len(all_stocks)}")
    print(f"  Largecap (Breeze→yF): {len(largecap)}")
    print(f"  Mid/Small (yF→Breeze): {len(midsmall)}")
    
    # Create queues
    queue_largecap = queue.Queue()
    queue_midsmall = queue.Queue()
    results = {}
    lock = threading.Lock()
    
    # Populate queues
    for stock in all_stocks:
        if stock in largecap:
            queue_largecap.put(stock)
        else:
            queue_midsmall.put(stock)
    
    # Start threads
    threads = []
    start_time = time.time()
    
    print("\nStarting threads...")
    print("  Threads 1-3: Mid/Small (yF-first, fast)")
    print("  Threads 4-5: Largecap (Breeze-first)")
    print("  Thread 6: Backup/Overflow")
    print()
    
    # Threads 1-3: Mid/Small
    for i in range(1, 4):
        t = OptimizedWorker(i, 'midsmall', queue_midsmall, results, lock)
        threads.append(t)
        t.start()
    
    # Threads 4-5: Largecap
    for i in range(4, 6):
        t = OptimizedWorker(i, 'largecap', queue_largecap, results, lock)
        threads.append(t)
        t.start()
    
    # Thread 6: Adaptive (help whichever finishes first)
    t6 = OptimizedWorker(6, 'midsmall', queue_midsmall, results, lock)
    threads.append(t6)
    t6.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.2f} minutes)")
    print(f"Stocks processed: {len(results)}/{len(all_stocks)}")
    print(f"Avg per stock: {elapsed/len(results):.2f} seconds")
    
    # Categorize
    success = sum(1 for r in results.values() if 'score' in r and 'error' not in r)
    errors = sum(1 for r in results.values() if 'error' in r)
    
    print(f"\nSuccess: {success}")
    print(f"Errors: {errors}")
    
    # Data sources
    sources = {}
    fallbacks_total = 0
    
    for r in results.values():
        if 'source' in r:
            src = r['source']
            sources[src] = sources.get(src, 0) + 1
    
    print(f"\nData sources used:")
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src:20} : {cnt:3}")
    
    # Save results
    with open("optimized_results.json", "w") as f:
        json.dump({
            'results': results,
            'summary': {
                'total_time': elapsed,
                'total_stocks': len(results),
                'success': success,
                'errors': errors,
                'sources': sources
            }
        }, f, indent=2, default=str)
    
    print(f"\nResults saved: optimized_results.json")
    print(f"End: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == '__main__':
    main()
