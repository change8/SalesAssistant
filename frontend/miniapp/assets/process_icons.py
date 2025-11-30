from PIL import Image, ImageOps
import os

def process_icon(input_path, output_name, output_dir):
    try:
        img = Image.open(input_path).convert("RGBA")
        
        # Resize to standard tab bar icon size (81x81 for @3x)
        img = img.resize((81, 81), Image.Resampling.LANCZOS)
        
        # Save active version
        active_path = os.path.join(output_dir, f"{output_name}-active.png")
        img.save(active_path)
        print(f"Saved {active_path}")
        
        # Create inactive version (Grayscale + Opacity)
        # Convert to grayscale
        gray = ImageOps.grayscale(img)
        # Create a new RGBA image with gray color #999999
        inactive = Image.new("RGBA", img.size, (153, 153, 153, 0))
        
        # Use the alpha channel from the original image
        r, g, b, a = img.split()
        inactive.putalpha(a)
        
        # Save inactive version
        inactive_path = os.path.join(output_dir, f"{output_name}.png")
        inactive.save(inactive_path)
        print(f"Saved {inactive_path}")
        
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

# Paths
assets_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"
generated_dir = "/Users/apple/.gemini/antigravity/brain/dad15cff-6a23-4f63-9bcc-d21b4cf99ed0"

# Icon mapping
icons = {
    "icon_home_active_1763914270824.png": "home",
    "icon_search_active_1763914312419.png": "search",
    "icon_profile_active_1763914352995.png": "profile"
}

for filename, output_name in icons.items():
    input_path = os.path.join(generated_dir, filename)
    process_icon(input_path, output_name, assets_dir)
