"""
synthetic_images.py — Generators for synthetic test images (clean, blur, dark, duplicate, with EXIF).
Strictly synthetic, NO real patient images!
"""
from PIL import Image, ImageDraw, ImageFilter
import io

def generate_sharp_skin_image(width: int = 800, height: int = 800) -> bytes:
    """Generate a sharp synthetic image with simulated skin tone and texture."""
    img = Image.new("RGB", (width, height), color=(225, 185, 150))
    draw = ImageDraw.Draw(img)
    # Draw some red lesion spots
    draw.ellipse([300, 300, 450, 450], fill=(200, 90, 80))
    draw.ellipse([350, 360, 410, 420], fill=(160, 50, 50))
    # Draw sharp texture lines
    for i in range(100, 700, 15):
        draw.line([i, 100, i + 10, 700], fill=(215, 175, 140), width=1)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def generate_blurry_image(width: int = 800, height: int = 800) -> bytes:
    """Generate heavily blurred image to trigger RETAKE blur gate."""
    img = Image.new("RGB", (width, height), color=(225, 185, 150))
    draw = ImageDraw.Draw(img)
    draw.ellipse([300, 300, 450, 450], fill=(200, 90, 80))
    # Apply severe Gaussian blur
    blurred = img.filter(ImageFilter.GaussianBlur(radius=25))
    buf = io.BytesIO()
    blurred.save(buf, format="JPEG", quality=80)
    return buf.getvalue()

def generate_dark_image(width: int = 800, height: int = 800) -> bytes:
    """Generate underexposed / dark image to trigger RETAKE exposure gate."""
    # Almost black / luminance < 12
    img = Image.new("RGB", (width, height), color=(5, 5, 5))
    draw = ImageDraw.Draw(img)
    draw.ellipse([350, 350, 450, 450], fill=(15, 8, 8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()

def generate_image_with_exif(width: int = 800, height: int = 800) -> bytes:
    """Generate image with dummy EXIF metadata including GPS coordinates."""
    img = Image.new("RGB", (width, height), color=(220, 180, 145))
    exif = img.getexif()
    # 0x010E is ImageDescription, 0x0131 is Software
    exif[0x010E] = "Synthetic Test with Sensitive EXIF"
    exif[0x0131] = "DermaCare Test Script 1.0"
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()
