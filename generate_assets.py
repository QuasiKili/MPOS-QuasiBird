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

# 2b. Create fire bird sprite (32x32) - for beating highscore
fire_bird = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(fire_bird)

# Draw bird body
draw.ellipse([(4, 6), (28, 30)], fill="#FFD700", outline="#FFA500", width=2)

# Draw wing
draw.ellipse([(16, 12), (28, 22)], fill="#FFA500", outline="#FF8C00", width=1)

# Draw eye
draw.ellipse([(8, 10), (14, 16)], fill="#FFFFFF", outline="#000000", width=1)
draw.ellipse([(10, 12), (12, 14)], fill="#000000")

# Draw beak
beak = [(18, 18), (26, 18), (22, 22)]
draw.polygon(beak, fill="#FF6B35", outline="#D84315", width=1)


# Draw crown (3 points on top of head)
crown_color = '#FFD700'  # Gold

# Middle crown point (tallest)
crown_mid = [(15, 2), (13, 8), (17, 8)]
draw.polygon(crown_mid, fill=crown_color, outline='#FF8C00', width=1)

# Left crown point
crown_left = [(11, 4), (9, 8), (13, 8)]
draw.polygon(crown_left, fill=crown_color, outline='#FF8C00', width=1)

# Right crown point
crown_right = [(19, 4), (17, 8), (21, 8)]
draw.polygon(crown_right, fill=crown_color, outline='#FF8C00', width=1)

fire_bird.save('assets/fire_bird.png', 'PNG', optimize=True)
print("Fire bird sprite saved: assets/fire_bird.png (with crown!)")

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

# 4. Create ground sprite (tileable pattern with adjustable parameters)
def create_ground_tile(
    width=20,           # Tile width in pixels
    height=40,          # Tile height in pixels
    grass_height=6,     # Height of grass strip on top
    dirt_color='#D2691E',      # Main dirt color
    grass_color1='#228B22',    # First grass color
    grass_color2='#32CD32',    # Second grass color (for alternating pattern)
    texture_color1='#A0522D',  # Vertical texture line color
    texture_color2='#8B4513',  # Horizontal texture line color
    add_vertical_texture=True,
    add_horizontal_texture=True
):
    """
    Create a tileable ground pattern.

    Tips for tiling:
    - Keep width small (10-40px) for better memory efficiency
    - Use even numbers for width if using alternating grass colors
    - Vertical textures on edges create repeating patterns
    """
    ground = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ground)

    # Ground base (dirt color)
    draw.rectangle([(0, 0), (width, height)], fill=dirt_color)

    # Add grass on top (alternating colors for texture)
    half_width = width // 2
    draw.rectangle([(0, 0), (half_width, grass_height)], fill=grass_color1)
    draw.rectangle([(half_width, 0), (width, grass_height)], fill=grass_color2)

    # Add vertical texture line on left edge (will create pattern when tiled)
    if add_vertical_texture:
        draw.line([(0, grass_height + 2), (0, height - 2)], fill=texture_color1, width=1)

    # Add horizontal texture
    if add_horizontal_texture:
        mid_height = height // 2
        draw.line([(0, mid_height), (width, mid_height)], fill=texture_color2, width=1)

    return ground

# Generate ground with default settings (experiment by changing these!)
ground = create_ground_tile(
    width=20,           # Try: 10, 20, 40
    height=40,
    grass_height=6,
    add_vertical_texture=True,
    add_horizontal_texture=True
)

ground.save('assets/ground.png', 'PNG', optimize=True)
print(f"Ground sprite saved: assets/ground.png ({ground.width}x{ground.height} tileable)")

# 5. Create cloud sprite (for parallax scrolling)
def create_cloud(width=50, height=25):
    """Create a simple cloud shape"""
    cloud = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(cloud)

    # Draw overlapping circles to create cloud shape
    center_y = height // 2

    # Left puff
    draw.ellipse([(0, center_y - 8), (20, center_y + 12)], fill='#FFFFFF')
    # Middle puff (larger)
    draw.ellipse([(12, center_y - 12), (38, center_y + 16)], fill='#FFFFFF')
    # Right puff
    draw.ellipse([(30, center_y - 8), (width, center_y + 12)], fill='#FFFFFF')

    return cloud

cloud = create_cloud(width=50, height=25)
cloud.save('assets/cloud.png', 'PNG', optimize=True)
print(f"Cloud sprite saved: assets/cloud.png ({cloud.width}x{cloud.height})")

# # 6. Create background (320x240)
# bg = Image.new('RGB', (320, 240), '#87CEEB')  # Sky blue
# draw = ImageDraw.Draw(bg)

# # Add some clouds
# for x, y in [(40, 30), (120, 50), (200, 35), (280, 45)]:
#     draw.ellipse([(x-20, y-10), (x+20, y+10)], fill='#FFFFFF')
#     draw.ellipse([(x-15, y-5), (x+15, y+15)], fill='#FFFFFF')
#     draw.ellipse([(x-10, y-8), (x+25, y+12)], fill='#FFFFFF')

# bg.save('assets/background.png', 'PNG', optimize=True)
# print("Background saved: assets/background.png")

print("\nAll assets generated successfully!")
