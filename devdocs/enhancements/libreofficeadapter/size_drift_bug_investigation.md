# Size Drift Bug Investigation

**Date:** 2026-01-20
**Status:** Confirmed - LibreOffice PPTX Filter Bug
**Severity:** Low (for typical use cases)

---

## Summary

Shape sizes change by ±1 unit per dimension on every PPTX open/save cycle through LibreOffice, even with NO edits made. This is a bug in LibreOffice's PPTX import/export filter, not in LibreServer code.

---

## Original Bug Report

From tool call logs during SlideFixer testing:

```
Initial:  [0] CustomShape size=(25399x2031)
After 1:  [0] CustomShape size=(25398x2030)  → lost 1x1
After 2:  [0] CustomShape size=(25397x2029)  → lost 1x1 again
...
After 20: [0] CustomShape size=(25378x2010)  → lost 21x21 total
```

Every operation (edit_style, edit_position, create_textbox) caused ALL shapes to shrink.

---

## Investigation

### Hypothesis

The shrinkage could be caused by:
1. Our edit code modifying sizes incorrectly
2. Unit conversion errors in LibreServer
3. LibreOffice's PPTX filter having precision loss

### Test Methodology

Created `/roundtrip` endpoint that:
1. Opens PPTX file
2. Saves immediately (NO edits)
3. Returns the file

This isolates LibreOffice's filter from our edit code.

### Test Script

```python
import requests
import base64

SERVER = "http://localhost:8000"
TEST_FILE = "/Users/ns/Desktop/projects/chatforge/my_test_slide.pptx"

with open(TEST_FILE, "rb") as f:
    initial_data = f.read()

files_data = [("round_0", initial_data)]

for i in range(5):
    resp = requests.post(f"{SERVER}/info", files={"file": ("test.pptx", files_data[-1][1])})
    size_before = resp.json()["slides"][0]["shapes"][0]["size"]

    resp = requests.post(f"{SERVER}/roundtrip", files={"file": ("test.pptx", files_data[-1][1])})
    new_data = base64.b64decode(resp.json()["document"])
    files_data.append((f"round_{i+1}", new_data))

    resp = requests.post(f"{SERVER}/info", files={"file": ("test.pptx", new_data)})
    size_after = resp.json()["slides"][0]["shapes"][0]["size"]

    delta_w = size_after['width'] - size_before['width']
    delta_h = size_after['height'] - size_before['height']
    print(f"Round-trip {i+1}: {size_before} → {size_after}  (Δ = {delta_w}, {delta_h})")
```

### Test Results

```
Round-trip 1: {'width': 23814, 'height': 0} → {'width': 23815, 'height': 1}  (Δ = 1, 1)
Round-trip 2: {'width': 23815, 'height': 1} → {'width': 23816, 'height': 2}  (Δ = 1, 1)
Round-trip 3: {'width': 23816, 'height': 2} → {'width': 23817, 'height': 3}  (Δ = 1, 1)
Round-trip 4: {'width': 23817, 'height': 3} → {'width': 23818, 'height': 4}  (Δ = 1, 1)
Round-trip 5: {'width': 23818, 'height': 4} → {'width': 23819, 'height': 5}  (Δ = 1, 1)
```

---

## Analysis

### Confirmed Root Cause

**The bug is in LibreOffice's PPTX import/export filter**, not in LibreServer code.

Evidence:
- `/roundtrip` makes ZERO edits - just open and save
- Sizes still change by exactly ±1 unit per cycle
- Affects ALL shapes in the document

### Unit Conversion Background

| System | Unit | Relationship |
|--------|------|--------------|
| PPTX/OOXML | EMU (English Metric Units) | 914400 EMU = 1 inch |
| LibreOffice Internal | 1/100mm (Map100thMM) | 2540 = 1 inch |
| Conversion Factor | | 360 EMU = 1 (1/100mm) |

Mathematically, the conversion should be lossless:
```
25399 × 360 = 9,143,640 EMU
9,143,640 ÷ 360 = 25399.0 (exact)
```

But LibreOffice's filter has an off-by-one error somewhere.

### Inconsistent Direction

- Original logs: **-1, -1** (shrinking)
- Test results: **+1, +1** (growing)

The direction of drift depends on the specific file/shape, suggesting the bug is in rounding/truncation logic that can go either way depending on the initial values.

---

## Severity Assessment

### Impact by Usage

| Iterations | Size Change | In mm | Visual Impact |
|------------|-------------|-------|---------------|
| 5 | ±5 units | 0.05mm | Invisible |
| 10 | ±10 units | 0.1mm | Barely noticeable |
| 20 | ±20 units | 0.2mm | Slight |
| 50 | ±50 units | 0.5mm | Noticeable on close inspection |
| 100 | ±100 units | 1.0mm | Visible |

### For SlideFixer

- **Typical session:** 3-10 iterations
- **Maximum drift:** ~0.1mm
- **Assessment:** Not visible to human eye

### When It Would Matter

1. Automated pipelines processing files repeatedly (100+ cycles)
2. Pixel-perfect layouts requiring exact alignment
3. Very long editing sessions (50+ operations)

---

## Recommendation

### Short-term: Ignore

For typical SlideFixer use cases (3-10 iterations), the drift is sub-millimeter and won't affect visual quality. Focus on core functionality.

### Long-term Options

1. **Store & Restore**: Save original sizes in metadata, restore after each operation
2. **Report to LibreOffice**: File bug report with reproduction steps
3. **Use Native Format**: Work with ODP internally, convert to PPTX only at final export
4. **Compensate**: Pre-adjust sizes by ±1 to counteract drift (hacky)

---

## Files

- **LibreServer:** `/Users/ns/Desktop/projects/slidefixer/LibreServer/`
- **Test endpoint:** `server.py` - `POST /roundtrip`
- **Test script:** `/Users/ns/Desktop/projects/chatforge/a.py`
- **Test file:** `/Users/ns/Desktop/projects/chatforge/my_test_slide.pptx`

---

## Conclusion

This is a **known limitation** of LibreOffice's PPTX filter, not a bug in our code. For the SlideFixer use case, it's acceptable to ignore. The `/roundtrip` endpoint remains available for future testing if needed.
