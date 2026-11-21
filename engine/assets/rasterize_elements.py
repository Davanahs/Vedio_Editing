"""Generate transparent PNG render counterparts for the hand-authored SVG assets."""
from pathlib import Path
from PIL import Image, ImageDraw
import math

OUT = Path(__file__).resolve().parent / "elements"
SIZE = 512


def canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def star_points(cx, cy, outer, inner, count=4):
    points = []
    for i in range(count * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / count
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


def save(name, draw_fn):
    image = canvas()
    draw_fn(ImageDraw.Draw(image))
    image.save(OUT / f"{name}.png", optimize=True)


def draw_sparkles(d):
    d.polygon(star_points(170, 210, 110, 22), fill="#f8c85a", outline="#fff2c7", width=8)
    d.polygon(star_points(360, 300, 75, 18), fill="#f8c85a", outline="#fff2c7", width=7)
    for x, y, r in [(310, 110, 13), (100, 390, 10), (430, 110, 9)]:
        d.ellipse((x-r, y-r, x+r, y+r), fill="#fff2c7")


def draw_heart(d):
    d.ellipse((92, 82, 278, 282), fill="#fb7185", outline="#fb7185", width=10)
    d.ellipse((234, 82, 420, 282), fill="#fb7185", outline="#fb7185", width=10)
    d.polygon([(100, 208), (412, 208), (256, 430)], fill="#fb7185")
    d.arc((82, 68, 430, 430), 185, 352, fill="#fecdd3", width=12)


def draw_polaroid(d):
    d.rounded_rectangle((82, 28, 430, 484), radius=10, fill="#fffdf6", outline="#e8dfcc", width=8)
    d.rectangle((116, 62, 396, 365), fill="#e8eef0")
    d.ellipse((302, 105, 372, 175), fill="#f3cf83")
    d.polygon([(116, 314), (210, 194), (267, 260), (318, 182), (396, 294), (396, 365), (116, 365)], fill="#9ab9aa")
    d.rounded_rectangle((198, 411, 314, 423), radius=6, fill="#d7cbb5")


def draw_flower(d):
    petals = [(215, 24, 297, 210), (215, 302, 297, 488),
              (24, 215, 210, 297), (302, 215, 488, 297),
              (70, 70, 220, 220), (292, 292, 442, 442),
              (292, 70, 442, 220), (70, 292, 220, 442)]
    for bounds in petals:
        d.ellipse(bounds, fill="#f9a8d4", outline="#fff1f8", width=7)
    d.ellipse((220, 220, 292, 292), fill="#fbbf24")


def draw_viewfinder(d):
    color = "#b6ffd4"
    w = 22
    for box, start, end in [((42,42,190,190),0,90),((322,42,470,190),90,180),((42,322,190,470),270,360),((322,322,470,470),180,270)]:
        x1,y1,x2,y2 = box
        d.line([(x1,y2),(x1,y1),(x2,y1)], fill=color, width=w, joint="curve")
    d.ellipse((190,190,322,322), outline=color, width=10)
    d.ellipse((246,246,266,266), fill=color)


def draw_glass(d):
    d.rounded_rectangle((26, 142, 486, 370), radius=92, fill=(103,232,249,90), outline=(165,243,252,230), width=12)
    d.line((78, 206, 260, 206), fill=(255,255,255,180), width=14)


def draw_music_player(d):
    d.rounded_rectangle((12, 122, 500, 390), radius=48, fill=(23,25,35,245), outline="#d5b7ff", width=8)
    d.rounded_rectangle((38, 154, 174, 290), radius=24, fill="#a78bfa")
    d.ellipse((70, 218, 122, 270), fill="#fff")
    d.rectangle((94, 170, 106, 240), fill="#fff")
    d.line((205, 184, 448, 184), fill="#fff", width=14)
    d.line((205, 228, 390, 228), fill="#aaaabb", width=11)
    d.line((42, 342, 466, 342), fill="#555768", width=12)
    d.line((42, 342, 238, 342), fill="#c4b5fd", width=12)
    d.ellipse((225, 327, 251, 357), fill="#fff")


def draw_retro_hud(d):
    d.rounded_rectangle((12, 86, 500, 426), radius=24, fill=(7,17,15,190), outline="#75f0ad", width=8)
    d.ellipse((42, 116, 78, 152), fill="#fb5252")
    d.text((96, 112), "REC", fill="#fff", stroke_width=1)
    color, w = "#75f0ad", 12
    d.line([(52,210),(52,160),(130,160)], fill=color, width=w)
    d.line([(382,160),(460,160),(460,210)], fill=color, width=w)
    d.line([(52,300),(52,350),(130,350)], fill=color, width=w)
    d.line([(382,350),(460,350),(460,300)], fill=color, width=w)
    d.text((155, 238), "CAM 01  |  AUTO FOCUS", fill="#b4ffd2")


def draw_tape(d):
    d.polygon([(42,112),(480,80),(466,368),(28,400)], fill=(247,215,148,185), outline="#fff3cb")
    for y in [176, 238, 300]:
        d.line((65,y,445,y-26), fill=(255,247,223,200), width=8)


def draw_tech_card(d):
    d.rounded_rectangle((12, 86, 500, 426), radius=26, fill=(7,24,39,235), outline="#38bdf8", width=8)
    for y, length in [(154,160),(195,110),(244,192),(285,132)]:
        d.line((48,y,48+length,y), fill="#67e8f9", width=12)
    d.line([(330,160),(388,222),(330,284)], fill="#a5f3fc", width=14, joint="curve")
    d.line([(280,222),(330,160)], fill="#a5f3fc", width=14)
    d.ellipse((48, 340, 76, 368), fill="#34d399")
    d.line((100,354,408,354), fill="#64748b", width=12)


def draw_subject_outline(d):
    white = "#ffffff"
    d.ellipse((170, 40, 344, 222), outline=white, width=15)
    d.line([(175,180),(136,216),(122,288),(84,330),(74,438),(438,438),(428,330),(390,288),(376,216),(339,180)], fill=white, width=14, joint="curve")
    d.line((130, 454, 382, 454), fill="#f9a8d4", width=8)


def draw_doodle_arrow(d):
    pink = "#fb7185"
    d.line([(58,390),(126,268),(228,190),(365,150)], fill=pink, width=20, joint="curve")
    d.line([(326,112),(390,142),(348,204)], fill=pink, width=20, joint="curve")


def draw_torn_frame(d):
    points = [(30,20),(130,30),(240,18),(360,34),(482,22),(470,180),(486,300),(470,480),(355,466),(240,482),(120,464),(32,480),(46,330),(28,200)]
    d.polygon(points, fill="#fff9e8", outline="#dfcfaa")
    d.rectangle((90,90,422,422), fill=(0,0,0,0), outline="#efe3c7", width=6)


def draw_film_frame(d):
    d.rounded_rectangle((10, 10, 502, 502), radius=18, fill=(17,24,39,70), outline="#f8fafc", width=18)
    for x in range(62, 470, 88):
        d.rounded_rectangle((x,22,x+48,62),radius=7,fill="#f8fafc")
        d.rounded_rectangle((x,450,x+48,490),radius=7,fill="#f8fafc")
    d.line((54, 90, 54, 422), fill="#fbbf24", width=6)
    d.line((458, 90, 458, 422), fill="#fbbf24", width=6)


def draw_kinetic_title(d):
    d.polygon([(30,122),(426,38),(482,360),(86,470)], fill="#facc15", outline="#fff7ae")
    d.line((108,205,350,152), fill="#111827", width=32)
    d.line((130,286,320,244), fill="#111827", width=28)
    d.line((438,42,490,18), fill="#fb7185", width=18)


def draw_catalog(name, d):
    """Draw one of the legacy catalog concepts as a transparent line-art sticker."""
    blue, pale, accent = "#38bdf8", "#e0f2fe", "#a78bfa"
    if name in {"gemini", "bulb"}:
        if name == "gemini":
            d.polygon(star_points(256,245,178,48),fill="#8b5cf6",outline="#ddd6fe",width=10)
            d.polygon(star_points(134,115,46,14),fill="#facc15")
            d.polygon(star_points(390,380,36,12),fill="#67e8f9")
        else:
            d.ellipse((150,65,362,280),fill="#3b2e15",outline="#facc15",width=15)
            d.arc((192,230,320,380),0,180,fill="#fde68a",width=15)
            for y in (306,340,374): d.line((208,y,304,y),fill="#facc15",width=12)
    elif name == "robot":
        d.rounded_rectangle((98,110,414,350),radius=55,fill="#132b45",outline=blue,width=15)
        d.line((256,65,256,108),fill=blue,width=12); d.ellipse((235,42,277,84),fill="#facc15")
        d.rounded_rectangle((148,175,210,238),radius=20,fill="#67e8f9"); d.rounded_rectangle((302,175,364,238),radius=20,fill="#67e8f9")
        d.arc((192,215,320,310),8,172,fill=pale,width=12)
    elif name == "brain_ai":
        for box in [(82,150,235,300),(135,80,275,230),(274,80,420,230),(278,150,435,305),(164,263,354,405)]: d.ellipse(box,fill="#40243e",outline="#f472b6",width=12)
        d.line((256,100,256,385),fill="#fbcfe8",width=9); d.line((162,185,224,185,224,260),fill="#fbcfe8",width=8); d.line((350,185,286,185,286,260),fill="#fbcfe8",width=8)
    elif name == "chip":
        d.rounded_rectangle((145,145,367,367),radius=34,fill="#071827",outline=blue,width=16); d.rectangle((205,205,307,307),outline="#67e8f9",width=12)
        for p in range(175,350,44):
            d.line((p,90,p,140),fill=blue,width=12); d.line((p,372,p,422),fill=blue,width=12); d.line((90,p,140,p),fill=blue,width=12); d.line((372,p,422,p),fill=blue,width=12)
        d.line((225,256,256,287,306,220),fill="#34d399",width=14)
    elif name == "laptop":
        d.rounded_rectangle((78,82,434,348),radius=22,fill="#142536",outline="#94a3b8",width=14); d.rectangle((108,112,404,312),fill="#0b1724",outline=blue,width=6)
        d.line((155,180,250,180),fill="#67e8f9",width=13); d.line((155,220,345,220),fill="#64748b",width=11); d.polygon([(48,365),(464,365),(420,420),(92,420)],fill="#cbd5e1",outline="#64748b")
    elif name == "sun_warmth":
        d.ellipse((160,160,352,352),fill="#fbbf24",outline="#fff2c7",width=13)
        for a in range(0,360,45):
            q=math.radians(a); d.line((256+math.cos(q)*125,256+math.sin(q)*125,256+math.cos(q)*205,256+math.sin(q)*205),fill="#f59e0b",width=16)
    elif name == "recipe_dish":
        d.arc((95,165,417,455),0,180,fill="#fb923c",width=20); d.line((98,310,418,310),fill="#fb923c",width=18)
        for x,y,c in [(185,340,"#22c55e"),(260,360,"#ef4444"),(335,340,"#facc15")]: d.ellipse((x-28,y-28,x+28,y+28),fill=c)
        d.arc((145,125,245,285),190,345,fill="#fcd34d",width=13); d.arc((270,125,370,285),190,345,fill="#fcd34d",width=13)
    elif name == "chef_hat":
        for box in [(100,120,245,270),(185,55,325,255),(270,120,415,270)]: d.ellipse(box,fill="#fffdf6",outline="#94a3b8",width=12)
        d.rounded_rectangle((90,205,425,310),radius=28,fill="#fffdf6",outline="#94a3b8",width=12); d.line((128,340,385,340),fill="#cbd5e1",width=18)
    elif name == "fresh_leaf":
        d.polygon([(84,405),(106,198),(205,102),(398,78),(420,268),(306,398)],fill="#14532d",outline="#86efac"); d.line((98,412,388,115),fill="#bbf7d0",width=13)
        for p in [(170,330,235,300),(218,280,275,230),(266,232,330,175)]: d.line(p,fill="#4ade80",width=9)
    elif name == "music_card": draw_music_player(d)
    elif name == "headphones":
        d.arc((93,56,419,390),180,360,fill=accent,width=28); d.rounded_rectangle((78,228,168,380),radius=28,fill="#211c36",outline="#c4b5fd",width=14); d.rounded_rectangle((344,228,434,380),radius=28,fill="#211c36",outline="#c4b5fd",width=14)
    elif name == "sound_wave":
        for x,h in [(96,70),(152,126),(208,186),(264,145),(320,102),(376,62)]: d.rounded_rectangle((x,256-h,x+30,256+h),radius=15,fill="#67e8f9")
    elif name == "book":
        d.rounded_rectangle((58,90,252,414),radius=20,fill="#1e3a5a",outline="#93c5fd",width=14); d.rounded_rectangle((260,90,454,414),radius=20,fill="#172554",outline="#93c5fd",width=14); d.line((256,104,256,425),fill=pale,width=15)
        for y in (170,225,280,335): d.line((95,y,215,y),fill="#bfdbfe",width=9); d.line((298,y,418,y),fill="#bfdbfe",width=9)
    elif name == "presentation":
        d.rounded_rectangle((48,70,464,343),radius=24,fill="#111827",outline=blue,width=14); d.line((256,344,256,420),fill="#cbd5e1",width=16); d.line((174,428,338,428),fill="#cbd5e1",width=16)
        for x,y,c in [(128,278,"#34d399"),(210,220,"#facc15"),(292,250,"#f472b6"),(374,164,"#60a5fa")]: d.line((x,278,x,y),fill=c,width=34)
    elif name == "quiz":
        d.rounded_rectangle((92,54,420,460),radius=28,fill="#172554",outline="#a5b4fc",width=14)
        for y in (144,245,346): d.rounded_rectangle((130,y-20,170,y+20),radius=8,outline="#c4b5fd",width=8); d.line((195,y,372,y),fill="#e0e7ff",width=12)
        d.line((136,144,149,158,169,125),fill="#4ade80",width=9); d.line((136,346,149,360,169,327),fill="#4ade80",width=9)
    elif name == "audio_mic":
        d.rounded_rectangle((204,62,308,282),radius=52,fill="#1e293b",outline="#fda4af",width=15); d.arc((126,145,386,385),0,180,fill="#fb7185",width=17); d.line((256,385,256,437),fill="#cbd5e1",width=14); d.line((190,438,322,438),fill="#cbd5e1",width=14)
    elif name == "rec_dot":
        for box in [(62,62,174,174),(338,62,450,174),(62,338,174,450),(338,338,450,450)]: d.rectangle(box,outline="#75f0ad",width=14)
        d.ellipse((203,87,309,193),fill="#ef4444",outline="#fecaca",width=9); d.line((206,256,336,256),fill="#75f0ad",width=12)
    elif name == "gamepad":
        d.rounded_rectangle((56,148,456,376),radius=104,fill="#211b37",outline="#c4b5fd",width=16); d.line((128,251,210,251),fill="#e9d5ff",width=18); d.line((169,210,169,292),fill="#e9d5ff",width=18)
        for x,y,c in [(320,215,"#f472b6"),(368,263,"#60a5fa"),(320,310,"#4ade80")]: d.ellipse((x-21,y-21,x+21,y+21),fill=c)
    elif name == "money":
        d.rounded_rectangle((65,125,447,385),radius=38,fill="#064e3b",outline="#6ee7b7",width=15); d.ellipse((198,174,314,334),outline="#a7f3d0",width=13); d.line((107,173,154,173),fill="#34d399",width=12); d.line((360,337,406,337),fill="#34d399",width=12)
    elif name == "comment":
        d.rounded_rectangle((60,78,452,347),radius=58,fill="#172554",outline="#93c5fd",width=15); d.polygon([(151,336),(130,433),(245,345)],fill="#172554",outline="#93c5fd")
        for x in (172,256,340): d.ellipse((x-14,194,x+14,222),fill="#bfdbfe")
    elif name == "bell":
        d.arc((126,55,386,367),180,360,fill="#fbbf24",width=16); d.polygon([(134,321),(166,270),(174,182),(194,125),(226,88),(286,88),(318,125),(338,182),(346,270),(378,321)],fill="#332a19",outline="#fbbf24"); d.line((134,321,378,321),fill="#fde68a",width=17); d.ellipse((223,340,289,406),fill="#f59e0b")
    else:
        draw_heart(d)


if __name__ == "__main__":
    save("sparkle_stars", draw_sparkles)
    save("doodle_heart", draw_heart)
    save("polaroid_frame", draw_polaroid)
    save("flower_blossom", draw_flower)
    save("viewfinder", draw_viewfinder)
    save("glass_pill", draw_glass)
    save("music_player_card", draw_music_player)
    save("retro_recording_hud", draw_retro_hud)
    save("scrapbook_tape", draw_tape)
    save("tech_interface_card", draw_tech_card)
    save("subject_outline", draw_subject_outline)
    save("doodle_arrow", draw_doodle_arrow)
    save("torn_paper_frame", draw_torn_frame)
    save("film_frame", draw_film_frame)
    save("kinetic_title_card", draw_kinetic_title)
    for name in ("gemini","robot","brain_ai","chip","laptop","sun_warmth","recipe_dish","chef_hat","fresh_leaf","music_card","headphones","sound_wave","book","presentation","quiz","audio_mic","bulb","rec_dot","gamepad","money","comment","heart","bell"):
        save(name, lambda d, asset_name=name: draw_catalog(asset_name, d))
