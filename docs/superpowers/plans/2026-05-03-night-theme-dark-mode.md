# Night Theme Dark Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the dark theme read clearly across the app by strengthening surface separation and visible borders, with the main menu as the priority validation surface.

**Architecture:** The implementation stays centered in the shared theme system so dialogs and the main menu inherit the same dark-mode hierarchy. Tests land first in the theme test module, then the palette/chrome derivation is updated in `src/config/theme.py`, and only after that are small widget-specific adjustments applied if shared styling still leaves gaps.

**Tech Stack:** Python 3.12, Tkinter/ttk, pytest, Ruff, Pyright

---

### Task 1: Lock the Dark Theme Expectations with Tests

**Files:**
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\tests\test_ui_theme_and_menu.py`
- Test: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\tests\test_ui_theme_and_menu.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_build_surface_palette_dark_mode_increases_surface_separation() -> None:
    palette = build_surface_palette(bg="#10161B", btn_bg="#1E2D38", fg="#F2F5F7")

    assert palette.panel_bg == "#21282f"
    assert palette.panel_alt_bg == "#2f3740"
    assert palette.panel_raised_bg == "#344450"
    assert palette.panel_border == "#3b4f5f"


def test_build_theme_chrome_enables_visible_outlines_in_dark_mode() -> None:
    chrome = build_theme_chrome("dark")

    assert chrome.card_borderwidth == 1
    assert chrome.card_relief == "solid"
    assert chrome.button_borderwidth == 1
    assert chrome.button_relief == "solid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: FAIL because the current dark palette and chrome still return flatter, less outlined values.

- [ ] **Step 3: Write minimal implementation**

```python
panel_bg = _blend_hex_colors(bg, "#ffffff", 0.09)
panel_alt_bg = _blend_hex_colors(bg, "#ffffff", 0.16)
panel_raised_bg = _blend_hex_colors(btn_bg, "#ffffff", 0.18)
panel_border = _blend_hex_colors(bg, "#79a7bf", 0.28)

return ThemeChrome(
    card_borderwidth=1,
    card_relief="solid",
    button_borderwidth=1,
    button_relief="solid",
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: PASS for the new dark-mode palette/chrome expectations.

- [ ] **Step 5: Commit**

```bash
git add tests/test_ui_theme_and_menu.py src/config/theme.py
git commit -m "Refine dark theme surface hierarchy"
```

### Task 2: Apply the Shared Dark Theme Improvements

**Files:**
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\src\config\theme.py`
- Test: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\tests\test_ui_theme_and_menu.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_surface_palette_dark_mode_keeps_buttons_distinct_from_cards() -> None:
    palette = build_surface_palette(bg="#10161B", btn_bg="#1E2D38", fg="#F2F5F7")

    assert palette.panel_alt_bg != "#1E2D38"
    assert palette.tree_heading_bg == palette.panel_alt_bg
    assert palette.listbox_border == palette.panel_border
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: FAIL if the derived dark surfaces still remain too close to the button layer.

- [ ] **Step 3: Write minimal implementation**

```python
btn_hover = _blend_hex_colors(btn_bg, "#ffffff", 0.18)
btn_pressed = _blend_hex_colors(btn_bg, bg, 0.18)

style.configure(
    "Card.TFrame",
    background=palette.panel_bg,
    relief=chrome.card_relief,
    borderwidth=chrome.card_borderwidth,
    bordercolor=palette.panel_border,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: PASS with cards, raised surfaces, and buttons mapped onto separate dark-mode layers.

- [ ] **Step 5: Commit**

```bash
git add src/config/theme.py tests/test_ui_theme_and_menu.py
git commit -m "Polish shared dark ttk styling"
```

### Task 3: Align the Main Menu and Shared Text Widgets

**Files:**
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\src\frontend\ui_main_menu.py`
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\src\frontend\text_widgets.py`
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\CHANGELOG.md`
- Test: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\tests\test_ui_theme_and_menu.py`

- [ ] **Step 1: Write the failing test**

```python
def test_main_menu_hero_uses_panel_border_for_consistent_dark_chrome() -> None:
    source = Path("src/frontend/ui_main_menu.py").read_text(encoding="utf-8")

    assert 'highlightbackground=palette.panel_border' in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: FAIL because the hero currently still uses `panel_highlight` as its outer line.

- [ ] **Step 3: Write minimal implementation**

```python
hero_frame = tk.Frame(
    main_frame,
    bg=palette.hero_bg,
    highlightthickness=1,
    highlightbackground=palette.panel_border,
    padx=18,
    pady=16,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: PASS, with the main menu hero inheriting the calmer shared dark border language.

- [ ] **Step 5: Commit**

```bash
git add src/frontend/ui_main_menu.py src/frontend/text_widgets.py tests/test_ui_theme_and_menu.py CHANGELOG.md
git commit -m "Tune dark mode menu chrome"
```

### Task 4: Final Verification and Project Hygiene

**Files:**
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\src\config\theme.py`
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\src\frontend\ui_main_menu.py`
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\src\frontend\text_widgets.py`
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\tests\test_ui_theme_and_menu.py`
- Modify: `C:\Users\aleja\Documents\trans_tools\worktrees\codex-dark-night-theme\CHANGELOG.md`

- [ ] **Step 1: Run focused theme tests**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest tests\test_ui_theme_and_menu.py -q`
Expected: PASS with all dark-theme expectations green.

- [ ] **Step 2: Run the full test suite**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m pytest -q`
Expected: PASS with `0` failures.

- [ ] **Step 3: Run Ruff fixes**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m ruff check . --fix`
Expected: PASS with no remaining lint errors.

- [ ] **Step 4: Run Ruff formatting**

Run: `C:\Users\aleja\Documents\trans_tools\.venv\Scripts\python.exe -m ruff format .`
Expected: PASS with formatting updated where needed.

- [ ] **Step 5: Run Pyright**

Run: `pyright`
Expected: PASS with `0 errors, 0 warnings, 0 informations`.
