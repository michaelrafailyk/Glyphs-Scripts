#MenuTitle: Random Color Paths
from GlyphsApp.plugins import NSColor
import random
__doc__="""
Toggles a selected glyphs layer to color layer and paint each path in random color from predefined palette.
"""

colors = ['fabd67', '96cc72', 'f39377', 'f7d574', 'f0ab9e', 'f2b985', 'f27e74', 'a9c2bb', '81b6db', 'd5d67c', '84ccb2', 'b8ab9e', 'bf987c', 'd1806d', '3f95d1', '869df0', '55c0e0']

for layer in Glyphs.font.selectedLayers:
	layer.attributes['color'] = True
	usedColors = []
	for path in layer.paths:
		pathColor = random.choice(colors)
		if pathColor in usedColors:
			usedColorsCounter = 0
			while pathColor in usedColors and usedColorsCounter < len(colors):
				pathColor = random.choice(colors)
				usedColorsCounter += 1
		usedColors.append(pathColor)
		path.attributes['fillColor'] = NSColor.colorWithString_('#' + pathColor)

		# or for yellow-black emoticons
# 		if layer.indexOfPath_(path) == 0:
# 			path.attributes['fillColor'] = NSColor.colorWithString_('#f7d574')
# 		else:
# 			path.attributes['fillColor'] = NSColor.colorWithString_('#000000')

		# or recolor all black to dark gray
# 		if str(path.attributes['fillColor']) == 'NSCalibratedRGBColorSpace 0 0 0 1':
# 			path.attributes['fillColor'] = NSColor.colorWithString_('#111111')