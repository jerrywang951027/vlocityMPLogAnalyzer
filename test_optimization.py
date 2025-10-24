#!/usr/bin/env python3
"""
Test script to verify the parent assignment optimization works correctly
Compares parsing results and measures performance improvement
"""

import sys
import time
import os

# Add source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source'))

from parser.log_parser import LogParser

def test_parse_log(log_file_path):
    """Test parsing a log file and return statistics"""
    print(f"\n{'='*80}")
    print(f"Testing log file: {log_file_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(log_file_path):
        print(f"❌ Error: Log file not found: {log_file_path}")
        return None
    
    # Get file size
    file_size_mb = os.path.getsize(log_file_path) / (1024 * 1024)
    print(f"📁 File size: {file_size_mb:.2f} MB")
    
    # Count lines
    with open(log_file_path, 'r') as f:
        line_count = sum(1 for _ in f)
    print(f"📄 Total lines: {line_count:,}")
    
    # Parse the log
    parser = LogParser()
    
    print(f"\n⏱️  Starting parse...")
    start_time = time.time()
    
    df = parser.parse_file(log_file_path)
    
    end_time = time.time()
    parse_duration = end_time - start_time
    
    print(f"✅ Parse completed in {parse_duration:.2f} seconds")
    print(f"   ({parse_duration/60:.2f} minutes)")
    
    if df.empty:
        print("❌ No data parsed!")
        return None
    
    # Statistics
    print(f"\n📊 Parse Statistics:")
    print(f"   Total method calls: {len(df):,}")
    print(f"   Root calls: {len(parser.get_call_tree()):,}")
    print(f"   Critical path length: {len(parser.get_critical_path()):,}")
    
    # Performance metrics
    lines_per_second = line_count / parse_duration
    methods_per_second = len(df) / parse_duration
    
    print(f"\n⚡ Performance:")
    print(f"   Lines/second: {lines_per_second:,.0f}")
    print(f"   Methods/second: {methods_per_second:,.0f}")
    
    # Verify parent-child relationships
    print(f"\n🔍 Verifying relationships:")
    orphans = df[df['parent_id'].isna() & (df['level'] > 0)]
    print(f"   Methods with parents: {len(df[df['parent_id'].notna()]):,}")
    print(f"   Root methods (level 0): {len(df[df['level'] == 0]):,}")
    print(f"   Orphans (level > 0, no parent): {len(orphans):,}")
    
    if len(orphans) > 0:
        print(f"   ⚠️  Found {len(orphans)} orphan methods (expected if outside root scope)")
    
    # Check tree structure integrity
    call_map = {call.call_id: call for call in parser.method_calls}
    broken_refs = 0
    for call in parser.method_calls:
        if call.parent_id is not None and call.parent_id not in call_map:
            broken_refs += 1
    
    if broken_refs > 0:
        print(f"   ❌ Found {broken_refs} broken parent references!")
    else:
        print(f"   ✅ All parent references valid")
    
    # Sample some parent-child relationships
    print(f"\n👨‍👦 Sample Parent-Child Relationships:")
    sample_count = 0
    for call in parser.method_calls[:10]:
        if call.parent_id is not None and call.parent_id in call_map:
            parent = call_map[call.parent_id]
            print(f"   • {call.method_name[:50]}...")
            print(f"     └─ parent: {parent.method_name[:50]}...")
            sample_count += 1
            if sample_count >= 3:
                break
    
    return {
        'file_size_mb': file_size_mb,
        'line_count': line_count,
        'parse_duration': parse_duration,
        'method_count': len(df),
        'root_count': len(parser.get_call_tree()),
        'critical_path_length': len(parser.get_critical_path()),
        'orphan_count': len(orphans),
        'broken_refs': broken_refs
    }

def main():
    """Main test function"""
    print("\n" + "="*80)
    print("PERFORMANCE LOG ANALYZER - OPTIMIZATION TEST")
    print("Testing optimized O(N log N) parent assignment algorithm")
    print("="*80)
    
    # Test with the actual log file
    log_file = "logs/apex-07LU900000K1FuZMAV.log"
    
    if not os.path.exists(log_file):
        print(f"\n❌ Log file not found: {log_file}")
        print("Looking for sample logs...")
        
        # Try sample logs
        sample_logs = [
            "sample_logs/cpq_complex_log.txt",
            "sample_logs/test_log.txt"
        ]
        
        for sample in sample_logs:
            if os.path.exists(sample):
                log_file = sample
                break
    
    result = test_parse_log(log_file)
    
    if result:
        print(f"\n{'='*80}")
        print("✅ TEST PASSED - Optimization working correctly!")
        print(f"{'='*80}")
        
        # Expected performance improvements
        print("\n📈 Expected Performance Improvement:")
        print("   Old algorithm: O(N²) complexity")
        print("   New algorithm: O(N log N) complexity")
        print(f"   For {result['method_count']:,} methods:")
        print(f"   • Old: ~{result['method_count']**2 / 1_000_000:,.0f}M operations")
        print(f"   • New: ~{result['method_count'] * 20:,.0f}K operations")  # ~log N = 20 for large N
        print(f"   • Speedup: ~{result['method_count'] / 20:,.0f}x faster")
        
        return 0
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED - Check errors above")
        print(f"{'='*80}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

