from PIL import Image, ImageOps, ImageChops
import os

# Configuration
input_path = "/Users/apple/.gemini/antigravity/brain/29f0b90c-be0a-4727-9b22-2eb4df6daa6c/uploaded_image_1764429041694.png"
output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"

def trim(im):
    # Trim whitespace (based on top-left pixel color)
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    return im

def process_composite():
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Processing {input_path}...")
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    
    # Split into 3 sections
    section_width = width // 3
    
    icons = [
        ("home", 0),
        ("search", 1),
        ("profile", 2)
    ]
    
    for name, index in icons:
        # Crop section
        left = index * section_width
        right = (index + 1) * section_width
        # Ensure we don't go out of bounds on the last one
        if index == 2:
            right = width
            
        section = img.crop((left, 0, right, height))
        
        # Auto-crop (Trim) content from background
        # We assume the background is uniform-ish. 
        # Since it's a screenshot/composite, let's try to trim based on the corner color.
        cropped = trim(section)
        
        # Resize to 81x81 (LANCZOS for quality)
        resized = cropped.resize((81, 81), Image.Resampling.LANCZOS)
        
        # Save Active (Original Color)
        active_path = os.path.join(output_dir, f"{name}-active.png")
        resized.save(active_path)
        print(f"Saved {active_path}")
        
        # Save Inactive (Grayscale)
        # Convert to grayscale then back to RGBA to keep transparency if any (though trim might have kept bg)
        # If the original image had a white background, trim might have removed it if it was exact match.
        # If it's a screenshot, it likely has a background.
        # Let's assume we want to keep the shape but make it gray.
        
        gray = ImageOps.grayscale(resized).convert("RGBA")
        inactive_path = os.path.join(output_dir, f"{name}.png")
        gray.save(inactive_path)
        print(f"Saved {inactive_path}")

if __name__ == "__main__":
    process_composite()
