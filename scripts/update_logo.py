# scripts/update_logo.py
import os
from PIL import Image, ImageDraw

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_MARK_PATH = r"C:\Users\kiran\.gemini\antigravity-ide\brain\0f3c18f0-56d5-436d-916b-67b90c26697e\.user_uploaded\media_1790007494940.png"

CLIENT_PUBLIC = os.path.join(BASE_DIR, "client", "public")
CLIENT_APP = os.path.join(BASE_DIR, "client", "src", "app")
ROOT_PUBLIC = os.path.join(BASE_DIR, "public")

def create_rounded_rect_favicon(mark, size=256, radius=40):
    """
    Creates the exact browser tab favicon shown in user's screenshot:
    Crisp white rounded-square background badge with the vibrant logo centered.
    """
    # Create white canvas
    bg = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    
    # Scale mark to fit nicely inside
    mark_copy = mark.copy()
    inner_size = int(size * 0.82)
    mark_copy.thumbnail((inner_size, inner_size), Image.Resampling.LANCZOS)
    
    # Center mark
    x = (size - mark_copy.width) // 2
    y = (size - mark_copy.height) // 2
    bg.paste(mark_copy, (x, y), mark_copy)
    
    # Optional rounded corners mask for clean aesthetic
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(bg, (0, 0), mask=mask)
    return result

def process_assets():
    # 1. Load source new mark
    new_mark = Image.open(NEW_MARK_PATH).convert("RGBA")
    bbox = new_mark.getbbox()
    new_mark_cropped = new_mark.crop(bbox) if bbox else new_mark

    # 2. Square transparent mark (high-res)
    max_dim = max(new_mark_cropped.size)
    pad = int(max_dim * 0.04)
    square_size = max_dim + (pad * 2)
    mark_square = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
    offset_x = (square_size - new_mark_cropped.width) // 2
    offset_y = (square_size - new_mark_cropped.height) // 2
    mark_square.paste(new_mark_cropped, (offset_x, offset_y), new_mark_cropped)

    # 3. Dark mode mark (on black background)
    mark_dark = Image.new("RGB", (square_size, square_size), (0, 0, 0))
    mark_dark.paste(new_mark_cropped, (offset_x, offset_y), new_mark_cropped)

    # 4. Favicon Badge (exact match to user's browser tab screenshot)
    fav_badge = create_rounded_rect_favicon(new_mark_cropped, size=256, radius=48)
    fav_square_white = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
    fav_inner = new_mark_cropped.copy()
    fav_inner.thumbnail((210, 210), Image.Resampling.LANCZOS)
    fav_square_white.paste(fav_inner, ((256 - fav_inner.width) // 2, (256 - fav_inner.height) // 2), fav_inner)

    # Save to client/public, root/public, and client/src/app
    all_dest_dirs = [CLIENT_PUBLIC, ROOT_PUBLIC, CLIENT_APP]
    for dest_dir in all_dest_dirs:
        os.makedirs(dest_dir, exist_ok=True)
        # Favicon ICO
        fav_square_white.save(
            os.path.join(dest_dir, "favicon.ico"),
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )
        # Favicon PNG
        fav_square_white.save(os.path.join(dest_dir, "favicon.png"), "PNG")
        # Next.js App Router metadata icon
        fav_square_white.save(os.path.join(dest_dir, "icon.png"), "PNG")
        fav_badge.save(os.path.join(dest_dir, "apple-icon.png"), "PNG")
        # Mark assets
        mark_square.save(os.path.join(dest_dir, "comlina-mark.png"), "PNG")
        mark_dark.save(os.path.join(dest_dir, "comlina-mark-dark.png"), "PNG")
        print(f"Generated core icons in {dest_dir}")

    # 5. Horizontal Logo (Mark + Wordmark)
    wordmark_path = os.path.join(CLIENT_PUBLIC, "comlina-wordmark.png")
    wordmark = Image.open(wordmark_path).convert("RGBA")

    target_height = 355
    mark_ratio = new_mark_cropped.width / new_mark_cropped.height
    scaled_mark_w = int(target_height * mark_ratio)
    scaled_mark = new_mark_cropped.resize((scaled_mark_w, target_height), Image.Resampling.LANCZOS)

    # Wordmark scaled proportionally
    wm_target_h = int(target_height * 0.48)
    wm_ratio = wordmark.width / wordmark.height
    scaled_wm_w = int(wm_target_h * wm_ratio)
    scaled_wm = wordmark.resize((scaled_wm_w, wm_target_h), Image.Resampling.LANCZOS)

    gap = 40
    horiz_w = scaled_mark_w + gap + scaled_wm_w
    horiz_h = target_height

    horiz_img = Image.new("RGBA", (horiz_w, horiz_h), (0, 0, 0, 0))
    horiz_img.paste(scaled_mark, (0, 0), scaled_mark)
    wm_y = (horiz_h - wm_target_h) // 2 + 10
    horiz_img.paste(scaled_wm, (scaled_mark_w + gap, wm_y), scaled_wm)

    # 6. Full Logo (Vertical: Mark + Wordmark + Tagline)
    tagline_path = os.path.join(CLIENT_PUBLIC, "comlina-tagline.png")
    tagline = Image.open(tagline_path).convert("RGBA") if os.path.exists(tagline_path) else None

    vert_mark_h = 500
    vert_mark_w = int(vert_mark_h * mark_ratio)
    scaled_vert_mark = new_mark_cropped.resize((vert_mark_w, vert_mark_h), Image.Resampling.LANCZOS)

    vert_wm_h = int(vert_mark_h * 0.28)
    vert_wm_w = int(vert_wm_h * wm_ratio)
    scaled_vert_wm = wordmark.resize((vert_wm_w, vert_wm_h), Image.Resampling.LANCZOS)

    vert_gap1 = 40
    vert_gap2 = 25

    scaled_tagline = None
    tag_h = 0
    if tagline:
        tag_h = int(vert_mark_h * 0.07)
        tag_ratio = tagline.width / tagline.height
        tag_w = int(tag_h * tag_ratio)
        scaled_tagline = tagline.resize((tag_w, tag_h), Image.Resampling.LANCZOS)

    total_h = vert_mark_h + vert_gap1 + vert_wm_h + (vert_gap2 + tag_h if scaled_tagline else 0)
    total_w = max(vert_mark_w, vert_wm_w, scaled_tagline.width if scaled_tagline else 0) + 80

    full_img = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    mx = (total_w - vert_mark_w) // 2
    full_img.paste(scaled_vert_mark, (mx, 0), scaled_vert_mark)

    wm_x = (total_w - vert_wm_w) // 2
    wm_y = vert_mark_h + vert_gap1
    full_img.paste(scaled_vert_wm, (wm_x, wm_y), scaled_vert_wm)

    if scaled_tagline:
        tx = (total_w - scaled_tagline.width) // 2
        ty = wm_y + vert_wm_h + vert_gap2
        full_img.paste(scaled_tagline, (tx, ty), scaled_tagline)

    for dest_dir in [CLIENT_PUBLIC, ROOT_PUBLIC]:
        horiz_img.save(os.path.join(dest_dir, "comlina-horizontal.png"), "PNG")
        full_img.save(os.path.join(dest_dir, "comlina-full.png"), "PNG")
        full_img.save(os.path.join(dest_dir, "comlina-logo.png"), "PNG")

    # 7. Horizontal Tagline Logo
    if scaled_tagline:
        horiz_tag_h = horiz_h + 50
        horiz_tag_w = max(horiz_w, scaled_mark_w + gap + scaled_tagline.width)
        horiz_tag_img = Image.new("RGBA", (horiz_tag_w, horiz_tag_h), (0, 0, 0, 0))
        horiz_tag_img.paste(scaled_mark, (0, 0), scaled_mark)
        horiz_tag_img.paste(scaled_wm, (scaled_mark_w + gap, wm_y - 15), scaled_wm)
        horiz_tag_img.paste(scaled_tagline, (scaled_mark_w + gap, wm_y + wm_target_h), scaled_tagline)
        for dest_dir in [CLIENT_PUBLIC, ROOT_PUBLIC]:
            horiz_tag_img.save(os.path.join(dest_dir, "comlina-horizontal-tagline.png"), "PNG")

if __name__ == "__main__":
    process_assets()
    print("All logo and favicon assets successfully generated and synced!")
