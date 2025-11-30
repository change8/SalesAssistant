from PIL import Image, ImageFilter
import os

input_path = "/Users/apple/.gemini/antigravity/brain/29f0b90c-be0a-4727-9b22-2eb4df6daa6c/uploaded_image_1764429041694.png"
output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"

def find_and_extract_cards():
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Processing {input_path}...")
    img = Image.open(input_path).convert("RGBA")
    
    # 1. Create a mask for the white cards
    # The cards are likely very bright/white. The background is likely slightly darker.
    # Convert to grayscale
    gray = img.convert("L")
    
    # Threshold. Assuming cards are near pure white (255).
    # Let's try a high threshold.
    threshold = 240
    mask = gray.point(lambda p: 255 if p > threshold else 0)
    
    # 2. Find bounding boxes of white regions
    # Since we don't have cv2, we can project to x and y axes or use a simple blob search.
    # Given the layout is horizontal, we can scan horizontally.
    
    # Get the bounding box of the non-black regions in the mask
    # This might give us one big box if they are connected or close, but they look separated.
    # Let's try to find separate components.
    
    # A simple way without cv2:
    # 1. Project to X axis (sum of white pixels per column)
    # 2. Find gaps in the projection to separate the 3 cards.
    
    width, height = mask.size
    col_counts = []
    for x in range(width):
        col_slice = mask.crop((x, 0, x+1, height))
        # Count non-zero pixels
        # getbbox returns None if all black
        if col_slice.getbbox():
            col_counts.append(1)
        else:
            col_counts.append(0)
            
    # Find segments of 1s
    segments = []
    in_segment = False
    start = 0
    for x, val in enumerate(col_counts):
        if val == 1 and not in_segment:
            in_segment = True
            start = x
        elif val == 0 and in_segment:
            in_segment = False
            segments.append((start, x))
            
    if in_segment:
        segments.append((start, width))
        
    print(f"Found {len(segments)} horizontal segments: {segments}")
    
    # Filter small segments (noise)
    segments = [s for s in segments if (s[1] - s[0]) > 50]
    print(f"Filtered segments: {segments}")
    
    if len(segments) != 3:
        print("Warning: Did not find exactly 3 segments. Adjusting threshold or logic might be needed.")
        # If we found 1 big segment, maybe they are too close?
        # If we found > 3, maybe noise?
    
    # Process each segment
    icons = ["home", "search", "profile"]
    
    for i, (start_x, end_x) in enumerate(segments):
        if i >= 3: break
        
        # Crop the vertical strip
        strip = img.crop((start_x, 0, end_x, height))
        strip_mask = mask.crop((start_x, 0, end_x, height))
        
        # Now find the vertical bounds (Y axis)
        bbox = strip_mask.getbbox()
        if bbox:
            # bbox is relative to strip
            final_crop = strip.crop(bbox)
            
            # Resize
            resized = final_crop.resize((81, 81), Image.Resampling.LANCZOS)
            
            name = icons[i]
            
            # Save Active
            active_path = os.path.join(output_dir, f"{name}-active.png")
            resized.save(active_path)
            print(f"Saved {active_path}")
            
            # Save Inactive (Grayscale)
            gray_icon = resized.convert("L").convert("RGBA")
            inactive_path = os.path.join(output_dir, f"{name}.png")
            gray_icon.save(inactive_path)
            print(f"Saved {inactive_path}")

if __name__ == "__main__":
    find_and_extract_cards()
