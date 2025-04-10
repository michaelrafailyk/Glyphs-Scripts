**About**

Python scripts for the [Glyphs font editor](http://glyphsapp.com/).

**Requirement**

- Glyphs
- Python

**Installing**

- Put the scripts into `~/Library/Application Support/Glyphs 3/Scripts` folder.
- Hold down the `Option` key and choose Script > Reload Scripts, or just press `Shift` `Opt` `Cmd` `Y` keys.

**Scripts**

# Align to Layer Horizontal Center

Align selection to horizontal center of the layer, also considering the italic angle.

![](Images/AlignToLayerHorizontalCenter.gif)

The script does not change the sidebearings to align the content, but only changes the x-coordinates of the selected elements.

The key feature of this script is how it analyzes bounds if an italic angle is specified. Each node in a selection is analyzed (even within components) to find the left and right extremes, respected to italic angle. And these extremes give the left origin and the width of the slanted bounds.

If a group of objects of different types (nodes, components, anchors, guides) is selected, they will be aligned to the center of the layer as a group, keeping the distance between the group elements.

Shortcut suggestion: `Shift` `Ctrl` `A`

# Flip Horizontal

Flip selection (or layer) horizontally, set the new first node (lowest left) and correct path direction.

Shortcut suggestion: `Shift` `Ctrl` `F`

# Flip Vertical

Flip selection (or layer) vertically, set the new first node (lowest left) and correct path direction.

Shortcut suggestion: `Shift` `Ctrl` `V`

# Rotate on 180 Degrees

Rotate selection (or layer) on 180 degrees, set the new first node (lowest left) and correct path direction.

Shortcut suggestion: `Shift` `Ctrl` `R`

# SVG to COLR

Convert Color layer to Color Palette layers.

If the font contains more than one master, please make sure the master with Color layer and the fallback master are active or specified in params, before starting. The script process all the glyphs by one pass. It may take up to 30 seconds depending on the design complexity and the count of glyphs.

Params:

- `colorLayerName` = "Master name"|None. Set the name like "Regular" to specify the Color layer to process, or None to use the selected master.
- `fallbackLayerName` = "Master name"|None. Set the master name like "Regular" to set it as the fallback layer, or None to use existed Color layer
- `groupSameColors` = True|False. Place the same colors on one layer if True, or on different layers if False.

The steps the script takes:

- Add an empty Color Palette to the Font Info.
- Get every path color from Color layer and add it to the Color Palette if it is not there yet.
- Check if the layer with such a color exist or not. It's also depends on the `groupSameColors` param (that is `True` by default) that you can set at the line 8 of the script.
- Copy path to a new Color Palette layer (or to an existed one depending on the previous step).
- Link the new Color Palette layer to the fallback layer.
- Add Color Palette layers with component parts to all composite glyphs.
- Focus on fallback layer if set in params.

# Add Color Palette layers to Components

It could be handy when you working on the COLR/CPAL font. So when you finished the base and mark glyphs and created composite glyphs like `/Aacute`, the components appears only on the fallback master layer. To export the color font properly, you also need to add an appropriate Color Palette layers with appropriate component color parts to this composite glyphs. This script automate it by adding a color components parts to all the glyphs builded with a components.

# Generate Kern Strings

Generate kern strings based on the Left and Right groups and add them into the Sample Texts. For example, for the left groups `C` `D` `c` `d` `three` `four` `.` `-` `c.sc` `d.sc` and right groups `A` `B` `a` `b` `one` `two` `.` `-` `a.sc` `b.sc` the kern strings will be:

- HH`A`CDcd34.-/c.sc/d.sc
- HH`B`CDcd34.-/c.sc/d.sc
- nn`a`CDcd34.-
- nn`b`CDcd34.-
- 00`1`CDcd34.-
- 00`2`CDcd34.-
- HH`.`CDcd34.-
- HH`-`CDcd34.-
- /h.sc/h.sc`/a.sc`/c.sc/d.sc
- /h.sc/h.sc`/b.sc`/c.sc/d.sc

The steps the script takes:

- Get unique left and right groups.
- Get one character attached to each group. Priority is given to characters whose name matches the name of the group. If the glyph don't have a character value (not a part of Unicode), the glyph name will be taken, like `/one.osf `.
- Sort the characters by `uppercase` `lowercase` `figure` `punctuation` `sc` `georgian` `armenian` `other` categories.
- Sort the characters inside these categories alphabetically (except of Georgian and Armenian because their letters are not named alphabetically).
- Print all the right and left groups to the Macro Panel output.
- Generate kern strings like `CC` `R` `LLLLLLLLL`, where `C` is a character to compare with (can be **HH** **nn** **00** **/h.sc/h.sc**), `R` is the one character from Right Groups (needed kerning to all the following ones), and `L` are all the characters from Left Groups (to kern with). For example, for the character `r` from Right Group, the first kern string may looks like: `nn` `r` `AHOJSTUVXYZaonftsuvxz01234589.?*-'//`.
- Add kern strings to the Sample Texts to the category named after the font family name.
- Open Edit view tab.
- Activate Text tool.
- Activate Show Group Members from View menu.
- Set kerning-only mode.
- Open Select Sample Texts panel and select the first string from added category.
- Set the caret position between the first kern pair (right after the main character).

# License

Copyright 2023 Michael Rafailyk (@michaelrafailyk).

Licensed under the Apache License, Version 2.0 (the "License"); you may not use the software provided here except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

See the License file included in this repository for further details.
