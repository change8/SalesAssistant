from PIL import Image, ImageFilter, ImageOps
import os

input_path = "/Users/apple/.gemini/antigravity/brain/29f0b90c-be0a-4727-9b22-2eb4df6daa6c/uploaded_image_1764429041694.png"
output_dir = "/Users/apple/WorkSpace/Codex/SalesAssistant/frontend/miniapp/assets"

def find_and_extract_cards():
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        return

    print(f"Processing {input_path}...")
    img = Image.open(input_path).convert("RGBA")
    
    # 1. Analyze brightness profile
    gray = img.convert("L")
    
    # Let's try to be smarter. The cards are likely the brightest things.
    # But the background might be light too.
    # Let's look at the center horizontal line to see the profile.
    width, height = gray.size
    mid_y = height // 2
    
    # If we can't separate by threshold, we can fallback to geometry.
    # The image is 1024 wide. 3 cards.
    # They are likely centered.
    # Let's try a very high threshold first.
    threshold = 250
    mask = gray.point(lambda p: 255 if p > threshold else 0)
    
    # Project to X
    col_counts = []
    for x in range(width):
        col_slice = mask.crop((x, 0, x+1, height))
        if col_slice.getbbox():
            col_counts.append(1)
        else:
            col_counts.append(0)
            
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
        
    segments = [s for s in segments if (s[1] - s[0]) > 50]
    print(f"Segments with threshold {threshold}: {segments}")
    
    # If still 1 segment, fallback to fixed geometry
    if len(segments) != 3:
        print("Fallback: Using fixed geometry (splitting into 3 equal parts)")
        # Assuming equal spacing
        section_width = width // 3
        segments = [
            (0, section_width),
            (section_width, 2*section_width),
            (2*section_width, width)
        ]
        
    icons = ["home", "search", "profile"]
    
    for i, (start_x, end_x) in enumerate(segments):
        if i >= 3: break
        
        # Crop the vertical strip
        strip = img.crop((start_x, 0, end_x, height))
        
        # Now we need to find the card inside this strip.
        # It's a white rounded rect.
        # Let's use the same threshold trick on the strip to find vertical bounds.
        strip_gray = strip.convert("L")
        strip_mask = strip_gray.point(lambda p: 255 if p > 250 else 0)
        bbox = strip_mask.getbbox()
        
        if bbox:
            # Expand bbox slightly to include anti-aliased edges/shadow if desired?
            # Or just take the white box. User said "according to white rounded frames".
            # The bbox of >250 brightness should be the white box.
            final_crop = strip.crop(bbox)
        else:
            # Fallback if mask is empty (maybe card is not pure white?)
            # Just take the center square?
            w, h = strip.size
            size = min(w, h)
            # Center crop
            left = (w - size) // 2
            top = (h - size) // 2
            final_crop = strip.crop((left, top, left+size, top+size))
            
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
