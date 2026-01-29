# KumiAI Screenshots

This directory contains screenshots and visual assets for the project documentation.

## Required Screenshots

To complete the open source publication, please add the following screenshots:

### 1. `kanban.png` - Kanban Workflow View
- **What to capture**: The Kanban board showing project management
- **How to capture**:
  1. Start KumiAI (frontend and backend)
  2. Navigate to a project with the Kanban view
  3. Ensure the board shows multiple columns and cards
  4. Take a full-window screenshot
  5. Save as `assets/kanban.png`

### 2. `running.png` - Application Running View
- **What to capture**: The main interface with active sessions
- **How to capture**:
  1. Start KumiAI with an active agent session
  2. Show the chat interface with messages
  3. Capture the full application window
  4. Save as `assets/running.png`

### 3. `agents.png` (Optional) - Agents Management
- **What to capture**: The agents page showing multiple agents
- **Recommended**: Shows how users manage their AI team

### 4. `skills.png` (Optional) - Skills Library
- **What to capture**: The skills management interface
- **Recommended**: Shows the skill library and import features

## Screenshot Guidelines

### Quality Standards
- **Resolution**: At least 1920x1080 (Full HD)
- **Format**: PNG (for crisp UI elements)
- **File size**: Aim for < 500KB (compress if needed)
- **Clean UI**: Remove any personal data or API keys

### Tools for Screenshots
- **macOS**: Cmd+Shift+4, then Space (window capture)
- **Windows**: Windows+Shift+S
- **Linux**: gnome-screenshot or spectacle

### Tools for Compression (if needed)
- **TinyPNG**: https://tinypng.com/
- **ImageOptim** (macOS): https://imageoptim.com/
- **pngquant**: Command-line tool

## Adding Screenshots

Once you've captured the screenshots:

1. Save them in this directory with the correct names
2. Verify they're referenced in `README.md`
3. Check file sizes (< 500KB each)
4. Test that images display correctly on GitHub

## Verification

After adding screenshots, verify with:

```bash
# Check screenshots exist
ls -lh assets/*.png

# Check if they're referenced in README
grep -r "assets/" README.md
```

## Need Help?

If you're having trouble capturing screenshots:
1. Start the application with sample data
2. Use a clean browser window
3. Capture during daytime (better lighting)
4. Consider using a tool like Shottr (macOS) or Greenshot (Windows)

---

**Status**: Screenshots needed before publication
**Priority**: HIGH - Required for open source release
