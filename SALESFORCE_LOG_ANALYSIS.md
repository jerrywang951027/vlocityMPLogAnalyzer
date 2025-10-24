# Salesforce Apex Debug Log Analysis Guide

This guide explains how to use the Performance Log Analyzer with real Salesforce Apex debug logs from CPQ quoting processes.

## Quick Start

```bash
./run.sh
```

Then:
1. Click **Browse** and select your Salesforce debug log (e.g., `logs/Arun-apex-07LO500000S9OsuMAF.log`)
2. Click **Analyze**
3. Explore the visualizations in different tabs

## What Gets Analyzed

The tool parses **METHOD_ENTRY** and **METHOD_EXIT** events from Salesforce debug logs:

```
13:22:50.0 (4975796)|METHOD_ENTRY|[1]|01p5j00000Js5fA|vlocity_cmt.ComponentController.ComponentController()
13:22:50.0 (21080019)|METHOD_EXIT|[9]||System.UserInfo.getOrganizationId()
```

### Key Metrics

- **Duration**: Time between METHOD_ENTRY and METHOD_EXIT (in milliseconds)
- **Self Time**: Time spent in the method excluding child method calls
- **Nesting Level**: How deep the method is in the call stack
- **Critical Path**: The longest execution sequence through the call tree

## Understanding the Visualizations

### 1. Timeline Tab

- **Gantt chart** showing method execution over time
- **Red bars** indicate the critical path (longest execution sequence)
- **Horizontal axis** = time in milliseconds
- **Each bar** = one method call
- **Hover/Click** to see details

**What to look for:**
- Long bars indicate slow methods
- Red (critical path) methods are bottlenecks
- Gaps indicate waiting/external calls

### 2. Duration Analysis Tab

- **Bar chart** of top N slowest methods
- **Red bars** = critical path methods
- **Blue bars** = other methods

**What to look for:**
- Methods taking >1000ms might need optimization
- Multiple occurrences of the same method
- Unexpected long-running methods

### 3. Call Hierarchy Tab

- **Tree visualization** of method calls
- **Red nodes** = critical path
- **Blue nodes** = other methods
- Shows nesting relationships

**What to look for:**
- Depth of call stack (deeply nested = complex)
- Fan-out (many children = coordination)
- Isolated branches (independent operations)

### 4. Summary Stats Tab

**Four panels:**
1. **Duration Distribution** - histogram of method times
2. **Methods by Nesting Level** - complexity metric
3. **Total vs Self Time** - overhead analysis
4. **Summary Text** - key statistics

**Key Metrics:**
- Total Execution Time
- Average/Median/Max durations
- Critical path length and time
- Max nesting level

### 5. Raw Data Tab

- **Tabular view** of all parsed method calls
- **Columns:**
  - `call_id`: Unique identifier
  - `parent_id`: Parent method's call_id
  - `method_name`: Full method signature
  - `start_time`: Start timestamp (ms)
  - `end_time`: End timestamp (ms)
  - `duration`: Total time (ms)
  - `self_time`: Time excluding children (ms)
  - `level`: Nesting depth
  - `num_children`: Child method count

## Performance Analysis Workflow

### 1. Identify Bottlenecks

1. Check **Summary Stats** for total time
2. Look at **Duration Analysis** for slowest methods
3. Note which ones are on the **critical path** (red)

### 2. Understand Context

1. Go to **Timeline** to see when bottlenecks occur
2. Check **Call Hierarchy** to understand nesting
3. Use **Raw Data** to find parent-child relationships

### 3. Categorize Issues

**Type A: Individual Slow Methods**
- High duration, low self_time = delegates to slow children
- High duration, high self_time = actually slow itself

**Type B: Cumulative Issues**
- Same method called many times
- Each call is fast, but total adds up

**Type C: External Dependencies**
- Long gaps in timeline
- Methods with "query", "callout", "http" in name

### 4. Prioritize Optimizations

Focus on:
1. **Critical path methods** (biggest impact)
2. **High self_time methods** (actual work)
3. **Frequently called methods** (cumulative impact)

## Example Analysis

### Sample Log: Arun-apex-07LO500000S9OsuMAF.log

**Stats:**
- Total method calls: 5,545
- Total execution time: ~458 seconds
- Max nesting level: 80 (very deep!)
- Slowest method: 23.7 seconds

**Top Bottlenecks:**
1. `ComponentController.handleDataSecured()` - 23.7s
2. `IntegrationProcedureService.runIntegrationService()` - 23.4s
3. `InvokeService.invokeAsMap()` - 23.5s

**Analysis:**
- Deep integration procedure execution (level 55-62)
- Critical path goes through integration procedures
- Likely external service calls or complex data processing

**Optimization Ideas:**
- Profile the integration procedure steps
- Check for unnecessary loops or repeated queries
- Consider caching frequently accessed data
- Review integration procedure design for efficiency

## Tips for Better Analysis

### 1. Filter Noise

Large logs can be overwhelming:
- Focus on the **Top 20** slowest methods first
- Look at methods > 100ms duration
- Ignore very fast methods (< 1ms) initially

### 2. Pattern Recognition

Look for patterns:
- **Query patterns**: Methods with "query", "find", "get"
- **DML patterns**: "insert", "update", "delete"
- **Integration patterns**: "invoke", "callout", "http"

### 3. Compare Runs

Analyze multiple logs:
- Different data volumes
- Different user permissions
- Different org configurations
- Before/after optimizations

### 4. Export Data

Use the toolbar in charts to:
- **Save PNG** - for documentation
- **Zoom** - focus on specific timeframes
- **Pan** - explore different sections

## Common CPQ Performance Issues

### 1. Pricing Calculations

Look for:
- `PricingEngine.calculatePrices()`
- `DiscountCalculator.*`
- `TaxCalculator.*`

**Common causes:**
- Complex pricing rules
- Many line items
- Nested product bundles
- Attribute-based calculations

### 2. Configuration

Look for:
- `ConfigurationEngine.*`
- `ConstraintSolver.*`
- `RuleEngine.*`

**Common causes:**
- Complex configuration rules
- Many configuration options
- Dependency checking
- Validation rules

### 3. Data Access

Look for:
- `DatabaseConnection.query`
- `*.find*`
- `*.get*`

**Common causes:**
- Non-selective queries
- Missing indexes
- Excessive SOQL calls
- Large data volumes

### 4. Integration

Look for:
- `IntegrationProcedureService.*`
- `InvokeService.*`
- `*.callout*`

**Common causes:**
- External API latency
- Synchronous callouts
- Excessive integration steps
- Data transformation overhead

## Troubleshooting

### "No data could be parsed"

**Cause:** Log format not recognized

**Solution:**
- Ensure debug level includes APEX_CODE and APEX_PROFILING at FINEST
- Verify log contains METHOD_ENTRY and METHOD_EXIT lines
- Check log isn't truncated (2MB limit in Salesforce)

### "Analysis is slow"

**Cause:** Very large log file

**Solution:**
- Filter log to specific timeframe before analyzing
- Remove non-APEX_CODE log entries
- Use log filtering tools to reduce size

### "Charts are cluttered"

**Cause:** Too many method calls

**Solution:**
- Use zoom controls in chart toolbar
- Focus on **Duration Analysis** tab first
- Review **Summary Stats** for overview
- Filter by duration threshold in code

## Next Steps

1. **Identify** your top 3 bottlenecks
2. **Understand** why they're slow (use call hierarchy)
3. **Optimize** the code or configuration
4. **Re-test** and analyze a new log
5. **Compare** before/after metrics

## Support

For issues or questions:
- Check the main README.md
- Review QUICKSTART.md
- Examine the source code in `/source`

---

**Happy Performance Tuning! 🚀**

Remember: The goal is not to make everything fast, but to make the critical path fast!

