from PIL import Image

def remove_background(input_path, output_path, threshold=240):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()

    new_data = []
    for item in data:
        # item is (r, g, b, a)
        # If pixel is light (near white), make it transparent
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved transparent icon to {output_path}")

if __name__ == "__main__":
    remove_background("filter_active.png", "filter_active.png")
    remove_background("filter_gray.png", "filter_gray.png")
