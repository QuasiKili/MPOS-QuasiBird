#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Ensure output directories exist
os.makedirs('res/mipmap-mdpi', exist_ok=True)
os.makedirs('assets', exist_ok=True)

# 1. Create app icon (64x64)
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw bird body (yellow circle)
draw.ellipse([(12, 18), (48, 54)], fill='#FFD700', outline='#FFA500', width=3)

# Draw wing
draw.ellipse([(32, 28), (52, 44)], fill='#FFA500', outline='#FF8C00', width=2)

# Draw eye
draw.ellipse([(20, 24), (30, 34)], fill='#FFFFFF', outline='#000000', width=2)
draw.ellipse([(23, 27), (27, 31)], fill='#000000')

# Draw beak
beak = [(32, 36), (46, 36), (39, 42)]
draw.polygon(beak, fill='#FF6B35', outline='#D84315', width=1)

img.save('res/mipmap-mdpi/icon_64x64.png', 'PNG', optimize=True)
print("Icon saved: res/mipmap-mdpi/icon_64x64.png")

# 2. Create bird sprite (32x32)
bird = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(bird)

# Draw bird body
draw.ellipse([(4, 6), (28, 30)], fill='#FFD700', outline='#FFA500', width=2)

# Draw wing
draw.ellipse([(16, 12), (28, 22)], fill='#FFA500', outline='#FF8C00', width=1)

# Draw eye
draw.ellipse([(8, 10), (14, 16)], fill='#FFFFFF', outline='#000000', width=1)
draw.ellipse([(10, 12), (12, 14)], fill='#000000')

# Draw beak
beak = [(18, 18), (26, 18), (22, 22)]
draw.polygon(beak, fill='#FF6B35', outline='#D84315', width=1)

bird.save('assets/bird.png', 'PNG', optimize=True)
print("Bird sprite saved: assets/bird.png")

# 3. Create pipe sprite (40x200)
pipe = Image.new('RGBA', (40, 200), (0, 0, 0, 0))
draw = ImageDraw.Draw(pipe)

# Pipe body
draw.rectangle([(4, 10), (36, 200)], fill='#5CB85C', outline='#449D44', width=2)

# Pipe cap
draw.rectangle([(0, 0), (40, 12)], fill='#5CB85C', outline='#449D44', width=2)

# Add some shading/detail
draw.rectangle([(8, 12), (10, 200)], fill='#78C878')
draw.rectangle([(30, 12), (32, 200)], fill='#449D44')

pipe.save('assets/pipe.png', 'PNG', optimize=True)
print("Pipe sprite saved: assets/pipe.png")

# Create flipped pipe for top pipes
pipe_flipped = pipe.transpose(Image.FLIP_TOP_BOTTOM)
pipe_flipped.save('assets/pipe_top.png', 'PNG', optimize=True)
print("Flipped pipe sprite saved: assets/pipe_top.png")

# 4. Create ground sprite (320x40)
ground = Image.new('RGBA', (320, 40), (0, 0, 0, 0))
draw = ImageDraw.Draw(ground)

# Ground base
draw.rectangle([(0, 0), (320, 40)], fill='#D2691E', outline='#8B4513', width=2)

# Add grass on top
for i in range(0, 320, 16):
    draw.rectangle([(i, 0), (i+8, 6)], fill='#228B22')
    draw.rectangle([(i+8, 0), (i+16, 6)], fill='#32CD32')

# Add some texture
for i in range(0, 320, 20):
    draw.line([(i, 8), (i, 38)], fill='#A0522D', width=1)

ground.save('assets/ground.png', 'PNG', optimize=True)
print("Ground sprite saved: assets/ground.png")

# 5. Create background (320x240)
bg = Image.new('RGB', (320, 240), '#87CEEB')  # Sky blue
draw = ImageDraw.Draw(bg)

# Add some clouds
for x, y in [(40, 30), (120, 50), (200, 35), (280, 45)]:
    draw.ellipse([(x-20, y-10), (x+20, y+10)], fill='#FFFFFF')
    draw.ellipse([(x-15, y-5), (x+15, y+15)], fill='#FFFFFF')
    draw.ellipse([(x-10, y-8), (x+25, y+12)], fill='#FFFFFF')

bg.save('assets/background.png', 'PNG', optimize=True)
print("Background saved: assets/background.png")

print("\nAll assets generated successfully!")
