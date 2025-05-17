from PIL import Image, ImageDraw
import os

# Create a new transparent image
width, height = 512, 512
img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# Define colors
highlighter_color = (255, 220, 0, 255)  # Yellow highlighter
highlighter_tip_color = (255, 190, 0, 255)  # Darker tip

# Draw the highlighter body
points = [
    (120, 100),    # Top left
    (350, 100),    # Top right
    (390, 140),    # Upper right corner
    (250, 380),    # Bottom right
    (170, 380),    # Bottom left
    (80, 140),     # Lower left corner
]
draw.polygon(points, fill=highlighter_color)

# Draw the highlighter tip
tip_points = [
    (170, 380),    # Top left
    (250, 380),    # Top right
    (220, 430),    # Bottom right
    (200, 430),    # Bottom left
]
draw.polygon(tip_points, fill=highlighter_tip_color)

# Draw a highlight stroke under the highlighter
highlight_points = [
    (90, 200),
    (420, 200),
    (420, 260),
    (90, 260),
]
draw.polygon(highlight_points, fill=(255, 255, 0, 128))  # Semi-transparent yellow

# Save the image
output_path = os.path.join(os.path.dirname(__file__), 'highlight.png')
img.save(output_path)

print(f"Highlight icon saved to {output_path}") 