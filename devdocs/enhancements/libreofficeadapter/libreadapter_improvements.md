# LibreOffice Adapter Improvements

This document tracks known limitations and required improvements for the LibreOffice adapter (LibreServer + chatforge adapter layer).

## Current Architecture

```
SlideFixer → ArtifactEditorAgentService → LibreOfficeEditorDockerServerAdapter → LibreServer (Docker)
                                                                                      ↓
                                                                               LibreOffice UNO API
```

## Important Note

**All limitations listed below are IMPLEMENTATION limitations, not UNO API limitations.**

The LibreOffice UNO API supports all the features we need. We simply haven't implemented the endpoints in LibreServer yet. This means extending LibreServer is the right path forward - no fundamental redesign needed.

## UNO Capability vs Implementation Status

| Feature | UNO Supports | LibreServer Has | Gap |
|---------|--------------|-----------------|-----|
| Get shape info | ✅ | ✅ | ✅ Fixed - now includes text + font |
| Edit text (any shape) | ✅ | ✅ | ✅ Fixed - works on CustomShape |
| Edit font/style | ✅ | ✅ | ✅ Fixed - works on CustomShape |
| Edit size | ✅ | ✅ | - |
| Edit position | ✅ | ✅ | Bug: position ignored |
| Create textbox | ✅ | ✅ | Bug: position ignored |
| Delete shape | ✅ | ✅ | ✅ Fixed - DELETE /edit/shape |
| Edit fill/background | ✅ | ✅ | ✅ Fixed - POST /edit/fill |
| Insert image | ✅ | ✅ | ✅ Fixed - POST /insert/image |
| Edit paragraph | ✅ | ✅ | ✅ Fixed - POST /edit/paragraph |
| Edit table cell | ✅ | ✅ | ✅ Fixed - POST /edit/table_cell |

**Conclusion**: 100% of required features are supported by UNO. Implementation work will unlock full capability.

---

## Critical Issues

### 1. get_artifact_info Does Not Return Text Content

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
The `/info` endpoint returns shape metadata but NOT the actual text content inside shapes.

**Current output**:
```
[0] CustomShape position=(508, 254) size=(25399x2031)
[1] CustomShape position=(1270, 3048) size=(7619x1269)
```

**Required output**:
```
[0] CustomShape position=(508, 254) size=(25399x2031)
    text="quarterly sales report - q4 2024"
    font="Times New Roman" size=18pt color=#666666
[1] CustomShape position=(1270, 3048) size=(7619x1269)
    text="Here are the key findings from Q4..."
    font="Arial" size=12pt color=#333333
```

**Impact**:
- LLM agent is blind to actual slide content
- Cannot make informed edit decisions
- Cannot verify if edits succeeded

**Fix (LibreServer)**:
```python
def get_shape_text(shape):
    """Extract text from any shape type."""
    try:
        text_obj = shape.getText()
        if text_obj:
            return text_obj.getString()
    except:
        pass
    return None

def get_shape_font_info(shape):
    """Extract font information from shape."""
    try:
        text_obj = shape.getText()
        if text_obj:
            cursor = text_obj.createTextCursor()
            cursor.gotoStart(False)
            return {
                "font_name": cursor.getPropertyValue("CharFontName"),
                "font_size": cursor.getPropertyValue("CharHeight"),
                "font_color": cursor.getPropertyValue("CharColor"),
            }
    except:
        pass
    return None
```

---

### 2. edit_text Fails on CustomShape

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
`/edit/text` endpoint returns 400 Bad Request when called on `CustomShape` type shapes.

**Observed behavior**:
```
edit_text(slide_index=0, shape_index=0, new_text="Title")
→ Error: 400 Bad Request
```

**Root cause**:
The current implementation likely only handles shapes with explicit `TextShape` service, not the more generic `CustomShape` which stores text differently.

**Fix (LibreServer)**:
```python
def edit_text(slide_index, shape_index, new_text):
    shape = get_shape(slide_index, shape_index)

    # Try generic text access (works for most shapes)
    text_obj = shape.getText()
    if text_obj:
        text_obj.setString(new_text)
        return success

    # Fallback for shapes without getText()
    if shape.supportsService("com.sun.star.drawing.TextShape"):
        shape.setString(new_text)
        return success

    raise UnsupportedShapeType(f"Cannot edit text on {shape.getShapeType()}")
```

---

### 3. edit_style Fails on CustomShape

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
`/edit/style` endpoint returns 400 Bad Request when called on `CustomShape` type shapes.

**Required capabilities**:
- Change font family
- Change font size
- Change font color
- Change font weight (bold/normal)
- Change text alignment

**Fix (LibreServer)**:
```python
def edit_style(slide_index, shape_index, font_name=None, font_size=None, font_color=None, bold=None):
    shape = get_shape(slide_index, shape_index)

    text_obj = shape.getText()
    if not text_obj:
        raise UnsupportedShapeType("Shape has no text content")

    cursor = text_obj.createTextCursor()
    cursor.gotoStart(False)
    cursor.gotoEnd(True)  # Select all text

    if font_name:
        cursor.setPropertyValue("CharFontName", font_name)
    if font_size:
        cursor.setPropertyValue("CharHeight", font_size)
    if font_color:
        cursor.setPropertyValue("CharColor", parse_color(font_color))
    if bold is not None:
        from com.sun.star.awt.FontWeight import BOLD, NORMAL
        cursor.setPropertyValue("CharWeight", BOLD if bold else NORMAL)
```

---

### 4. Missing delete_shape Capability

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
No endpoint exists to delete a shape from a slide. This prevents the "delete & recreate" fallback pattern.

**Required endpoint**:
```
DELETE /edit/shape
{
  "slide_index": 0,
  "shape_index": 2
}
```

**Use case**:
When edit_text/edit_style fail, the agent could:
1. Delete the problematic shape
2. Create a new textbox with correct content/styling

**Fix (LibreServer)**:
```python
@app.delete("/edit/shape")
def delete_shape(slide_index: int, shape_index: int):
    slide = get_slide(slide_index)
    shape = slide.getDrawPages().getByIndex(0).getByIndex(shape_index)
    slide.getDrawPages().getByIndex(0).remove(shape)
    return {"status": "success"}
```

**Note**: Shape indices shift after deletion. Agent must re-fetch artifact_info.

---

### 5. Shape Type Awareness

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
The adapter doesn't distinguish between shape types or communicate capabilities per type.

**LibreOffice shape types**:
| Shape Type | getText() | setString() | Style Editable | Notes |
|------------|-----------|-------------|----------------|-------|
| CustomShape | ✓ | via getText() | ✓ | Most common |
| TextShape | ✓ | ✓ | ✓ | Simple text |
| TitleTextShape | ✓ | ✓ | ✓ | Slide titles |
| TableShape | Special | Special | ✓ | Cell-by-cell |
| GraphicShape | ✗ | ✗ | ✗ | Images |
| ConnectorShape | ✗ | ✗ | ✗ | Lines/arrows |
| OLE2Shape | ✗ | ✗ | ✗ | Embedded objects |

**Improvement**:
- Return shape type in get_artifact_info
- Return capability flags per shape
- Better error messages indicating why edit failed

---

## Medium Priority Issues

### 6. No Background/Fill Color Editing

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
Cannot change shape background/fill color. Important for fixing contrast issues.

**Use case**: Perception identifies "poor contrast - dark text on dark background". Need to change background to brand color.

**UNO supports this**: ✅ Yes

**Required endpoint**:
```
POST /edit/fill
{
  "slide_index": 0,
  "shape_index": 3,
  "fill_color": "#0D47A1",
  "fill_style": "solid"  // or "none", "gradient"
}
```

**Fix (LibreServer)**:
```python
from com.sun.star.drawing.FillStyle import SOLID, NONE

def edit_fill(slide_index, shape_index, fill_color, fill_style="solid"):
    shape = get_shape(slide_index, shape_index)

    if fill_style == "none":
        shape.setPropertyValue("FillStyle", NONE)
    else:
        shape.setPropertyValue("FillStyle", SOLID)
        shape.setPropertyValue("FillColor", parse_color(fill_color))
```

---

### 7. No Paragraph-Level Styling

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
Current edit_style applies to entire shape. Cannot style individual paragraphs or bullet points differently.

**Use case**: Perception identifies "inconsistent fonts in bullet list". Need to change each bullet individually.

**UNO supports this**: ✅ Yes

**Required capabilities**:
- Edit specific paragraph by index
- Change bullet style
- Change paragraph spacing
- Change indentation

**Required endpoint**:
```
POST /edit/paragraph
{
  "slide_index": 0,
  "shape_index": 2,
  "paragraph_index": 1,
  "font_name": "Arial",
  "font_size": 12,
  "bullet_char": "•",
  "indent": 0.5
}
```

**Fix (LibreServer)**:
```python
def edit_paragraph(slide_index, shape_index, paragraph_index, **kwargs):
    shape = get_shape(slide_index, shape_index)
    text = shape.getText()

    # Enumerate paragraphs
    enum = text.createEnumeration()
    para_idx = 0
    while enum.hasMoreElements():
        para = enum.nextElement()
        if para_idx == paragraph_index:
            # Apply styles to this paragraph
            if kwargs.get("font_name"):
                para.setPropertyValue("CharFontName", kwargs["font_name"])
            if kwargs.get("font_size"):
                para.setPropertyValue("CharHeight", kwargs["font_size"])
            if kwargs.get("bullet_char"):
                para.setPropertyValue("NumberingType", 6)  # CHAR_SPECIAL
                para.setPropertyValue("BulletChar", kwargs["bullet_char"])
            break
        para_idx += 1
```

---

### 8. Table Cell Editing

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
TableShape requires cell-by-cell editing. Current API doesn't support this.

**Use case**: Perception identifies "table styling inconsistent". Need to change header row background, cell text, etc.

**UNO supports this**: ✅ Yes

**Required endpoint**:
```
POST /edit/table_cell
{
  "slide_index": 2,
  "shape_index": 5,
  "row": 0,
  "col": 1,
  "text": "New Value",
  "font_name": "Arial",
  "font_size": 12,
  "background_color": "#0D47A1"
}
```

**Fix (LibreServer)**:
```python
def edit_table_cell(slide_index, shape_index, row, col, **kwargs):
    shape = get_shape(slide_index, shape_index)

    # Access cell
    cell = shape.getCellByPosition(col, row)

    # Edit text
    if kwargs.get("text"):
        cell.setString(kwargs["text"])

    # Edit cell background
    if kwargs.get("background_color"):
        cell.setPropertyValue("FillColor", parse_color(kwargs["background_color"]))

    # Edit text style
    text = cell.getText()
    cursor = text.createTextCursor()
    cursor.gotoStart(False)
    cursor.gotoEnd(True)

    if kwargs.get("font_name"):
        cursor.setPropertyValue("CharFontName", kwargs["font_name"])
    if kwargs.get("font_size"):
        cursor.setPropertyValue("CharHeight", kwargs["font_size"])
```

---

### 9. Image/Logo Insertion

**Status**: ✅ Fixed (see LibreServer/server.py)

**Problem**:
Cannot insert images (logos, icons). Required for branding compliance fixes.

**Use case**: Perception identifies "company logo missing from bottom-right". Need to insert logo image.

**UNO supports this**: ✅ Yes

**Required endpoint**:
```
POST /insert/image
{
  "slide_index": 0,
  "x": 25400,
  "y": 17780,
  "width": 1524,
  "height": 1524,
  "image_data": "<base64>",
  "image_type": "png"
}
```

**Fix (LibreServer)**:
```python
import base64
import tempfile

def insert_image(slide_index, x, y, width, height, image_data, image_type="png"):
    doc = get_document()
    slide = doc.getDrawPages().getByIndex(slide_index)

    # Create graphic shape
    graphic_shape = doc.createInstance("com.sun.star.drawing.GraphicObjectShape")

    # Write image data to temp file (UNO needs file path or URL)
    with tempfile.NamedTemporaryFile(suffix=f".{image_type}", delete=False) as f:
        f.write(base64.b64decode(image_data))
        temp_path = f.name

    # Set graphic URL
    graphic_shape.GraphicURL = f"file://{temp_path}"

    # Set position and size
    graphic_shape.setPosition(Point(x, y))
    graphic_shape.setSize(Size(width, height))

    # Add to slide
    slide.add(graphic_shape)

    # Clean up temp file
    os.unlink(temp_path)
```

---

## Bugs Identified From Logs

### 13. Shape Sizes Drift With Each Operation

**Status**: 🟡 Confirmed - LibreOffice Bug (Acceptable to Ignore)

**Problem**:
Every operation causes ALL shapes to change size by ±1 unit per dimension.

**Root cause**: Bug in LibreOffice's PPTX import/export filter, NOT in LibreServer code.

**Evidence**: See [size_drift_bug_investigation.md](./size_drift_bug_investigation.md)

**Test results** (using `/roundtrip` endpoint with NO edits):
```
Round-trip 1: {'width': 23814, 'height': 0} → {'width': 23815, 'height': 1}  (Δ = +1, +1)
Round-trip 2: {'width': 23815, 'height': 1} → {'width': 23816, 'height': 2}  (Δ = +1, +1)
Round-trip 3: {'width': 23816, 'height': 2} → {'width': 23817, 'height': 3}  (Δ = +1, +1)
```

**Severity**: Low for typical use (5-10 iterations = 0.05-0.1mm drift, invisible to eye)

**Decision**: Ignore for now. Focus on core functionality.

---

### 14. create_textbox Position Ignored

**Status**: 🔴 Critical Bug

**Problem**:
When creating a textbox, the specified position is ignored. The shape ends up at a default location.

**Evidence**:
```python
# Requested:
create_textbox(x=32512, y=17272, ...)

# Result:
[7] TitleTextShape text="Company Logo"
    position=(1693, 758)  # ← NOT where we asked!
```

All created textboxes appear at ~(1693, 7xx) regardless of requested position.

---

### 15. edit_text/edit_style Work ONLY on TitleTextShape

**Status**: 🟡 Important (Clarification)

**Observation from logs**:
- `edit_style` on CustomShape → **FAILS**
- `edit_style` on TitleTextShape → **SUCCESS**
- `edit_text` on TitleTextShape → **SUCCESS**

The adapter DOES work, but only for shapes created via `create_textbox`. Original PowerPoint shapes (CustomShape) cannot be edited.

**Workaround confirmed**: Create new textbox → then edit_style/edit_text works on it.

---

### 16. No Way to Remove Duplicate Shapes

**Status**: 🟡 Important

**Problem**:
Without `delete_shape`, the LLM creates duplicates it can't clean up.

**Evidence**:
```
Slide 0: 7 shapes (original)
Slide 0: 14 shapes (after edits - full of duplicates)

Multiple "Confidential - Acme Corp" textboxes:
  [10] TitleTextShape text="Confidential - Acme Corp"
  [11] TitleTextShape text="Confidential - Acme Corp"
  [12] TitleTextShape text="Confidential - Acme Corp"
```

---

## Lower Priority Issues

### 17. No Undo/Rollback

**Status**: 🔵 Low

**Problem**:
If an edit makes things worse, no way to undo without keeping full artifact history.

**Consideration**:
- Could implement via version snapshots in LibreServer
- Or handle at SlideFixer level (we already track history)

---

### 18. Batch Operations

**Status**: 🔵 Low

**Problem**:
Each edit requires separate HTTP request. Slow for multiple changes.

**Improvement**:
```
POST /edit/batch
{
  "operations": [
    {"type": "edit_text", "slide_index": 0, "shape_index": 0, "new_text": "..."},
    {"type": "edit_style", "slide_index": 0, "shape_index": 0, "font_name": "Arial"},
    {"type": "edit_fill", "slide_index": 0, "shape_index": 3, "fill_color": "#0D47A1"}
  ]
}
```

---

### 19. Master Slide / Template Support

**Status**: 🔵 Low

**Problem**:
Cannot edit master slides or apply consistent templates.

**Use case**:
- Set default fonts for entire presentation
- Apply company template

---

## Implementation Priority

All features below are UNO-supported and implementable.

### Phase 0: Critical Bugs (Immediate)
- 🔴 #13: Fix shape size shrinking bug (unit conversion issue)
- 🔴 #14: Fix create_textbox position being ignored

### Phase 1: Core Editing (Week 1) - Enables ~60% of fixes
- 🔴 #1: get_artifact_info returns text content
- 🔴 #2: edit_text works on CustomShape
- 🔴 #3: edit_style works on CustomShape
- 🟡 #4: Add delete_shape endpoint

### Phase 2: Visual Styling (Week 2) - Enables ~80% of fixes
- 🟡 #6: edit_fill for background colors (contrast fixes)
- 🟡 #9: insert_image for logos (branding requirement)
- 🔵 #5: Shape type awareness and better errors

### Phase 3: Advanced Editing (Week 3+) - Enables ~100% of fixes
- 🔵 #7: Paragraph-level styling (bullet formatting)
- 🔵 #8: Table cell editing
- 🔵 #17-19: Undo, batch operations, master slides

---

## Testing Checklist

When implementing fixes, test against these shape types:
- [ ] CustomShape with text
- [ ] CustomShape without text (pure graphic)
- [ ] TitleTextShape
- [ ] TextShape (subtitle, body)
- [ ] TableShape
- [ ] Shapes inside groups
- [ ] Shapes with multiple paragraphs
- [ ] Shapes with mixed formatting

---

## Summary From Tool Call Logs

### What Works
| Operation | CustomShape | TitleTextShape |
|-----------|-------------|----------------|
| get_artifact_info | ✓ (no text) | ✓ (with text) |
| edit_text | ✗ 400 | ✓ |
| edit_style | ✗ 400 | ✓ |
| edit_size | ✓ | ✓ |
| edit_position | ✓ | ✓ |
| create_textbox | ✓ (creates TitleTextShape) | n/a |

### LLM Workaround Pattern (Current)
```
1. Try edit_text on CustomShape → FAIL
2. Try edit_style on CustomShape → FAIL
3. create_textbox with desired content → SUCCESS (but wrong position)
4. edit_style on new TitleTextShape → SUCCESS
5. Result: Original content still exists, new content overlays it
```

### Key Insight
The adapter **can** edit text and styles, but **only on shapes it creates**.
Original PowerPoint shapes (`CustomShape`) are read-only for text/style operations.

---

## Related Files

**LibreServer** (external repo):
- `main.py` - API endpoints
- `uno_utils.py` - UNO API helpers

**Chatforge Adapter**:
- `chatforge/adapters/artifact_editor/libreoffice.py`
- `chatforge/services/artifact_editor_agent/service.py`

**SlideFixer**:
- `slidefixer/llmservice.py` - Creates editor agent
- `slidefixer/fixer.py` - Fix loop
