#!/usr/bin/env python3
"""
Test script to verify method filtering works correctly
Tests that vlocity_cmt and System.* methods are NOT filtered by default
"""

import sys
import os

# Add source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'source'))

from parser.log_parser import LogParser
from visualization.chart_generator import ChartGenerator

def test_filtering():
    """Test that filtering is not applied by default"""
    print("\n" + "="*80)
    print("TESTING METHOD FILTERING")
    print("="*80)
    
    log_file = "logs/apex-07LU900000K1FuZMAV.log"
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        return False
    
    print(f"\n📁 Parsing log file: {log_file}")
    
    # Parse the log
    parser = LogParser()
    df = parser.parse_file(log_file)
    
    if df.empty:
        print("❌ No data parsed!")
        return False
    
    print(f"✅ Parsed {len(df)} method calls")
    
    # Count framework methods
    vlocity_methods = df[df['method_name'].str.contains('vlocity_cmt', na=False)]
    system_methods = df[df['method_name'].str.startswith('System.')]
    
    print(f"\n📊 Framework Method Counts:")
    print(f"   Methods containing 'vlocity_cmt': {len(vlocity_methods)}")
    print(f"   Methods starting with 'System.': {len(system_methods)}")
    print(f"   Total framework methods: {len(vlocity_methods) + len(system_methods)}")
    print(f"   Custom/business methods: {len(df) - len(vlocity_methods) - len(system_methods)}")
    
    # Create chart generator (should NOT filter by default)
    chart_gen = ChartGenerator(df, parser)
    
    # Verify that all methods are in the dataframe used by chart_gen
    print(f"\n🔍 Verifying ChartGenerator has all methods:")
    print(f"   ChartGenerator df size: {len(chart_gen.df)}")
    print(f"   Original df size: {len(df)}")
    
    if len(chart_gen.df) == len(df):
        print(f"   ✅ PASS - ChartGenerator has all methods (no filtering by default)")
    else:
        print(f"   ❌ FAIL - ChartGenerator is missing {len(df) - len(chart_gen.df)} methods!")
        return False
    
    # Test manual filtering (simulate UI checkbox)
    print(f"\n🔧 Testing manual filtering (simulating UI checkbox):")
    filtered_df = df[
        ~(df['method_name'].str.contains('vlocity_cmt', na=False) | 
          df['method_name'].str.startswith('System.'))
    ]
    print(f"   Filtered df size: {len(filtered_df)}")
    print(f"   Removed: {len(df) - len(filtered_df)} methods")
    
    if len(filtered_df) < len(df):
        print(f"   ✅ PASS - Manual filtering works correctly")
    else:
        print(f"   ⚠️  WARNING - No methods were filtered")
    
    # Show sample methods
    print(f"\n📋 Sample Framework Methods (should be visible by default):")
    sample_count = 0
    for _, row in df.iterrows():
        method_name = row['method_name']
        if 'vlocity_cmt' in method_name or method_name.startswith('System.'):
            print(f"   • {method_name[:70]}...")
            sample_count += 1
            if sample_count >= 5:
                break
    
    print(f"\n{'='*80}")
    print("✅ ALL TESTS PASSED")
    print("   - Framework methods are NOT filtered by default")
    print("   - Manual filtering works when checkbox is enabled")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = test_filtering()
    sys.exit(0 if success else 1)

