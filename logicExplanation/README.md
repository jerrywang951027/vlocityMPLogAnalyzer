# Logic Explanation Documentation

This folder contains detailed documentation on the log parsing algorithm used by the Performance Log Analyzer.

## 📚 Documentation Files

### 1. [PARSING_ALGORITHM.md](./PARSING_ALGORITHM.md)
**Comprehensive text explanation of the parsing logic**

- Log format and structure
- Multi-phase parsing strategy
- Key insight: Why level numbers are unreliable
- Parent-child relationship algorithm (time containment)
- Handling unclosed methods
- Tree construction and validation
- Real-world example walkthrough
- Edge cases and performance analysis

**Recommended for:** Understanding the "why" and "how" of the algorithm in depth.

### 2. [ALGORITHM_DIAGRAM.md](./ALGORITHM_DIAGRAM.md)
**Visual diagrams and flowcharts**

- Overall parsing pipeline (ASCII art)
- Time containment concept visualization
- Why level numbers fail (timeline diagram)
- Level-specific stacks illustration
- Step-by-step parent assignment example
- Self-time calculation diagram
- Complexity analysis breakdown

**Recommended for:** Visual learners who prefer diagrams and examples.

---

## 🎯 Quick Summary

### The Problem
Parse Salesforce Apex debug logs to build an accurate method call hierarchy tree, despite:
- Missing EXIT events (unclosed methods)
- Inconsistent level numbers
- Thousands of nested method calls

### The Solution
**Pure Time Containment Algorithm**

A method `B` is a child of method `A` if and only if:
```
A.start_time ≤ B.start_time  AND  B.end_time ≤ A.end_time
```

By searching backwards through time-sorted methods, we find the **most recent (closest)** containing method as the immediate parent.

### The Result
✅ **Single root** (CODE_UNIT)  
✅ **Zero broken durations** (no children > parent time)  
✅ **All positive self-times**  
✅ **Correct nesting** matching actual execution flow  

---

## 🔍 Key Insights

### 1. Level Numbers Are Unreliable
```
Log shows: [117] → [36] → [72] → [216]
Actual nesting: 117 contains 36 contains 72 contains 216

But: 72 < 216 (level increased!)
```
**Conclusion:** Don't trust level numbers. Use time instead.

### 2. Time Containment Is Sufficient
If a method starts and ends within another method's timeframe, it's a child. No other information needed.

### 3. Nested CODE_UNITs (Apex Callouts) Are Supported
Salesforce logs can have nested CODE_UNITs representing Apex-to-Apex callouts:
- Tracked using a depth counter
- FINISHED events may omit `[EXTERNAL]|` prefix - regex handles both formats
- Example: `CPQServicePtc.processInCore` → `CpqApexCallable` → `CustomPricingPlanStepImpl`

### 4. Unclosed Methods Must Be Removed
Keeping unclosed non-root methods corrupts the tree because:
- Unknown end time → incorrect duration
- Children take more time than parent → impossible!

### 5. Backward Search Finds Immediate Parent
Searching backwards in time-sorted list ensures the first match is the direct parent, not a grandparent.

---

## 📖 Reading Guide

**For Quick Understanding:**
1. Read this README
2. Skim the "Overview" section of PARSING_ALGORITHM.md
3. Look at the "Time Containment" diagram in ALGORITHM_DIAGRAM.md

**For Implementation Details:**
1. Read PARSING_ALGORITHM.md sections 1-6
2. Study the example walkthrough (section 7)
3. Review the actual code in `source/parser/log_parser.py`

**For Visual Learning:**
1. Start with ALGORITHM_DIAGRAM.md
2. Follow the pipeline from raw log → final tree
3. Study the step-by-step parent assignment example
4. Read PARSING_ALGORITHM.md for deeper explanation

---

## 🧪 Validation

The algorithm is validated on every parse:

```python
roots = [c for c in method_calls if c.parent_id is None]
broken = sum(1 for c in method_calls 
             if sum(ch.duration for ch in c.children) > c.duration)

assert len(roots) == 1, "Should have exactly one root"
assert broken == 0, "No method should have children_time > duration"
```

**Real results:**
- Method calls: 18,438
- Roots: 1 ✅
- Broken: 0 ✅
- Unclosed (logged): 546 (all documented in `logExceptionRules.txt`)

---

## 💡 Why This Matters

**Incorrect hierarchy causes:**
- ❌ Negative self-time (confusing charts)
- ❌ Children taking more time than parents (impossible!)
- ❌ Wrong critical path identification
- ❌ Misleading performance insights

**Correct hierarchy enables:**
- ✅ Accurate self-time calculation
- ✅ True critical path highlighting
- ✅ Reliable performance bottleneck identification
- ✅ Chrome DevTools-like navigation

---

## 🔧 Related Files

- **Implementation:** `source/parser/log_parser.py`
- **Data Model:** `source/parser/method_call.py`
- **UI Tree View:** `source/ui/app.py` (Treeview rendering)
- **Exception Log:** `logExceptionRules.txt` (unclosed methods)
- **Test Logs:** `logs/apex-07LU900000K1FuZMAV.log`

---

## 📝 Version History

- **v1.0** (Initial): Stack-based with level comparison → Failed (many broken)
- **v2.0** (Level fix): Reversed level comparison → Failed (still broken)
- **v3.0** (Time only): Pure time containment → Success! ✅
- **v3.1** (Current): Fixed nested CODE_UNIT parsing → Complete! ✅

---

## 🤝 Contributing

If you find issues with the algorithm or have improvements:

1. Document the specific case in `logExceptionRules.txt`
2. Add a test case with the problematic log snippet
3. Propose a solution that maintains validation (1 root, 0 broken)

---

## 📚 Further Reading

- Salesforce Debug Log documentation
- Interval tree data structures (for optimization)
- Call graph analysis algorithms
- Chrome DevTools Performance panel architecture

---

**Last Updated:** October 22, 2025  
**Algorithm Version:** 3.1 (Pure Time Containment + Nested CODE_UNITs)  
**Validation Status:** ✅ All tests passing (18,467 methods, 1 root, 0 broken)

