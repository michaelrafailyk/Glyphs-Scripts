# MenuTitle: Add Ghost Hints for Unicase Font
from GlyphsApp import Glyphs, GSHint, OFFCURVE

__doc__ = """
Add unattached ghost hints at baseline and cap height for glyphs containing nodes at both of these vertical positions
"""

font = Glyphs.font
# If "Get Hints From Master" parameter is presented, use that master for getting zones and hint only him
# Otherwise, use selected master for getting zones and hint all masters
get_hints_from_master_id = font.customParameters["Get Hints From Master"]
hint_master = None
if get_hints_from_master_id:
	for m in font.masters:
		if m.id == get_hints_from_master_id:
			hint_master = m
			break
else:
	hint_master = font.selectedFontMaster
# Decide which masters to process
if get_hints_from_master_id:
	target_masters = [hint_master]
else:
	target_masters = font.masters
# Get zones positions and sizes
baseline_position = 0
baseline_size = 0
capheight_position = hint_master.capHeight
capheight_size = 0
for zone in hint_master.alignmentZones:
	if zone.position == baseline_position:
		baseline_size = zone.size
	elif zone.position == capheight_position:
		capheight_size = zone.size
# Helpers
def has_node_inside_zone(layer, position, size):
	zone_min = min(position, position + size)
	zone_max = max(position, position + size)
	for path in layer.paths:
		for node in path.nodes:
			if node.type != OFFCURVE:
				if zone_min <= node.y <= zone_max:
					return node.y
	return None
def add_horizontal_hint(layer, position, direction):
	hint = GSHint()
	hint.position = position
	if direction == 'up':
		hint.type = -1
	elif direction == 'down':
		hint.type = 1
	layer.hints.append(hint)

font.disableUpdateInterface()
try:
	# Process target masters
	for glyph in font.glyphs:
		for master in target_masters:
			layer = glyph.layers[master.id]
			if not layer.paths:
				continue
			# If glyph has a nodes inside both baseline zone and cap height zone
			baseline_zone_node_y = has_node_inside_zone(layer, baseline_position, baseline_size)
			capheight_zone_node_y = has_node_inside_zone(layer, capheight_position, capheight_size)
			if baseline_zone_node_y is not None and capheight_zone_node_y is not None:
				add_horizontal_hint(layer, baseline_position, 'down')
				add_horizontal_hint(layer, capheight_position, 'up')
finally:
	font.enableUpdateInterface()
