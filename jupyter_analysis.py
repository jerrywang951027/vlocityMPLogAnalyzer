"""
Salesforce Apex Performance Log Analysis - Jupyter Notebook Template

This script can be copied into a Jupyter notebook for interactive analysis.
Each section can be a separate cell in your notebook.

To use:
1. Run: jupyter notebook
2. Create a new notebook
3. Copy sections from this file into notebook cells
"""

# ============================================================================
# CELL 1: Setup and Import
# ============================================================================
import sys
import os

# Add source directory to path
sys.path.insert(0, os.path.join(os.getcwd(), 'source'))

from parser.log_parser import LogParser, MethodCall
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure plotting (for Jupyter)
# %matplotlib inline  # Uncomment this line in Jupyter (no inline comment allowed!)
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 6)

# Configure pandas display options for better readability
pd.set_option('display.max_colwidth', None)     # Show full column content (no truncation)
pd.set_option('display.max_rows', 100)          # Show up to 100 rows
pd.set_option('display.width', None)            # No width limit
pd.set_option('display.max_columns', None)      # Show all columns
pd.set_option('display.float_format', '{:.0f}'.format)  # No decimal points for floats

print("✅ Setup complete!")


# ============================================================================
# CELL 2: Load and Parse Log File
# ============================================================================
# Specify your log file path
LOG_FILE = 'logs/apex-07LU900000K1FuZMAV.log'

# Parse the log
parser = LogParser()
parser.parse_file(LOG_FILE)

# Get call tree and critical path
call_tree = parser.get_call_tree()
critical_path = parser.get_critical_path()

# Convert to DataFrame for analysis
df = pd.DataFrame([call.to_dict() for call in parser.method_calls])

# Clean up method names: strip signatures (everything after '(')
df['method_name'] = df['method_name'].str.split('(').str[0]

print(f"📁 Parsed log file: {LOG_FILE}")
print(f"📊 Total method calls: {len(df)}")
print(f"🎯 Critical path length: {len(critical_path)} methods")
print(f"⏱️  Total execution time: {df['duration'].max()} ms")
print("✅ Method signatures stripped for cleaner display")


# ============================================================================
# CELL 3: Quick Data Preview
# ============================================================================
# Display first few rows
print(df.head(10))

# Statistical summary
print("\n", df[['duration', 'self_time', 'level']].describe())


# ============================================================================
# CELL 4: Top Slow Methods
# ============================================================================
# Top 20 methods by total duration
print("🔥 Top 20 Slowest Methods (Overall):\n")
top_20 = df.nlargest(20, 'duration')[['method_name', 'duration', 'self_time']]
print(top_20)

# Top 20 methods excluding vlocity_cmt
print("\n🎯 Top 20 Slowest Methods (Excluding vlocity_cmt):\n")
top_20_no_vlocity = df[~df['method_name'].str.startswith('vlocity_cmt')].nlargest(20, 'duration')
print(top_20_no_vlocity[['method_name', 'duration', 'self_time']])

# Top 20 methods by self time (methods doing most work themselves)
print("\n⚡ Top 20 Methods by Self Time (Most Direct Work):\n")
top_self_time = df.nlargest(20, 'self_time')[['method_name', 'duration', 'self_time']]
print(top_self_time)


# ============================================================================
# CELL 5: Critical Path Analysis
# ============================================================================
print("🎯 Critical Path (slowest execution chain):\n")
for i, call in enumerate(critical_path, 1):
    indent = "  " * call.level
    method_short = call.method_name.split('(')[0]  # Remove signature
    print(f"{i:2d}. {indent}[{call.duration:.0f}ms] {method_short}")


# ============================================================================
# CELL 6: Custom Filtering Examples
# ============================================================================
# Find all methods taking more than 1 second
slow_methods = df[df['duration'] > 1000]
print(f"Found {len(slow_methods)} methods taking > 1 second:")
print(slow_methods[['method_name', 'duration', 'self_time']].sort_values('duration', ascending=False))

# Find methods from a specific class (e.g., CpqAppHandler)
class_filter = 'CpqAppHandler'
class_methods = df[df['method_name'].str.contains(class_filter, na=False)]
print(f"\nFound {len(class_methods)} methods in {class_filter}:")
print(class_methods[['method_name', 'duration', 'self_time']].sort_values('duration', ascending=False))

# Find methods with high self-time (doing a lot of work themselves)
high_self_time = df[df['self_time'] > 100].sort_values('self_time', ascending=False)
print(f"\nFound {len(high_self_time)} methods with self-time > 100ms:")
print(high_self_time[['method_name', 'duration', 'self_time']].head(20))


# ============================================================================
# CELL 7: Visualizations - Duration Distribution
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(df['duration'], bins=50, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Duration (ms)')
axes[0].set_ylabel('Count')
axes[0].set_title('Distribution of Method Durations')
axes[0].set_yscale('log')  # Log scale to see outliers

# Box plot by level
df.boxplot(column='duration', by='level', ax=axes[1])
axes[1].set_xlabel('Call Depth Level')
axes[1].set_ylabel('Duration (ms)')
axes[1].set_title('Duration by Call Depth')
plt.suptitle('')  # Remove default title

plt.tight_layout()
plt.show()


# ============================================================================
# CELL 8: Visualizations - Top 15 Methods Bar Chart
# ============================================================================
top_15 = df.nlargest(15, 'duration')
method_names_short = [name.split('(')[0][:50] for name in top_15['method_name']]

plt.figure(figsize=(12, 8))
plt.barh(range(len(top_15)), top_15['duration'], color='steelblue', alpha=0.8)
plt.yticks(range(len(top_15)), method_names_short)
plt.xlabel('Duration (ms)')
plt.title('Top 15 Methods by Duration')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()


# ============================================================================
# CELL 9: Visualizations - Self-Time vs Total Duration
# ============================================================================
plt.figure(figsize=(12, 6))
scatter = plt.scatter(df['self_time'], df['duration'], 
                     c=df['level'], cmap='viridis', alpha=0.6, s=50)
plt.colorbar(scatter, label='Call Depth Level')
plt.xlabel('Self Time (ms)')
plt.ylabel('Total Duration (ms)')
plt.title('Self-Time vs Total Duration (colored by call depth)')
plt.plot([0, df['duration'].max()], [0, df['duration'].max()], 'r--', alpha=0.3, label='y=x line')
plt.legend()
plt.tight_layout()
plt.show()

print("\nPoints above the red line = methods spending time in children")
print("Points on/near the red line = leaf methods doing their own work")


# ============================================================================
# CELL 10: Timeline Visualization
# ============================================================================
# Timeline visualization (top 20 longest methods)
top_20 = df.nlargest(20, 'duration').sort_values('start_time')

fig, ax = plt.subplots(figsize=(14, 10))
colors = plt.cm.tab20(np.linspace(0, 1, len(top_20)))

for i, (idx, row) in enumerate(top_20.iterrows()):
    method_name = row['method_name'].split('(')[0][:40]
    start = row['start_time']
    duration = row['duration']
    
    ax.barh(i, duration, left=start, height=0.7, color=colors[i], alpha=0.8)
    ax.text(start + duration/2, i, f"{duration:.0f}ms", 
            va='center', ha='center', fontsize=8, fontweight='bold')

ax.set_yticks(range(len(top_20)))
ax.set_yticklabels([name.split('(')[0][:40] for name in top_20['method_name']])
ax.set_xlabel('Time (ms)')
ax.set_title('Execution Timeline - Top 20 Longest Methods')
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.show()


# ============================================================================
# CELL 11: Performance Hotspot Detection
# ============================================================================
# Group by method name (without signature) to find frequently called methods
df['method_base'] = df['method_name'].str.split('(').str[0]
method_stats = df.groupby('method_base').agg({
    'duration': ['count', 'sum', 'mean', 'max'],
    'self_time': ['sum', 'mean']
}).round(0)

method_stats.columns = ['call_count', 'total_duration', 'avg_duration', 'max_duration', 
                        'total_self_time', 'avg_self_time']
method_stats = method_stats.sort_values('total_duration', ascending=False)

print("🔥 Performance Hotspots (methods with highest cumulative time):")
print(method_stats.head(20))

# Find methods called many times (potential for caching/optimization)
frequent_methods = method_stats[method_stats['call_count'] > 5].sort_values('call_count', ascending=False)
print(f"\n📞 Found {len(frequent_methods)} methods called more than 5 times:")
print(frequent_methods.head(20))


# ============================================================================
# CELL 12: Export Results
# ============================================================================
# Export to CSV
output_dir = 'analysis_results'
os.makedirs(output_dir, exist_ok=True)

# Full data
df.to_csv(f'{output_dir}/full_analysis.csv', index=False)

# Top slow methods
df.nlargest(50, 'duration').to_csv(f'{output_dir}/top_50_slow_methods.csv', index=False)

# Method statistics
method_stats.to_csv(f'{output_dir}/method_statistics.csv')

# Critical path
critical_df = pd.DataFrame([call.to_dict() for call in critical_path])
critical_df.to_csv(f'{output_dir}/critical_path.csv', index=False)

print(f"✅ Results exported to '{output_dir}/' directory")


# ============================================================================
# CELL 13: Custom Analysis - Vlocity vs Non-Vlocity
# ============================================================================
# Compare vlocity_cmt methods vs others
df['is_vlocity'] = df['method_name'].str.startswith('vlocity_cmt')

vlocity_stats = df.groupby('is_vlocity')['duration'].agg(['count', 'sum', 'mean'])
vlocity_stats.index = ['Non-Vlocity', 'Vlocity']
print(vlocity_stats)

# Visualize vlocity vs non-vlocity
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Count comparison
vlocity_stats['count'].plot(kind='bar', ax=axes[0], color=['steelblue', 'coral'])
axes[0].set_ylabel('Number of Methods')
axes[0].set_title('Vlocity vs Non-Vlocity Method Count')
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=0)

# Total time comparison
vlocity_stats['sum'].plot(kind='bar', ax=axes[1], color=['steelblue', 'coral'])
axes[1].set_ylabel('Total Duration (ms)')
axes[1].set_title('Vlocity vs Non-Vlocity Total Time')
axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=0)

plt.tight_layout()
plt.show()

