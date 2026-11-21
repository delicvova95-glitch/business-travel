import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

W, H = 1920, 1080
FPS = 30
DURATION = 12.0
N_FRAMES = int(FPS * DURATION)

EARTH_D = 640
ECX, ECY = 960, 545
ORBIT_RX = 620
ORBIT_TILT = 0.14          # vertical amplitude fraction of ORBIT_RX
PLANE_W = 460
DEPTH_SCALE = 0.30
THETA0 = 264.0             # start angle: just past the left limb, behind the planet

# ---------------- background: navy space + stars ----------------
rng = np.random.default_rng(7)

def make_background():
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    d = np.sqrt((x - 0.35) ** 2 + (y - 0.3) ** 2)
    base = 10 + 22 * (1 - np.clip(d, 0, 1))
    bg = np.dstack([base * 0.45, base * 0.62, base * 1.35 + 6]).astype(np.uint8)
    return Image.fromarray(bg, "RGB")

N_STARS = 280
stars = []
for _ in range(N_STARS):
    sx = rng.uniform(0, W)
    sy = rng.uniform(0, H)
    br = rng.uniform(60, 220)
    size = int(rng.choice([1, 1, 1, 2, 2, 3]))
    k = int(rng.integers(1, 3))          # integer twinkle freq -> seamless loop
    ph = rng.uniform(0, 2 * math.pi)
    stars.append((sx, sy, br, size, k, ph))

BG = make_background()

# ---------------- earth assets ----------------
earth_src = Image.open("assets/earth.png").convert("RGBA")
side = max(earth_src.size)
sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
sq.paste(earth_src, ((side - earth_src.width) // 2, (side - earth_src.height) // 2), earth_src)
earth_src = sq.resize((EARTH_D, EARTH_D), Image.LANCZOS)

# atmosphere: soft outer halo + sharper rim
c = EARTH_D
glow = Image.new("RGBA", (EARTH_D * 2, EARTH_D * 2), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([c - EARTH_D // 2, c - EARTH_D // 2, c + EARTH_D // 2, c + EARTH_D // 2],
           fill=(70, 140, 255, 90))
glow = glow.filter(ImageFilter.GaussianBlur(26))
rim = Image.new("RGBA", (EARTH_D * 2, EARTH_D * 2), (0, 0, 0, 0))
rd = ImageDraw.Draw(rim)
rd.ellipse([c - EARTH_D // 2, c - EARTH_D // 2, c + EARTH_D // 2, c + EARTH_D // 2],
           outline=(120, 180, 255, 110), width=3)
rim = rim.filter(ImageFilter.GaussianBlur(4))
glow = Image.alpha_composite(glow, rim)

# ---------------- clouds: isotropic noise, tileable horizontally ----------------
CW = EARTH_D * 2
noise = rng.uniform(0, 1, (48, 96)).astype(np.float32)
cn_img = Image.fromarray((noise * 255).astype(np.uint8)).resize((CW, EARTH_D), Image.BICUBIC)
cn = np.array(cn_img).astype(np.float32) / 255.0
cn = np.clip((cn - 0.55) * 2.6, 0, 1) ** 1.8
cloud_strip = np.tile(cn, (1, 2))                       # width 2*CW -> wraps seamlessly
cloud_alpha = (cloud_strip * 55).astype(np.uint8)
cloud_img = Image.fromarray(
    np.dstack([np.full_like(cloud_alpha, 255), np.full_like(cloud_alpha, 255),
               np.full_like(cloud_alpha, 255), cloud_alpha]), "RGBA")
disk_mask = earth_src.getchannel("A")

# ---------------- plane sprites ----------------
plane_src = Image.open("assets/plane.png").convert("RGBA")
plane_mirror = plane_src.transpose(Image.FLIP_LEFT_RIGHT)
P_AR = plane_src.height / plane_src.width


def plane_sprite(width, mirrored, brightness, tint_blue):
    h = max(2, int(width * P_AR))
    sp = (plane_mirror if mirrored else plane_src).resize((width, h), Image.LANCZOS)
    if brightness < 0.999:
        rgb = sp.convert("RGB")
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
        if tint_blue > 0:
            overlay = Image.new("RGB", rgb.size, (30, 60, 140))
            rgb = Image.blend(rgb, overlay, tint_blue)
        sp = Image.merge("RGBA", (*rgb.split(), sp.getchannel("A")))
    return sp


def orbit(t):
    """theta decreases 30 deg/s. Front pass = second half, R->L, original sprite."""
    theta = math.radians(THETA0 - 360.0 * t / DURATION)
    z = math.cos(theta)                                   # >0 in front of the planet
    x = ECX + ORBIT_RX * math.sin(theta)
    y = ECY - ORBIT_TILT * ORBIT_RX * math.cos(theta)
    vx = -math.cos(theta)         # d(x)/dtheta with theta_dot < 0
    vy = -ORBIT_TILT * math.sin(theta)
    gamma = math.degrees(math.atan2(-vy, vx))             # screen-CCW heading (y-up conv.)
    return theta, x, y, z, gamma


def render_frame(t):
    phi = 2 * math.pi * t / DURATION
    frame = BG.copy()

    d = ImageDraw.Draw(frame)
    for sx, sy, br, size, k, ph in stars:
        b = br * (0.78 + 0.22 * math.sin(phi * k + ph))
        d.ellipse([sx - size / 2, sy - size / 2, sx + size / 2, sy + size / 2],
                  fill=(int(b * 0.9), int(b * 0.95), int(b)))

    # camera breathing (integer sine periods -> seamless)
    zoom = 1.0 + 0.018 * math.sin(phi)
    cam_dx = 10 * math.sin(2 * phi)
    cam_dy = 6 * math.cos(2 * phi)

    ed = int(EARTH_D * zoom)
    ecx = ECX + cam_dx
    ecy = ECY + cam_dy

    rock = 3.0 * math.sin(phi)                            # gentle libration, seamless
    earth = earth_src.resize((ed, ed), Image.LANCZOS).rotate(rock, resample=Image.BICUBIC)
    gl = glow.resize((ed * 2, ed * 2), Image.BILINEAR)

    shift = int((t / DURATION) * CW)                      # cloud drift, wraps -> seamless
    strip = cloud_img.crop((shift, 0, shift + CW, EARTH_D)).resize((ed, ed), Image.BILINEAR)
    strip.putalpha(Image.composite(strip.getchannel("A"),
                                   Image.new("L", strip.size, 0), disk_mask.resize((ed, ed))))
    strip = strip.rotate(rock, resample=Image.BICUBIC)

    theta, px, py, z, gamma = orbit(t)
    front = z > 0
    scale = 1.0 + DEPTH_SCALE * z
    pw = int(PLANE_W * scale * zoom)
    mirrored = not front
    sp = plane_sprite(pw, mirrored, 1.0 if front else 0.62, 0.0 if front else 0.22)

    # bank into the turn, proportional to turn rate (clamped)
    eps = 0.02
    g2 = orbit(min(t + eps, DURATION))[4]
    d_gamma = ((g2 - gamma + 540) % 360 - 180) / eps      # deg/s
    bank = max(-16.0, min(16.0, 0.22 * d_gamma))

    rest = 180.0 if not mirrored else 0.0
    rot = gamma - rest - bank
    sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)

    def draw_plane(fr):
        fr.paste(sp, (int(px + cam_dx - sp.width / 2), int(py + cam_dy - sp.height / 2)), sp)

    ex = int(ecx - earth.width / 2)
    ey = int(ecy - earth.height / 2)
    if not front:
        draw_plane(frame)
    frame.paste(gl, (int(ecx - gl.width / 2), int(ecy - gl.height / 2)), gl)
    frame.paste(earth, (ex, ey), earth)
    frame.paste(strip, (ex, ey), strip)
    if front:
        draw_plane(frame)

    return frame


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        for ts in [0.0, 1.8, 3.0, 5.0, 6.5, 8.0, 9.5, 11.0]:
            render_frame(ts).save(f"test_frame_{ts:04.1f}.png")
            print("saved test frame t =", ts)
    else:
        import imageio.v2 as imageio
        out = "business_travel_hero.mp4"
        wr = imageio.get_writer(out, fps=FPS, codec="libx264", quality=8,
                                pixelformat="yuv420p", macro_block_size=1)
        for i in range(N_FRAMES):
            wr.append_data(np.array(render_frame(i / FPS)))
            if i % 60 == 0:
                print(f"frame {i}/{N_FRAMES}")
        wr.close()
        print("done:", out)
