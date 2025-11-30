from PIL import Image

def check_transparency(path):
    img = Image.open(path).convert("RGBA")
    extrema = img.getextrema()
    # extrema[3] is alpha channel min/max
    if extrema[3][0] < 255:
        print(f"{path}: Has transparency")
    else:
        print(f"{path}: NO transparency (Opaque)")

    # Check corners for background color
    width, height = img.size
    corners = [
        (0, 0),
        (width-1, 0),
        (0, height-1),
        (width-1, height-1)
    ]
    for x, y in corners:
        pixel = img.getpixel((x, y))
        print(f"{path} corner ({x},{y}): {pixel}")

if __name__ == "__main__":
    check_transparency("filter_active.png")
    check_transparency("filter_gray.png")
