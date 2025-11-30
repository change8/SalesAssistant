from PIL import Image, ImageDraw
import os

def create_icon(name, color, output_path):
    size = (81, 81)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Common settings
    stroke_width = 6
    padding = 15
    
    if name == 'home':
        # House icon
        # Roof
        draw.polygon([
            (40, padding), 
            (padding, 40), 
            (size[0]-padding, 40)
        ], fill=None, outline=color, width=stroke_width)
        # Body
        draw.rectangle([
            (20, 40), 
            (60, size[1]-padding)
        ], fill=None, outline=color, width=stroke_width)
        # Door
        draw.rectangle([
            (32, 55), 
            (48, size[1]-padding)
        ], fill=color, outline=None)
        
    elif name == 'search':
        # Magnifying glass
        # Circle
        circle_bbox = [padding, padding, 55, 55]
        draw.ellipse(circle_bbox, outline=color, width=stroke_width)
        # Handle
        draw.line([
            (52, 52), 
            (size[0]-padding, size[1]-padding)
        ], fill=color, width=stroke_width+2)
        
    elif name == 'profile':
        # User icon
        # Head
        head_radius = 14
        draw.ellipse([
            (40-head_radius, 20-head_radius), 
            (40+head_radius, 20+head_radius)
        ], outline=color, width=stroke_width)
        # Body (curved)
        draw.arc([
            (padding, 40), 
            (size[0]-padding, size[1]+20)
        ], 180, 360, fill=color, width=stroke_width)

    img.save(output_path)
    print(f"Generated {output_path}")

# Colors
active_color = "#3366FF"
inactive_color = "#999999"

# Output directory
output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"
os.makedirs(output_dir, exist_ok=True)

# Generate icons
icons = ['home', 'search', 'profile']

for icon in icons:
    create_icon(icon, inactive_color, os.path.join(output_dir, f"{icon}.png"))
    create_icon(icon, active_color, os.path.join(output_dir, f"{icon}-active.png"))
