# Night Theme Dark Mode Design

## Goal

Improve the night theme so panels, borders, buttons, inputs, tables, and the main menu all read clearly as separate surfaces without losing the dark overall look.

## Problem Summary

The current dark theme is usable but visually too flat in important places:

- cards and the window background are too close in value
- some dark-mode borders are missing or too subtle
- buttons blend too much into their parent panels
- the top hero area on the main menu feels visually disconnected from the rest of the screen
- shared widgets such as entries, comboboxes, trees, listboxes, and multiline text areas do not all communicate the same surface hierarchy

The result is that the main menu, and likely several dialogs, feel low-contrast in structure even when text remains readable.

## Scope

This change covers the whole application theme in dark mode, with the main menu treated as the visual priority.

Included:

- shared dark-mode palette tokens
- shared border and relief behavior for ttk widgets
- shared colors for text widgets, listboxes, trees, notebook tabs, scrollbars, and labeled sections
- any small main-menu-specific adjustment still needed after the shared theme update
- automated tests for the revised dark theme behavior

Not included:

- redesigning the light theme
- changing app layout structure
- introducing a new theme mode beyond the existing `dark` and `light`
- one-off styling patches across many dialogs unless the shared theme still leaves a specific problem visible

## Recommended Approach

Keep the existing dark theme as the base, but strengthen its hierarchy through the shared theme system instead of patching individual windows first.

The implementation should:

1. Increase the separation between background, standard panels, raised panels, and active input surfaces.
2. Make borders visible in dark mode as well as light mode.
3. Keep border colors muted and professional rather than bright or decorative.
4. Reuse the shared theme across the app so the menu and dialogs stay visually aligned.
5. Only add menu-specific tweaks if the shared theme changes do not fully resolve the captured issues.

## Visual Direction

The dark theme should remain calm and subdued, but it needs clearer structural contrast.

Target visual behavior:

- app background remains the darkest layer
- cards and grouped panels sit above the background with a visible but restrained separation
- elevated panels and interactive surfaces are distinguishable from standard cards
- buttons read as intentional controls rather than flat rectangles inside a card
- borders are visible enough to define structure without looking harsh
- focus and hover states are more prominent than base borders but do not overpower them

## Files to Change

### Primary

- `src/config/theme.py`
  - revise dark-mode palette derivation
  - enable visible dark-mode card borders
  - tighten shared ttk border, relief, hover, and focus styling

### Secondary

- `src/frontend/ui_main_menu.py`
  - adjust any menu-only chrome still needed after shared theme changes, especially the hero section

- `src/frontend/text_widgets.py`
  - keep multiline `Text` widgets aligned with the revised dark-mode borders and selection contrast

- `src/frontend/ui_dialogs/section_widgets.py`
  - ensure reusable collapsible and scrollable sections inherit the improved hierarchy cleanly

### Tests

- `tests/test_ui_theme_and_menu.py`
  - extend coverage for dark-mode surface separation, visible borders, and shared chrome expectations

### Documentation

- `CHANGELOG.md`
  - record the dark-theme polish update if implementation changes are made

## Detailed Design

### 1. Shared palette changes

In `build_surface_palette`, dark mode should use stronger separation between:

- `bg`
- `panel_bg`
- `panel_alt_bg`
- `panel_raised_bg`
- `entry_bg`

The chosen values should still belong to the same dark family, but they should no longer collapse into a nearly uniform block.

The dark-mode border color should be:

- darker and calmer than a bright highlight
- lighter than the background enough to remain visible
- reusable across cards, entries, trees, listboxes, and scrollbars

### 2. Shared chrome changes

In `build_theme_chrome`, dark mode should no longer use borderless cards. The theme should provide real outlines in dark mode, likely with:

- `card_borderwidth >= 1`
- visible card relief or solid outlines
- visible button borders where needed

The outcome should be that dark-mode cards and controls are defined by both fill and edge, not fill alone.

### 3. Shared ttk styling changes

In `configure_ttk_styles`, dark-mode updates should affect these shared surfaces:

- `Card.TFrame`
- `RaisedCard.TFrame`
- `Toolbar.TFrame`
- `TLabelframe`
- `TButton`, `MenuCard.TButton`, `Utility.TButton`, `Danger.TButton`, `Accent.TButton`, `SummaryToggle.TButton`
- `TEntry`
- `TCombobox`
- `TSpinbox`
- `Treeview`
- `Treeview.Heading`
- `TNotebook.Tab`
- `TScrollbar`

The dark theme should especially improve:

- panel edge visibility
- separation between card fills and button fills
- input outlines
- table and heading containment
- scrollbar visibility against dark troughs

### 4. Main menu polish

The main menu is the user-visible priority and should be checked after the shared theme changes.

Likely areas:

- hero background and its border/highlight relation to the rest of the page
- spacing and contrast between top summary card and the section cards below
- visual distinction between neutral buttons and the exit button

The menu should not need a custom style system; only small adjustments are acceptable if the shared theme still leaves it looking flat.

### 5. Text and reusable section widgets

Shared non-ttk widgets should not lag behind the new theme:

- `configure_notes_widget` should keep multiline text areas consistent with the new border and focus treatment
- collapsible section headers and bodies should still read clearly when placed inside dark dialogs
- listboxes should remain aligned with shared dark borders and selection colors

## Testing Strategy

Add or update unit tests in `tests/test_ui_theme_and_menu.py` to verify:

- dark preset still resolves correctly
- dark palette surfaces remain distinct from one another
- dark borders are intentionally visible
- dark theme chrome uses real outlines for cards and buttons
- key derived colors remain stable enough to protect against regressions

Manual validation should focus first on:

- main menu in dark mode
- at least one dialog with text inputs
- at least one dialog with list/table content
- at least one dialog with collapsible sections

## Risks and Mitigations

### Risk: over-bright dark mode

If surfaces are separated too aggressively, the app may stop feeling like a dark theme.

Mitigation:

- keep the palette in the same hue family
- prefer small but meaningful value changes
- avoid bright border colors except for focus/highlight states

### Risk: menu improves but dialogs drift

If the solution relies too much on menu-only tweaks, the rest of the app may still feel inconsistent.

Mitigation:

- implement shared theme changes first
- use menu-specific changes only as final polish

### Risk: brittle color tests

If tests pin too many exact colors, future iteration becomes painful.

Mitigation:

- test the most important shared tokens and chrome behavior
- avoid snapshot-like over-specification for every derived value

## Success Criteria

This work is successful when:

- the dark main menu shows clearly separated panels and visible borders
- buttons no longer visually disappear into their parent cards
- shared dark-mode inputs, tables, and listboxes look consistent with the menu
- the overall theme still feels dark, calm, and cohesive
- automated theme tests cover the new dark-mode expectations
