#MenuTitle: Sync Automatic Alignment between masters
__doc__="""
Sync Automatic Alignments for components of a current master to specified reference master (Regular by default).
"""

# name of a reference master to compare the components alignment state
master_reference_name = 'Regular'

font = Glyphs.font
# get ids for selected master and for reference master
master_selected_id = font.selectedFontMaster.id
master_reference_id = False
# try to find reference master with defined name
for master in font.masters:
	if master.name == master_reference_name:
		master_reference_id = master.id
		break
# or get the first available reference master which is not selected one
if master_reference_id == False or master_reference_id == master_selected_id:
	for master in font.masters:
		if master.id != master_selected_id:
			master_reference_id = master.id
			break

font.disableUpdateInterface()

# check if the glyph contains components
for glyph in font.glyphs:
	layer_selected = glyph.layers[master_selected_id]
	if layer_selected.components:
		layer_reference = glyph.layers[master_reference_id]
		for i, component_selected in enumerate(layer_selected.components):
			component_reference = layer_reference.components[i]
			# sync component alignment of selected layer with reference layer
			if component_selected.alignment != component_reference.alignment:
				component_selected.alignment = component_reference.alignment

font.enableUpdateInterface()