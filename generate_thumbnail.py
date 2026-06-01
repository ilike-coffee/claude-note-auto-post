"""
Claude素人 note サムネイル自動生成スクリプト
Pillowを使って毎日同じデザインテンプレートで画像を生成する
"""

import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillowをインストールします...")
    os.system("pip install Pillow --break-system-packages")
    from PIL import Image, ImageDraw, ImageFont


def create_thumbnail(day: int, title: str, output_path: str):
    """
    サムネイル画像を生成する
    サイズ: 1280x670px
    デザイン: オレンジ背景、白いロボット、Day番号、タイトル
    """

    W, H = 1280, 670

    # ベースカラー
    COLOR_BG_MAIN   = "#E8630A"   # メインオレンジ
    COLOR_BG_ACCENT = "#F5A623"   # アクセントオレンジ
    COLOR_WHITE     = "#FFFFFF"
    COLOR_DARK      = "#C44D00"   # 影・装飾用

    img  = Image.new("RGB", (W, H), COLOR_BG_MAIN)
    draw = ImageDraw.Draw(img)

    # --- 背景装飾：右下に大きな円 ---
    draw.ellipse([(800, 300), (1500, 1000)], fill=COLOR_BG_ACCENT)

    # --- 背景装飾：左上に小さな円 ---
    draw.ellipse([(-80, -80), (200, 200)], fill=COLOR_DARK)

    # --- ロボットアイコン（左エリア） ---
    _draw_robot(draw, cx=220, cy=340, size=180, color=COLOR_WHITE)

    # --- 「Claude素人」テキスト（ロボット下） ---
    font_small = _get_font(28)
    draw.text((220, 490), "Claude素人", font=font_small,
              fill=COLOR_WHITE, anchor="mm")

    # --- Day番号（右エリア上部） ---
    font_day = _get_font(52, bold=True)
    day_text = f"Day {day:02d}"
    draw.text((800, 160), day_text, font=font_day,
              fill=COLOR_WHITE, anchor="mm")

    # Day番号の下にアンダーライン
    draw.rectangle([(640, 192), (960, 197)], fill=COLOR_WHITE)

    # --- タイトル（右エリア中央） ---
    font_title = _get_font(54, bold=True)
    _draw_wrapped_text(draw, title, font_title, COLOR_WHITE,
                       x=800, y=320, max_width=580, line_height=68)

    # --- 保存 ---
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"✅ サムネイル生成: {output_path}")


def _draw_robot(draw, cx, cy, size, color):
    """シンプルなロボットを描画する"""
    s = size

    # 頭
    head_x1 = cx - s * 0.35
    head_y1 = cy - s * 0.55
    head_x2 = cx + s * 0.35
    head_y2 = cy - s * 0.10
    draw.rounded_rectangle(
        [(head_x1, head_y1), (head_x2, head_y2)],
        radius=s * 0.1, fill=color
    )

    # 目（左）
    draw.ellipse([
        (cx - s * 0.22, cy - s * 0.45),
        (cx - s * 0.08, cy - s * 0.31)
    ], fill="#E8630A")

    # 目（右）
    draw.ellipse([
        (cx + s * 0.08, cy - s * 0.45),
        (cx + s * 0.22, cy - s * 0.31)
    ], fill="#E8630A")

    # 口
    draw.rounded_rectangle([
        (cx - s * 0.18, cy - s * 0.22),
        (cx + s * 0.18, cy - s * 0.14)
    ], radius=s * 0.04, fill="#E8630A")

    # アンテナ
    draw.rectangle([
        (cx - s * 0.03, cy - s * 0.72),
        (cx + s * 0.03, cy - s * 0.55)
    ], fill=color)
    draw.ellipse([
        (cx - s * 0.08, cy - s * 0.80),
        (cx + s * 0.08, cy - s * 0.64)
    ], fill=color)

    # 胴体
    draw.rounded_rectangle([
        (cx - s * 0.42, cy - s * 0.08),
        (cx + s * 0.42, cy + s * 0.40)
    ], radius=s * 0.08, fill=color)

    # 左腕
    draw.rounded_rectangle([
        (cx - s * 0.62, cy - s * 0.05),
        (cx - s * 0.44, cy + s * 0.30)
    ], radius=s * 0.06, fill=color)

    # 右腕
    draw.rounded_rectangle([
        (cx + s * 0.44, cy - s * 0.05),
        (cx + s * 0.62, cy + s * 0.30)
    ], radius=s * 0.06, fill=color)

    # 左足
    draw.rounded_rectangle([
        (cx - s * 0.30, cy + s * 0.42),
        (cx - s * 0.08, cy + s * 0.65)
    ], radius=s * 0.06, fill=color)

    # 右足
    draw.rounded_rectangle([
        (cx + s * 0.08, cy + s * 0.42),
        (cx + s * 0.30, cy + s * 0.65)
    ], radius=s * 0.06, fill=color)


def _get_font(size: int, bold: bool = False):
    """フォントを取得する（システムフォントにフォールバック）"""
    font_paths = [
        # macOS
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_wrapped_text(draw, text, font, color, x, y, max_width, line_height):
    """テキストを折り返して描画する"""
    # 文字数ベースで折り返し（日本語対応）
    chars_per_line = max(1, max_width // (font.size if hasattr(font, 'size') else 40))
    lines = []
    while len(text) > chars_per_line:
        lines.append(text[:chars_per_line])
        text = text[chars_per_line:]
    if text:
        lines.append(text)

    total_h = len(lines) * line_height
    start_y = y - total_h // 2

    for i, line in enumerate(lines):
        draw.text((x, start_y + i * line_height), line,
                  font=font, fill=color, anchor="mm")


if __name__ == "__main__":
    # 引数: day title output_path
    if len(sys.argv) < 4:
        print("Usage: python generate_thumbnail.py <day> <title> <output_path>")
        sys.exit(1)

    day_num   = int(sys.argv[1])
    title_str = sys.argv[2]
    out_path  = sys.argv[3]

    create_thumbnail(day_num, title_str, out_path)
