# Manual Edit Instructions for Chunks 8-9

Due to file editing tool limitations, the following changes should be applied **manually** in a code editor.

## CHUNK 8: Light Mode CSS Refinement

**File**: `index.html`  
**Lines**: 28-39

**Replace this:**
```css
        :root {
            --bg-app: #f8fafc;
            --bg-card: #ffffff;
            --border: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.15);
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
        }
```

**With this:**
```css
        :root {
            --bg-app: #fafaf9;
            --bg-card: #fdfdfc;
            --border: #e7e5e4;
            --text-primary: #1c1917;
            --text-secondary: #78716c;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.12);
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
            --shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02);
            --shadow-lg: 0 8px 12px -3px rgba(0, 0, 0, 0.06), 0 3px 5px -4px rgba(0, 0, 0, 0.03);
        }
```

**Changes Summary**:
- Warmer off-white backgrounds (#fafaf9, #fdfdfc)
- Softer stone-gray borders (#e7e5e4)
- Warmer text colors (stone palette)
- Reduced shadow opacity for lighter appearance

---

## CHUNK 9: Copy/Label Improvements

These changes improve clarity for novice users. Find and replace the following labels:

Coming soon
