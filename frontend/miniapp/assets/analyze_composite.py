from PIL import Image, ImageOps
import os

input_path = "/Users/apple/.gemini/antigravity/brain/29f0b90c-be0a-4727-9b22-2eb4df6daa6c/uploaded_image_1764429041694.png"

def analyze_image():
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    img = Image.open(input_path)
    print(f"Image Size: {img.size}")
    print(f"Image Mode: {img.mode}")
    
    # Convert to grayscale and threshold to find content
    gray = img.convert("L")
    # Invert if the background is white (common for screenshots)
    # Assuming icons are darker or colored on white/light background
    # Let's try to find the bounding box of non-white content
    inverted = ImageOps.invert(gray)
    bbox = inverted.getbbox()
    print(f"Content Bounding Box: {bbox}")
    
    # If we can't easily detect, we might just assume 3 equal horizontal sections
    # or ask the user. But let's try to be smart.
    
    # Let's check if it's wide or tall
    w, h = img.size
    if w > h:
        print("Layout: Likely Horizontal")
        section_width = w // 3
        print(f"Estimated Section Width: {section_width}")
    else:
        print("Layout: Likely Vertical or Grid")

if __name__ == "__main__":
    analyze_image()
