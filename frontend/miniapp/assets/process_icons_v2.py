from PIL import Image, ImageOps
import os

def process_icon(input_path, output_name, output_dir):
    try:
        print(f"Processing {input_path} -> {output_name}")
        img = Image.open(input_path).convert("RGBA")
        
        # Resize to standard tab bar icon size (81x81 for @3x)
        # Use LANCZOS for best downscaling quality
        img = img.resize((81, 81), Image.Resampling.LANCZOS)
        
        # Save active version (Blue)
        active_path = os.path.join(output_dir, f"{output_name}-active.png")
        img.save(active_path)
        print(f"Saved {active_path}")
        
        # Create inactive version (Gray #999999)
        # Create a solid gray image
        gray_bg = Image.new("RGBA", img.size, (153, 153, 153, 255)) # #999999 is (153,153,153)
        
        # Create a new image for the result
        inactive = Image.new("RGBA", img.size, (0, 0, 0, 0))
        
        # Use the alpha channel of the original image as the mask
        # This ensures we keep the shape and anti-aliasing but change the color
        r, g, b, a = img.split()
        inactive.paste(gray_bg, (0, 0), mask=a)
        
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
    "ios_home_icon_retry_1763963007831.png": "home",
    "ios_search_icon_1763962931226.png": "search",
    "ios_profile_icon_1763962946946.png": "profile"
}

for filename, output_name in icons.items():
    input_path = os.path.join(generated_dir, filename)
    if os.path.exists(input_path):
        process_icon(input_path, output_name, assets_dir)
    else:
        print(f"File not found: {input_path}")
