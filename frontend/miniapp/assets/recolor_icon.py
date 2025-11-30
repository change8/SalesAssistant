from PIL import Image

def recolor_icon(input_path, output_path, color):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()

    new_data = []
    for item in data:
        # item is (r, g, b, a)
        if item[3] > 0:  # If not transparent
            # Apply new color, keep alpha
            new_data.append((color[0], color[1], color[2], item[3]))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved recolored icon to {output_path}")

if __name__ == "__main__":
    # Color #9ca3af is (156, 163, 175)
    recolor_icon("filter_active.png", "filter_gray.png", (156, 163, 175))
