#MenuTitle: Add Color Palette layers to Components
__doc__="""
Add a color components parts to all the glyphs builded with a components.
"""

font = Glyphs.font
# the master with a Color Palette layers should be active/selected
id = font.selectedFontMaster.id
font.disableUpdateInterface()

# process all glyphs that have components
for glyph in font.glyphs:
	layer = glyph.layers[id]
	if layer.components:
		for component in layer.components:
			source = component.component.layers[layer.associatedMasterId].parent
			for sourceLayer in source.layers:
				# build a Color Palette layers in the same order as in the source of component
				if sourceLayer.attributes['colorPalette'] or sourceLayer.attributes['colorPalette'] == 0:
					newLayer = GSLayer()
					newLayer.attributes['colorPalette'] = sourceLayer.attributes['colorPalette']
					# link new Color Palette layer to appropriate master
					newLayer.associatedMasterId = id
					# add a color element from source as a component
					colorComponent = GSComponent(source)
					colorComponent.automaticAlignment = False
					colorComponent.x = component.x
					colorComponent.y = component.y
					newLayer.components.append(colorComponent)
					layer.parent.layers.append(newLayer)
					newLayer.syncMetrics()

font.enableUpdateInterface()
