import cv2
import numpy as np
from PIL import Image, ImageFilter

SRC_PLANE = r"C:/Users/user/Downloads/c197fc16-7ce3-4763-8fca-00ca4a1891ae.png"
OUT_PLANE = "assets/plane.png"

img = cv2.imread(SRC_PLANE)  # BGR
h, w = img.shape[:2]

# GrabCut with rectangle init: plane occupies roughly y 380..880, x 30..1210
mask = np.zeros((h, w), np.uint8)
rect = (25, 385, 1165, 500)
bgd = np.zeros((1, 65), np.float64)
fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(img, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)

fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

# clean up: close small holes, keep largest component
kernel = np.ones((5, 5), np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=2)
n, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
if n > 1:
    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    fg = np.where(labels == largest, 255, 0).astype(np.uint8)
# fill interior holes
ff = fg.copy()
ffmask = np.zeros((h + 2, w + 2), np.uint8)
cv2.floodFill(ff, ffmask, (0, 0), 128)
holes = ff == 0
fg[holes] = 255

alpha = cv2.erode(fg, np.ones((3, 3), np.uint8), iterations=1)
alpha = cv2.GaussianBlur(alpha, (3, 3), 0.8)

rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
rgba[..., 3] = alpha
plane = Image.fromarray(rgba, "RGBA")
ys, xs = np.where(alpha > 8)
bbox = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
print("bbox:", bbox)
plane = plane.crop(bbox)
plane.save(OUT_PLANE)
print("saved:", plane.size)

prev = Image.new("RGB", (800, 500), (8, 12, 40))
p2 = plane.copy()
p2.thumbnail((760, 460))
prev.paste(p2, (20, 20), p2)
prev.save("preview_plane.png")
