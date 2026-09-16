from html import escape

# ============================================================
# ASCII → ANIMATED SVG
# ============================================================

input_path = "assets/my_photo1_ascii.txt"
output_path = "assets/portrait.svg"

print("Opening ASCII portrait...")

# Read the ASCII portrait exactly as generated
with open(input_path, "r", encoding="utf-8") as file:
    lines = file.read().splitlines()

# ============================================================
# SETTINGS
# ============================================================

cols = 90

# Use a fixed character grid.
# 16px Courier-style monospace characters are ~9.6px wide.
font_size = 16
char_width = 9.6
char_height = 16

rows = len(lines)

svg_width = cols * char_width
svg_height = rows * char_height

print("Columns:", cols)
print("Rows:", rows)
print("SVG size:", svg_width, "x", svg_height)

# ============================================================
# START SVG
# ============================================================

svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{svg_width}" '
    f'height="{svg_height}" '
    f'viewBox="0 0 {svg_width} {svg_height}">'
)

# ============================================================
# ANIMATION CLIPS
# ============================================================

svg.append("<defs>")

svg.append(
    '<linearGradient id="asciiGradient" x1="0%" y1="0%" x2="100%" y2="0%">'
    '<stop offset="0%" stop-color="#00e5ff"/>'
    '<stop offset="100%" stop-color="#a855f7"/>'
    '</linearGradient>'
)

for i in range(rows):
    y = i * char_height

    svg.append(
        f'<clipPath id="row{i}">'
        f'<rect x="0" y="{y}" '
        f'width="0" '
        f'height="{char_height}">'
        f'<animate '
        f'attributeName="width" '
        f'from="0" '
        f'to="{svg_width}" '
        f'dur="0.8s" '
        f'begin="{i * 0.09:.2f}s" '
        f'fill="freeze"/>'
        f'</rect>'
        f'</clipPath>'
    )

svg.append("</defs>")

# ============================================================
# PORTRAIT
# ============================================================

svg.append(
    '<g '
    'font-family="Courier New, Liberation Mono, DejaVu Sans Mono, monospace" '
    f'font-size="{font_size}px" '
    'font-weight="400" '
    'fill="url(#asciiGradient)" '
    'xml:space="preserve">'
)

# ============================================================
# RENDER EVERY CHARACTER AT A FIXED X POSITION
# ============================================================

for row_index, original_line in enumerate(lines):

    # Force exactly 90 columns
    line = original_line.ljust(cols)[:cols]

    baseline_y = (row_index + 1) * char_height - 2

    for col_index, character in enumerate(line):

        # Spaces don't need an SVG element
        if character == " ":
            continue

        x = col_index * char_width

        # Escape characters such as &, < and >
        character = escape(character)

        svg.append(
            f'<text '
            f'x="{x:.2f}" '
            f'y="{baseline_y:.2f}" '
            f'clip-path="url(#row{row_index})">'
            f'{character}'
            f'</text>'
        )

svg.append("</g>")

svg.append("</svg>")

# ============================================================
# SAVE
# ============================================================

with open(output_path, "w", encoding="utf-8") as file:
    file.write("\n".join(svg))

print()
print("===================================")
print("SVG portrait created successfully!")
print("===================================")
print("Saved:", output_path)