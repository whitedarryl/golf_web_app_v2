from fontTools.ttLib import TTFont
import brotli

# Load TTF
font = TTFont("PatrickHandSC-Regular.ttf")

# Export to WOFF2
font.flavor = 'woff2'
font.save("PatrickHandSC-Regular.woff2")

print("✅ Satisfy font converted to .woff2")
