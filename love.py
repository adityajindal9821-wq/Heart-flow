import math as m
import random as r
import turtle as t
import tkinter.font as tkf

SC = 21
OY = 20
DURATION = 10
TICK = 16
ANIM = 42
LIFT = 34
GAP = 7
SIZES = (9, 10, 11, 12)
FONT = "Arial"
BG = "#060208"

screen = t.Screen()
screen.setup(800, 800)# My Python project
screen.bgcolor(BG)
screen.title("Love Heart")
screen.tracer(0)

cv = screen.getcanvas()
rng = r.Random(11)

PHRASES = [
    "I love you", "আমি তোমাকে ভালোবাসব", "Te amo", "Je t'aime",
    "Ich liebe dich", "Ti amo", "Eu te amo", "Я тебя люблю",
    "사랑해", "愛してる", "我爱你", "Anh yêu em",
    "Σ' αγαπώ", "میں آپ سے محبت کرتا ہوں", "Jag älskar dig", "Kocham cię",
    "ฉันรักเธอ", "मैं तुमसे प्यार करता हूँ", "Main twade naal pyaar karda vaan", "Я тебе кохаю",
]

_fonts = {}


def font_for(size):
    if size not in _fonts:
        _fonts[size] = tkf.Font(
            root=cv, family=FONT, size=size, weight="bold"
        )
    return _fonts[size]


def heart(a):
    x = 16 * (m.sin(a) ** 3)
    y = (
        13 * m.cos(a)
        - 5 * m.cos(2 * a)
        - 2 * m.cos(3 * a)
        - m.cos(4 * a)
    )
    return x * SC, y * SC + OY


def hx(c):
    return "#%02x%02x%02x" % tuple(
        int(max(0, min(1, v)) * 255) for v in c
    )


def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(p + (q - p) * k for p, q in zip(a, b))


def dim(c, k):
    return tuple(v * k for v in c)


POLY = [heart(2 * m.pi * i / 720) for i in range(720)]
EDGES = list(zip(POLY, POLY[1:] + POLY[:1]))
YMAX = max(p[1] for p in POLY)
YMIN = min(p[1] for p in POLY)
CY = (YMAX + YMIN) / 2


def spans(y):
    xs = []
    for (x1, y1), (x2, y2) in EDGES:
        if (y1 <= y < y2) or (y2 <= y < y1):
            if y2 != y1:
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo > 14:
                out.append((lo, hi))
    return out


def phrase_cycle():
    while True:
        order = PHRASES[:]
        rng.shuffle(order)
        yield from order


def math_dist(x, y):
    return m.hypot(x / (16 * SC), (y - CY) / (14.5 * SC))


BGC = tuple(int(BG[i:i + 2], 16) / 255 for i in (1, 3, 5))
FLASH = (1.0, 0.78, 0.78)


def build():
    cycle = phrase_cycle()
    row_h = max(font_for(z).metrics("linespace") for z in SIZES) + 4
    half = row_h / 2
    placed = []

    y = YMAX - half
    while y > YMIN + half:
        row = intersect(spans(y + half), spans(y - half))

        for lo, hi in row:
            lo += 4
            hi -= 4
            cur = lo + rng.uniform(0, 8)
            line = []

            while True:
                fit = None
                for _ in range(10):
                    text = next(cycle)
                    size = rng.choice(SIZES)
                    w = font_for(size).measure(text)
                    if cur + w <= hi:
                        fit = (text, size, w)
                        break
                if fit is None:
                    break

                text, size, w = fit
                line.append([cur + w / 2, text, size, w])
                cur += w + GAP

            if not line:
                continue

            if len(line) > 1:
                left = hi - (line[-1][0] + line[-1][3] / 2)
                for i, item in enumerate(line):
                    item[0] += left * i / (len(line) - 1)
            else:
                line[0][0] = (lo + hi) / 2

            for i, (x, text, size, width) in enumerate(line):
                placed.append({
                    "x": x,
                    "y": y,
                    "text": text,
                    "size": size,
                    "edge": i == 0 or i == len(line) - 1,
                })

        y -= row_h

    wine = (0.58, 0.0, 0.09)
    crimson = (0.90, 0.05, 0.14)
    blood = (0.98, 0.10, 0.16)

    for p in placed:
        rad = min(1.0, math_dist(p["x"], p["y"]))
        base = mix(wine, crimson, 0.25 + 0.75 * rad)
        base = mix(
            base, blood,
            min(1.0, rng.uniform(0, 0.35) + (0.3 if p["edge"] else 0))
        )
        p["color"] = tuple(min(1.0, v) for v in base)
        p["rad"] = rad

    edges = [p for p in placed if p["edge"]]
    inner = [p for p in placed if not p["edge"]]

    edges.sort(
        key=lambda p: m.atan2(p["x"], p["y"] - CY) % (2 * m.pi)
    )
    inner.sort(key=lambda p: -p["rad"] + rng.uniform(0, 0.08))
    return edges + inner


main_ids = []
active = []
acc = 0.0
spawning = True
closed = False


def clamp(v):
    return max(0.0, min(1.0, v))


def spawn(p):
    x, y = p["x"], -p["y"]
    size, text, color = p["size"], p["text"], p["color"]
    font = (FONT, size, "bold")
    big = (FONT, size + 1, "bold")

    shadow = cv.create_text(
        x + 2, y + 3, text=text, font=font, fill=BG
    )
    halo = cv.create_text(
        x, y, text=text, font=big, fill=BG
    )
    main = cv.create_text(
        x, y - LIFT, text=text, font=font, fill=BG
    )

    p.update(
        shadow=shadow,
        halo=halo,
        main=main,
        f=0,
        dx=rng.uniform(-10, 10),
    )
    main_ids.append((main, color))
    active.append(p)


def math_sin(v):
    return m.sin(m.pi * v)


def animate(p):
    p["f"] += 1
    u = clamp(p["f"] / ANIM)
    e = 1 - (1 - u) ** 3
    color = p["color"]
    x, y = p["x"], -p["y"]

    hover = (1 - e) * LIFT
    px = x + p["dx"] * (1 - e)
    py = y - hover

    cv.itemconfig(
        p["shadow"], fill=hx(mix(BGC, dim(color, 0.30), e))
    )
    cv.itemconfig(
        p["halo"], fill=hx(mix(BGC, dim(color, 0.20), e * e))
    )
    cv.coords(p["halo"], px, py)

    flash = 0.75 * math_sin(clamp((u - 0.55) / 0.45))
    final_color = mix(mix(BGC, color, e ** 1.5), FLASH, flash)

    cv.itemconfig(p["main"], fill=hx(final_color))
    cv.coords(p["main"], px, py)

    if u >= 1:
        cv.coords(p["halo"], x, y)
        cv.coords(p["main"], x, y)
        cv.itemconfig(p["main"], fill=hx(color))
        return False

    return True


ORDER = build()
items = iter(ORDER)
RATE = len(ORDER) / max(1, DURATION * 1000 / TICK)


def safe(i, color):
    if closed:
        return
    try:
        cv.itemconfig(i, fill=hx(color))
    except Exception:
        pass


def shimmer():
    if closed:
        return

    if main_ids:
        i, color = rng.choice(main_ids)
        safe(i, mix(color, FLASH, 0.6))
        cv.after(260, lambda i=i, c=color: safe(i, c))

    cv.after(140, shimmer)


def step():
    global spawning, acc

    if closed:
        return

    if spawning:
        acc += RATE
        while acc >= 1:
            try:
                p = next(items)
            except StopIteration:
                spawning = False
                break
            acc -= 1
            spawn(p)

    active[:] = [p for p in active if animate(p)]

    if not spawning and not active:
        shimmer()
        return

    cv.after(TICK, step)


def on_close():
    global closed
    closed = True
    try:
        screen.bye()
    except t.Terminator:
        pass


screen.listen()
screen.getcanvas().winfo_toplevel().protocol("WM_DELETE_WINDOW", on_close)

cv.after(200, step)

try:
    t.mainloop()
except t.Terminator:
    pass