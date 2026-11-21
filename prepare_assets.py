import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC_PLANE = r"C:/Users/user/Downloads/c197fc16-7ce3-4763-8fca-00ca4a1891ae.png"
SRC_EARTH = r"C:/Users/user/Downloads/Без названия.jpg"
OUT_PLANE = "assets/plane.png"
OUT_EARTH = "assets/earth.png"

# ---------- plane: flood-fill white background from the borders ----------
img = Image.open(SRC_PLANE).convert("RGB")
w, h = img.size
marker = (255, 0, 255)
# seed from many border points (plane does not touch borders)
seeds = [(x, 0) for x in range(0, w, 50)] + [(x, h - 1) for x in range(0, w, 50)] + \
        [(0, y) for y in range(0, h, 50)] + [(w - 1, y) for y in range(0, h, 50)]
for s in seeds:
    px = img.getpixel(s)
    if px != marker and min(px) > 235:  # only start on near-white
        ImageDraw.floodfill(img, s, marker, thresh=28)

arr = np.array(img)
mask = np.all(arr == marker, axis=-1)  # background
alpha = np.where(mask, 0, 255).astype(np.uint8)

# feather: pixels adjacent to background that are near-white get partial alpha
a = Image.fromarray(alpha)
a_soft = a.filter(ImageFilter.GaussianBlur(1.2))
alpha = np.minimum(np.array(a), np.array(a_soft) + 60).astype(np.uint8)

rgba = np.dstack([np.array(Image.open(SRC_PLANE).convert("RGB")), alpha])
plane = Image.fromarray(rgba, "RGBA")

# crop to content bounding box
bbox = plane.getchannel("A").getbbox()
plane = plane.crop(bbox)
plane.save(OUT_PLANE)
print("plane saved:", plane.size)

# ---------- earth: chroma-key green ----------
e = Image.open(SRC_EARTH).convert("RGB")
a = np.array(e).astype(np.float32)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
# greenness: how much g dominates
green_score = g - np.maximum(r, b)
# alpha: 0 for strong green, 1 otherwise, soft transition
alpha = np.clip((60 - green_score) / 70.0, 0, 1)
alpha = (alpha * 255).astype(np.uint8)
alpha_img = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1.0))
alpha = np.array(alpha_img)

# despill: reduce green where it dominates
g_new = np.minimum(g, (r + b) / 2 + 18)
rgb = np.dstack([r, g_new, b]).astype(np.uint8)
earth = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")

bbox = earth.getchannel("A").getbbox()
earth = earth.crop(bbox)
earth.save(OUT_EARTH)
print("earth saved:", earth.size)
