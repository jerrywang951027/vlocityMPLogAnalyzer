# Quick Reference: Parent Assignment Algorithm

> **TL;DR:** Use pure time containment. A method is a child if its execution time is fully within another method's time. Search backwards to find the immediate parent.

---

## Core Algorithm (20 lines of logic)

```python
# Sort all method calls by start time
sorted_calls = sorted(method_calls, key=lambda x: x.start_time)

# For each method, find its parent
for i, call in enumerate(sorted_calls):
    if call.level == 0:
        call.parent_id = None  # Root (CODE_UNIT)
        continue
    
    # Search backwards for the most recent containing method
    best_parent = None
    for j in range(i - 1, -1, -1):
        candidate = sorted_calls[j]
        
        # Check if candidate FULLY contains this call
        if (candidate.start_time <= call.start_time and
            call.end_time <= candidate.end_time):
            best_parent = candidate
            break  # Stop at first match (most recent = immediate parent)
    
    call.parent_id = best_parent.call_id if best_parent else None
```

---

## Key Rules

| Rule | Explanation |
|------|-------------|
| **Time Containment** | Parent must start ≤ child start AND parent must end ≥ child end |
| **Backward Search** | Search from most recent to oldest (first match is immediate parent) |
| **Ignore Levels** | Level numbers are inconsistent - don't use them for hierarchy |
| **Break Early** | Stop at first match (don't search for grandparents) |
| **Level 0 = Root** | CODE_UNIT methods with level 0 are always roots |

---

## Decision Tree

```
For method M at index i:

  Is M.level == 0?
    YES → parent_id = None (M is root)
    NO  → Continue
  
  Search backwards from i-1 to 0:
    For each candidate C:
      
      Does C fully contain M?
      (C.start ≤ M.start AND M.end ≤ C.end)
        YES → parent_id = C.call_id, BREAK
        NO  → Continue to next candidate
  
  No parent found?
    Try level-0 root as fallback
    Still no parent?
      → parent_id = None (orphan)
```

---

## Example

```python
# Input: Three methods sorted by start time
methods = [
    MethodCall(id=0, start=100, end=1000),  # A
    MethodCall(id=1, start=200, end=900),   # B
    MethodCall(id=2, start=300, end=400),   # C
]

# Process id=0 (A): level 0 → parent=None

# Process id=1 (B): 
#   Check id=0 (A): A.start(100) ≤ B.start(200)? ✓
#                   B.end(900) ≤ A.end(1000)? ✓
#   → parent=A ✅

# Process id=2 (C):
#   Check id=1 (B): B.start(200) ≤ C.start(300)? ✓
#                   C.end(400) ≤ B.end(900)? ✓
#   → parent=B ✅ (don't check A, break early)

# Result:
#   A (root)
#   └─ B
#      └─ C
```

---

## Common Pitfalls

### ❌ Don't: Use level numbers for hierarchy
```python
# WRONG!
if candidate.level > call.level:  # Level numbers are unreliable!
    parent = candidate
```

### ✅ Do: Use time containment
```python
# CORRECT!
if (candidate.start_time <= call.start_time and
    call.end_time <= candidate.end_time):
    parent = candidate
```

---

### ❌ Don't: Search forward (later methods)
```python
# WRONG!
for j in range(i + 1, len(sorted_calls)):  # Can't be parent if started after!
    candidate = sorted_calls[j]
```

### ✅ Do: Search backward (earlier methods)
```python
# CORRECT!
for j in range(i - 1, -1, -1):  # Only earlier methods can be parents
    candidate = sorted_calls[j]
```

---

### ❌ Don't: Keep searching after finding a parent
```python
# WRONG! (finds grandparent, not immediate parent)
for j in range(i - 1, -1, -1):
    if candidate_contains_call:
        best_parent = candidate  # Don't break, keep searching
```

### ✅ Do: Break immediately on first match
```python
# CORRECT!
for j in range(i - 1, -1, -1):
    if candidate_contains_call:
        best_parent = candidate
        break  # First match is immediate parent!
```

---

## Validation

After parent assignment, validate:

```python
# Test 1: Single root
roots = [c for c in calls if c.parent_id is None]
assert len(roots) == 1  # Should have exactly one CODE_UNIT root

# Test 2: No impossible durations
for call in calls:
    children_time = sum(child.duration for child in call.children)
    assert children_time <= call.duration  # Children can't exceed parent time

# Test 3: No negative self-time
for call in calls:
    self_time = call.duration - sum(child.duration for child in call.children)
    assert self_time >= 0  # Self-time must be non-negative
```

**Expected results:**
- ✅ Roots: 1
- ✅ Broken: 0
- ✅ All self_time ≥ 0

---

## Why It Works

### Timeline Proof

```
Time: 0ms ─────────────────────────────────────► 1000ms

ParentA:  [════════════════════════════════]  100-900ms
             │                           │
             └──► ChildB: [═════]  200-400ms
                     │         │
                     │         └──── ChildB.end (400) ≤ ParentA.end (900) ✓
                     │
                     └──────────── ParentA.start (100) ≤ ChildB.start (200) ✓

Conclusion: ChildB's execution is FULLY WITHIN ParentA's execution
            → ParentA called ChildB
            → ParentA is parent of ChildB
```

### Backward Search Proof

```
Methods sorted by start time:
  [A, B, C, D, E] ← Processing E

  E's time: [500-600ms]

  Check D (most recent):
    D's time: [400-550ms] → Doesn't contain E (ends too early)
  
  Check C:
    C's time: [300-700ms] → CONTAINS E! ✓
    → C is E's parent (break here)
  
  Don't check B or A (they would be grandparents, not direct parent)
```

---

## Time Complexity

- **Sort:** O(n log n)
- **Assign parents:** O(n × d) where d = tree depth
  - Worst case: O(n²) for linear chain
  - Typical case: O(n × 10-50) for typical Apex logs

**For 18,000 methods:** ~1-2 seconds

---

## One-Liner Summary

> **Search backwards through time-sorted methods to find the most recent method that fully contains the current method's execution timeframe.**

---

## Recent Updates

### Version 3.1 (October 22, 2025)
- **Fixed:** Nested CODE_UNIT parsing (e.g., `CpqApexCallable`)
- **Issue:** CODE_UNIT_FINISHED events without `[EXTERNAL]|` prefix weren't matched
- **Impact:** Methods like `CpqApexCallable` (2065ms Apex callouts) were missing
- **Solution:** Updated regex: `|(?:[^\|]*\|)?` makes prefix optional
- **Result:** All nested CODE_UNITs now correctly parsed (18,467 methods vs 18,437)

---

## See Also

- [PARSING_ALGORITHM.md](./PARSING_ALGORITHM.md) - Full explanation
- [ALGORITHM_DIAGRAM.md](./ALGORITHM_DIAGRAM.md) - Visual diagrams
- [README.md](./README.md) - Documentation index
- `source/parser/log_parser.py:68-71` - CODE_UNIT regex
- `source/parser/log_parser.py:286-316` - Parent assignment algorithm

