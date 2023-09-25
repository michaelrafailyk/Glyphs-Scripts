#MenuTitle: SVG to COLR
__doc__="""
Convert Color layer to Color Palette layers
"""



# params
# set the name like "Regular" to specify the Color layer to process, or None to use the selected master
colorLayerName = None
# set the master name like "Regular" to use it as the fallback, or None to use existed Color layer
fallbackLayerName = None
# place the same colors on one layer if True, or on different layers if False
groupSameColors = True


font = Glyphs.font
font.disableUpdateInterface()

# if the font contains more than one master, please make sure the master with Color layer is active or specified on params
activeMasterId = font.selectedFontMaster.id
if colorLayerName:
	for master in font.masters:
		if master.name == colorLayerName:
			activeMasterId = master.id

# add an empty Color Palette to the Font Info
if not Glyphs.font.customParameters["Color Palettes"]:
	Glyphs.font.customParameters["Color Palettes"] = NSMutableArray.arrayWithObjects_([])

# process all the glyphs at once
for glyph in Glyphs.font.glyphs:
	layer = glyph.layers[activeMasterId]
	if layer.attributes['color']:
		if not fallbackLayerName:
			# remove Color layer attribute and made it the fallback layer
			layer.attributes['color'] = None
		# get the fallback layer id for linking a Color palette layers to him
		fallbackMasterId = font.fontMasterAtIndex_(font.masterIndex).id
		fallbackMasterIndex = font.masterIndex
		if fallbackLayerName:
			for master in font.masters:
				if master.name == fallbackLayerName:
					fallbackMasterId = master.id
					fallbackMasterIndex = font.masters.index(master)
					break
		for path in layer.paths:
			# get the path color
			color = path.attributes['fillColor']
			if not fallbackLayerName:
				# clear the color info on the fallback layer
				path.attributes['fillColor'] = None
			# add the color to the Palette if it is not there yet
			if color not in Glyphs.font.customParameters["Color Palettes"][0]:
				Glyphs.font.customParameters["Color Palettes"][0].append(color)
			# get the color index from the Palette
			colorIndex = 0
			for paletteColor in Glyphs.font.customParameters["Color Palettes"][0]:
				if color == paletteColor:
					colorIndex = Glyphs.font.customParameters["Color Palettes"][0].index(paletteColor)
					break
			# check if the Color Palette layer with such a color exist or not
			existedLayer = False;
			if groupSameColors:
				for sublayer in layer.parent.layers:
					if sublayer.name == 'Color ' + str(colorIndex):
						existedLayer = sublayer
						break
			if not existedLayer:
				# copy to a new Color Palette layer
				newLayer = GSLayer()
				# link it to the fallback layer
				newLayer.associatedMasterId = fallbackMasterId
				# assign the color index from Palette
				newLayer.attributes['colorPalette'] = colorIndex
				# add the layer
				layer.parent.layers.append(newLayer)
				# copy path
				newLayer.paths.append(path.copy())
				newLayer.syncMetrics()
			else:
				# copy to an existed Color Palette layer
				existedLayer.paths.append(path.copy())

# add a color components parts to the glyphs with a components
for glyph in font.glyphs:
	layer = glyph.layers[activeMasterId]
	if layer.components:
		for component in layer.components:
			source = component.component.layers[layer.associatedMasterId].parent
			for colorPaletteLayer in source.layers:
				if colorPaletteLayer.attributes['colorPalette'] or colorPaletteLayer.attributes['colorPalette'] == 0:
					newLayer = GSLayer()
					newLayer.associatedMasterId = activeMasterId
					newLayer.attributes['colorPalette'] = colorPaletteLayer.attributes['colorPalette']
					colorComponent = GSComponent(source)
					colorComponent.automaticAlignment = False
					colorComponent.x = component.x
					colorComponent.y = component.y
					newLayer.components.append(colorComponent)
					layer.parent.layers.append(newLayer)
					newLayer.syncMetrics()

# focus to fallback layer if set in params
if fallbackLayerName:
	Font.masterIndex = fallbackMasterIndex

font.enableUpdateInterface()