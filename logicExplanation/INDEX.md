# Documentation Index

## 📚 Complete Documentation Suite

This folder contains **4 complementary documents** (1,348 lines total) explaining the log parsing algorithm:

---

### 1. 📖 [README.md](./README.md) - **START HERE**
**183 lines** | Entry point and overview

- Quick summary of the problem and solution
- Key insights at a glance
- Reading guide for different learning styles
- Validation results
- Version history

**Best for:** Getting oriented and deciding what to read next

---

### 2. 🎯 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - **For Developers**
**246 lines** | Fast lookup and code snippets

- Core algorithm in 20 lines of code
- Decision tree flowchart
- Quick example walkthrough
- Common pitfalls (❌ vs ✅)
- One-liner summary
- Validation checklist

**Best for:** Implementing or modifying the algorithm

---

### 3. 📝 [PARSING_ALGORITHM.md](./PARSING_ALGORITHM.md) - **Deep Dive**
**466 lines** | Comprehensive explanation

- Log format specifications
- Multi-phase parsing strategy
- Why level numbers are unreliable (with proof)
- Parent-child algorithm design rationale
- Handling unclosed methods
- Edge cases and validation
- Performance analysis
- Complete example walkthrough

**Best for:** Understanding the "why" behind every decision

---

### 4. 📊 [ALGORITHM_DIAGRAM.md](./ALGORITHM_DIAGRAM.md) - **Visual Learning**
**453 lines** | ASCII art diagrams and flowcharts

- Overall parsing pipeline (visual)
- Time containment concept (timeline diagrams)
- Level number inconsistency (illustrated example)
- Parent assignment step-by-step (visual trace)
- Self-time calculation (breakdown)
- Complexity analysis (charts)

**Best for:** Visual learners who prefer diagrams

---

## 🎓 Learning Paths

### Path 1: Quick Understanding (15 minutes)
```
1. README.md (Quick Summary section)
2. QUICK_REFERENCE.md (Core Algorithm + Example)
3. ALGORITHM_DIAGRAM.md (Time Containment diagram)
```

### Path 2: Implementation (30 minutes)
```
1. QUICK_REFERENCE.md (entire document)
2. PARSING_ALGORITHM.md (sections 1-4)
3. Review: source/parser/log_parser.py (lines 286-316)
```

### Path 3: Complete Understanding (2 hours)
```
1. README.md (complete)
2. PARSING_ALGORITHM.md (complete)
3. ALGORITHM_DIAGRAM.md (all diagrams)
4. QUICK_REFERENCE.md (for recap)
5. Code review: source/parser/log_parser.py
```

### Path 4: Visual First (45 minutes)
```
1. ALGORITHM_DIAGRAM.md (all diagrams)
2. PARSING_ALGORITHM.md (Example Walkthrough section)
3. QUICK_REFERENCE.md (validation section)
```

---

## 🔑 Key Takeaways

### The Core Insight
**Level numbers in Salesforce logs are NOT hierarchical.**

Example:
```
METHOD_ENTRY [117] methodA
METHOD_ENTRY [36] methodB
METHOD_ENTRY [72] methodC
METHOD_ENTRY [216] methodD  ← Level increased, but it's deeper!
```

### The Solution
**Pure Time Containment**

```python
if (parent.start_time <= child.start_time and
    child.end_time <= parent.end_time):
    # parent contains child
```

### The Results
- ✅ Roots: 1 (single CODE_UNIT)
- ✅ Broken: 0 (no impossible durations)
- ✅ All positive self-times
- ✅ Correct nesting matching execution flow

---

## 📖 Quick Reference by Topic

| Topic | Document | Section |
|-------|----------|---------|
| Why level numbers fail | PARSING_ALGORITHM.md | § Key Insight |
| Core algorithm code | QUICK_REFERENCE.md | § Core Algorithm |
| Time containment visual | ALGORITHM_DIAGRAM.md | § 2. Time Containment |
| Handling unclosed methods | PARSING_ALGORITHM.md | § 5. Handling Unclosed |
| Step-by-step example | ALGORITHM_DIAGRAM.md | § 6. Parent Assignment |
| Validation tests | QUICK_REFERENCE.md | § Validation |
| Performance analysis | PARSING_ALGORITHM.md | § Performance |
| Common mistakes | QUICK_REFERENCE.md | § Common Pitfalls |

---

## 🧪 Try It Yourself

### Test the Algorithm

```bash
cd /Users/jin.wang/workspace/tools/perfLogAnalyzer1
source venv/bin/activate
python -c "
import sys
sys.path.insert(0, 'source')
from parser.log_parser import LogParser

parser = LogParser()
parser.parse_file('logs/apex-07LU900000K1FuZMAV.log')

# Validate
roots = [c for c in parser.method_calls if c.parent_id is None]
broken = sum(1 for c in parser.method_calls 
             if sum(ch.duration for ch in c.children) > c.duration)

print(f'Methods: {len(parser.method_calls)}')
print(f'Roots: {len(roots)}')
print(f'Broken: {broken}')
"
```

**Expected Output:**
```
Methods: 18438
Roots: 1
Broken: 0
```

---

## 📁 File Sizes

```
README.md             183 lines    5.2 KB
QUICK_REFERENCE.md    246 lines    7.1 KB
PARSING_ALGORITHM.md  466 lines   15.0 KB
ALGORITHM_DIAGRAM.md  453 lines   23.0 KB
─────────────────────────────────────────
Total:              1,348 lines   50.3 KB
```

---

## 🔗 Related Resources

### Code Implementation
- `source/parser/log_parser.py` - Main parser implementation
- `source/parser/method_call.py` - Method call data model
- `source/ui/app.py` - Tree view rendering

### Log Files
- `logs/apex-07LU900000K1FuZMAV.log` - Test log (20K+ methods)
- `logExceptionRules.txt` - Unclosed methods log (546 exceptions)

### Project Documentation
- `README.md` - Project overview
- `QUICKSTART.md` - Getting started guide
- `SALESFORCE_LOG_ANALYSIS.md` - Log analysis guide

---

## 💡 Need Help?

1. **Not sure where to start?** → Read [README.md](./README.md)
2. **Need to implement it?** → Read [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
3. **Want to understand deeply?** → Read [PARSING_ALGORITHM.md](./PARSING_ALGORITHM.md)
4. **Prefer visuals?** → Read [ALGORITHM_DIAGRAM.md](./ALGORITHM_DIAGRAM.md)

---

**Last Updated:** October 22, 2025  
**Algorithm Version:** 3.1 (Pure Time Containment + Nested CODE_UNITs)  
**Status:** ✅ Production-ready, fully validated

### Latest Update (v3.1)
Fixed parsing of nested CODE_UNITs (Apex callouts) - `CpqApexCallable` and similar methods now correctly appear in tree!
