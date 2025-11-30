from PIL import Image, ImageOps
import os

# Configuration
input_dir = "/Users/apple/.gemini/antigravity/brain/29f0b90c-be0a-4727-9b22-2eb4df6daa6c"
output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"

# Mapping: Uploaded Filename -> Target Icon Name
# Based on Implementation Plan:
# uploaded_image_1... -> Home
# uploaded_image_2... -> Search
# uploaded_image_0... -> Profile
image_mapping = {
    "uploaded_image_1_1764416602859.jpg": "home",
    "uploaded_image_2_1764416602859.jpg": "search",
    "uploaded_image_0_1764416602859.jpg": "profile"
}

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
            
            # Open image
            img = Image.open(input_path).convert("RGBA")
            
            # Resize to 81x81 (Standard TabBar icon size for @3x)
            img = img.resize((81, 81), Image.Resampling.LANCZOS)
            
            # 1. Save Active State (Original Color)
            active_name = f"{icon_name}-active.png"
            active_path = os.path.join(output_dir, active_name)
            img.save(active_path)
            print(f"  Saved Active: {active_path}")
            
            # 2. Save Inactive State (Grayscale)
            # Since input is JPG (no transparency), we convert to grayscale.
            # If we used a solid color mask on a square JPG, we'd get a solid square.
            # Grayscale preserves the icon details but removes color.
            inactive_name = f"{icon_name}.png"
            inactive_path = os.path.join(output_dir, inactive_name)
            
            # Convert to grayscale
            gray_img = ImageOps.grayscale(img)
            # Convert back to RGBA to save as PNG (though L mode works too, RGBA is safer for consistency)
            gray_img = gray_img.convert("RGBA")
            
            gray_img.save(inactive_path)
            print(f"  Saved Inactive: {inactive_path}")
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    process_icons()
