from PIL import Image, ImageDraw, ImageOps
import os

# Configuration
input_dir = "/Users/apple/.gemini/antigravity/brain/29f0b90c-be0a-4727-9b22-2eb4df6daa6c"
output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"

# Mapping based on visual inspection of Step 92
# Image 2 (House) -> Home
# Image 1 (Magnifying Glass) -> Search
# Image 0 (Person) -> Profile
image_mapping = {
    "uploaded_image_2_1764437640255.png": "home",
    "uploaded_image_1_1764437640255.png": "search",
    "uploaded_image_0_1764437640255.png": "profile"
}

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    
    # Paste 4 corners
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    
    # Paste rectangles to fill the rest
    # (Actually, the standard way is to start with black and draw white rounded rect)
    
    mask = Image.new('L', im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w, h), radius=rad, fill=255)
    
    im.putalpha(mask)
    return im

def process_icons():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for filename, icon_name in image_mapping.items():
        input_path = os.path.join(input_dir, filename)
        
        if not os.path.exists(input_path):
            print(f"Error: Input file not found: {input_path}")
            continue
            
        try:
            print(f"Processing {filename} -> {icon_name}...")
            
            img = Image.open(input_path).convert("RGBA")
            
            # Resize to 81x81
            img = img.resize((81, 81), Image.Resampling.LANCZOS)
            
            # Apply rounded corners
            # Radius: 20% of 81 is ~16. Let's use 16.
            img = add_corners(img, 16)
            
            # Save Active
            active_name = f"{icon_name}-active.png"
            active_path = os.path.join(output_dir, active_name)
            img.save(active_path)
            print(f"  Saved Active: {active_path}")
            
            # Save Inactive (Grayscale)
            # Convert to grayscale but keep alpha channel (rounded corners)
            # Split alpha
            r, g, b, a = img.split()
            gray = ImageOps.grayscale(img)
            # Merge back
            gray_icon = Image.merge("LA", (gray, a))
            # Or convert to RGBA
            gray_icon = gray_icon.convert("RGBA")
            
            inactive_name = f"{icon_name}.png"
            inactive_path = os.path.join(output_dir, inactive_name)
            gray_icon.save(inactive_path)
            print(f"  Saved Inactive: {inactive_path}")
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    process_icons()
