from PIL import Image, ImageDraw
import os

def create_icon(name, color, output_path):
    # Increase size for better anti-aliasing (downscale later if needed, but 81x81 is fine for @3x)
    size = (81, 81)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Settings
    stroke_width = 7 # Slightly thicker
    
    if name == 'home':
        # Modern House
        # Body
        draw.rectangle([20, 35, 60, 65], outline=color, width=stroke_width)
        # Roof (Triangle)
        draw.polygon([(15, 35), (40, 10), (65, 35)], outline=color, width=stroke_width)
        # Door
        draw.rectangle([34, 48, 46, 65], fill=color)
        
    elif name == 'search':
        # Modern Search
        # Circle
        draw.ellipse([15, 15, 55, 55], outline=color, width=stroke_width)
        # Handle
        draw.line([48, 48, 65, 65], fill=color, width=stroke_width+2)
        
    elif name == 'profile':
        # Modern User
        # Head
        draw.ellipse([28, 15, 52, 39], outline=color, width=stroke_width)
        # Body (Curved shoulders)
        draw.arc([15, 45, 65, 95], 180, 360, fill=color, width=stroke_width)

    img.save(output_path)
    print(f"Generated {output_path}")

# Colors - Royal Blue and Gray
active_color = "#3366FF"
inactive_color = "#999999"

output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"
os.makedirs(output_dir, exist_ok=True)

icons = ['home', 'search', 'profile']

for icon in icons:
    create_icon(icon, inactive_color, os.path.join(output_dir, f"{icon}.png"))
    create_icon(icon, active_color, os.path.join(output_dir, f"{icon}-active.png"))
