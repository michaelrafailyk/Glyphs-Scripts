#MenuTitle: SVG to COLR
__doc__="""
Convert Color layer to Color Palette layer
"""

# params
# group the same colors on one layer
groupSameColors = True

font = Glyphs.font
# disable interface update
font.disableUpdateInterface()

# add an empty Color Palette to the Font Info
if not Glyphs.font.customParameters["Color Palettes"]:
	Glyphs.font.customParameters["Color Palettes"] = NSMutableArray.arrayWithObjects_([])

# if the font contains more than one master, please make the Color layer master active
activeMasterId = Glyphs.font.selectedFontMaster.id

# process all the glyphs at once
for glyph in Glyphs.font.glyphs:
	layer = glyph.layers[activeMasterId]
	if layer.attributes['color']:
		# remove Color layer attribute and made it the fallback layer
		layer.attributes['color'] = None
		# get the fallback layer id for linking a Color palette layers to him
		masterId = font.fontMasterAtIndex_(font.masterIndex).id
		for path in layer.paths:
			# get the path color
			color = path.attributes['fillColor']
			# clear the color info on the fallback layer
			path.attributes['fillColor'] = None
			# add the color to the Palette if it is not there yet
			if color not in Glyphs.font.customParameters["Color Palettes"][0]:
				Glyphs.font.customParameters["Color Palettes"][0].append(color)
			# get the color index in the Palette
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
				newLayer.associatedMasterId = masterId
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

# enable interface update back
font.enableUpdateInterface()