# -*- coding: utf-8 -*-

"""Map SVG previews.

Pure functions over a map row (an Emmett row or the dict built by
`diplomatic.variants.load`): no database, no request context.

Previews use the board's palette (docs/design/README.md, "Baked palette"):
the province layer of the game page is muted with `saturate(.55)
brightness(.82)` baked into its values, and owner colours, which are data,
go through the same filter here in Python. The output is plain `rgb()`
values only (no `var()`, no `color-mix`, no relative colours), so the
document renders the same wherever it is shown through `<img>`.
"""

import re


#: the muted board palette (README "Baked palette", the "After" column)
LAND_FILL = (0x12, 0x16, 0x1A)  # coast / inland, #12161a
SEA_FILL = (0x07, 0x0A, 0x0D)  # sea and `.water` paths, #070a0d
NEUTRAL_FILL = (0x0A, 0x0C, 0x0F)  # impassable, #0a0c0f
LAND_STROKE = (0x7A, 0x80, 0x86)  # #7a8086, neutral grey for the previews (the board uses #748796)

#: the mockup's filter on the province layer
SATURATE = 0.55
BRIGHTNESS = 0.82
#: share of the muted owner colour in an owned province's fill
OWNED_TINT = 0.55  # previews are small: more solid than the board's 21% so ownership reads at 240 px
#: opacity of the muted owner colour on an owned province's border

#: previews are shown small (240 px wide for a 1300-unit map), where a
#: hairline vanishes: every border is drawn 2 map units wide
PREVIEW_STROKE_WIDTH = 2

_STYLE_ELEMENT = re.compile(r"<style\b[^>]*?(?:/>|>.*?</style\s*>)", re.S)
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.S)


def _xml_text(value):
    # `>` stays readable (CSS child combinator); only `]]>` requires escaping it
    return value.replace("&", "&amp;").replace("<", "&lt;").replace("]]>", "]]&gt;")


# ---------------------------------------------------------------- colour maths
# Colours are (r, g, b) tuples of floats or ints on the 0-255 sRGB scale.
# CSS filters operate on sRGB values directly (Chromium applies `saturate`
# and `brightness` as linear maps on the non-linearised channels), so the
# maths below is plain linear algebra on the 0-255 values.


def saturate(rgb, s):
    """CSS `saturate(s)`: the Filter Effects feColorMatrix `saturate` matrix.

        R' = (.213 + .787 s) R + (.715 - .715 s) G + (.072 - .072 s) B
        G' = (.213 - .213 s) R + (.715 + .285 s) G + (.072 - .072 s) B
        B' = (.213 - .213 s) R + (.715 - .715 s) G + (.072 + .928 s) B

    (.213, .715, .072 are the luminance weights; s = 1 is the identity,
    s = 0 is grey at the same luminance.)
    """
    r, g, b = rgb
    return (
        (0.213 + 0.787 * s) * r + (0.715 - 0.715 * s) * g + (0.072 - 0.072 * s) * b,
        (0.213 - 0.213 * s) * r + (0.715 + 0.285 * s) * g + (0.072 - 0.072 * s) * b,
        (0.213 - 0.213 * s) * r + (0.715 - 0.715 * s) * g + (0.072 + 0.928 * s) * b,
    )


def brightness(rgb, k):
    """CSS `brightness(k)`: every channel multiplied by k (C' = k C)."""
    return tuple(k * c for c in rgb)


def mute(rgb):
    """The board's muting, `saturate(.55) brightness(.82)`.

    Composed, at s = .55 and k = .82 (README "Baked palette", `--cm`):

        R' = .5296 R + .2638 G + .0266 B
        G' = .0786 R + .7148 G + .0266 B
        B' = .0786 R + .2638 G + .4776 B
    """
    return brightness(saturate(rgb, SATURATE), BRIGHTNESS)


def mix(rgb, ground, p):
    """`color-mix(in srgb, rgb p, ground)`: C = p C_rgb + (1 - p) C_ground."""
    return tuple(p * a + (1 - p) * b for a, b in zip(rgb, ground, strict=True))


def css_rgb(rgb):
    """`rgb(r, g, b)` with each channel rounded and clamped to 0-255."""
    r, g, b = (min(255, max(0, round(c))) for c in rgb)
    return f"rgb({r}, {g}, {b})"


def owner_colours(color):
    """(fill, stroke) of a province owned by `color` ({'r', 'g', 'b'}).

    Previews skip the board's muting (`mute`, kept for reference): at 240 px
    the muted tint looks worn out. fill = `color-mix(in srgb, color 55%,
    land fill)`; stroke = the colour itself (unused by the preview rules).
    """
    rgb = (color["r"], color["g"], color["b"])
    return mix(rgb, LAND_FILL, OWNED_TINT), rgb


# ---------------------------------------------------------------- stylesheet


def css_string(value):
    """Quote `value` as a CSS string (for attribute selectors)."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\a ")
    return f'"{escaped}"'


def base_style():
    """The muted land / sea / impassable rules, borders widened for previews."""
    land, sea, neutral = css_rgb(LAND_FILL), css_rgb(SEA_FILL), css_rgb(NEUTRAL_FILL)
    land_stroke = css_rgb(LAND_STROKE)
    return "\n".join(
        [
            # one stroke colour for every path: neighbours share edges, so each border is painted twice
            # (once per province) and the later one wins; different colours per kind or owner would make
            # a border's colour depend on document order
            f".provinces path {{ stroke: {land_stroke}; stroke-width: {PREVIEW_STROKE_WIDTH}; stroke-linejoin: round; }}",
            f'g[data-kind="coast"] > path:not(.water), g[data-kind="inland"] > path {{ fill: {land}; }}',
            f'g[data-kind="neutral"] > path:not(.water) {{ fill: {neutral}; }}',
            f'g[data-kind="sea"] > path, .provinces path.water {{ fill: {sea}; }}',
        ]
    )


def owner_rule(province, color):
    fill, _ = owner_colours(color)
    selector = f"g[data-province={css_string(province)}] > path:not(.water)"
    return f"{selector} {{ fill: {css_rgb(fill)}; }}"


def preview_style(row):
    """The board palette, then one fill and border per province owned at start.

    The stored document's own <style> (the converter's draft palette) is
    ignored. Owner rules skip `.water` paths (water children such as
    `Denmark (strait)` keep the sea fill) and, having the same specificity
    as the land rules, win by coming after them.
    """
    names, countries = row["names"], row["countries"]
    rules = [
        owner_rule(names[str(pid)], countries[country])
        for country, pids in row["init"]["territories"].items()
        for pid in pids
    ]
    return "\n".join([base_style(), *rules])


def replace_style(svg, css):
    """`svg` with its first <style> element replaced by one holding `css`.

    The rest of the document is kept byte for byte. A document without a
    <style> gets one right after the opening <svg> tag.
    """
    element = f"<style>\n{_xml_text(css)}\n  </style>"
    rv, count = _STYLE_ELEMENT.subn(lambda _: element, svg, count=1)
    if count:
        return rv
    rv, count = _SVG_OPEN.subn(lambda match: f"{match.group(0)}\n  {element}", svg, count=1)
    if not count:
        raise ValueError("not an SVG document")
    return rv


def preview_svg(row):
    return replace_style(row["svg"], preview_style(row))
