# -*- coding: utf-8 -*-

"""Map SVG previews.

Pure functions over a map row (an Emmett row or the dict built by
`diplomatic.variants.load`): no database, no request context.
"""

import re
import xml.etree.ElementTree as ET


#: the converter's display rules (tools/png_to_svg.py), used only when the
#: stored document has no <style> of its own
DEFAULT_STYLE = """
g[data-kind="sea"] path { fill: #a9cbe0; }
g[data-kind="coast"] path, g[data-kind="inland"] path { fill: #e9dfbd; }
g[data-kind="neutral"] path { fill: #cfc8b0; }
.provinces path.water { fill: #a9cbe0; }
.provinces path { stroke: #6b6b6b; stroke-width: 0.6; stroke-linejoin: round; }
""".strip("\n")

#: previews are shown small (240 px wide for a 1300-unit map), where the
#: document's own hairline stroke vanishes; borders are redrawn darker and
#: wider on top of the owner fills
PREVIEW_STROKE = ".provinces path { stroke: #2b2b2b; stroke-width: 2; stroke-linejoin: round; }"

_STYLE_ELEMENT = re.compile(r"<style\b[^>]*?(?:/>|>.*?</style\s*>)", re.S)
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.S)


def _xml_text(value):
    # `>` stays readable (CSS child combinator); only `]]>` requires escaping it
    return value.replace("&", "&amp;").replace("<", "&lt;").replace("]]>", "]]&gt;")


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def document_style(svg):
    """CSS text of the document's first <style> element, or None."""
    for element in ET.fromstring(svg).iter():  # noqa: S314 - stored by the loader from the variant folder
        if isinstance(element.tag, str) and _local(element.tag) == "style":
            return "".join(element.itertext()).strip() or None
    return None


def css_string(value):
    """Quote `value` as a CSS string (for attribute selectors)."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\a ")
    return f'"{escaped}"'


def owner_rule(province, color):
    selector = f"g[data-province={css_string(province)}] > path:not(.water)"
    return f"{selector} {{ fill: rgb({color['r']}, {color['g']}, {color['b']}); }}"


def preview_style(row):
    """The document's own rules, then one fill per province owned at start.

    Owner rules skip `.water` paths (water children such as
    `Denmark (strait)` keep the water fill) and outrank the `data-kind`
    fills by specificity.
    """
    base = document_style(row["svg"]) or DEFAULT_STYLE
    names, countries = row["names"], row["countries"]
    rules = [
        owner_rule(names[str(pid)], countries[country])
        for country, pids in row["init"]["territories"].items()
        for pid in pids
    ]
    return "\n".join([base, *rules, PREVIEW_STROKE])


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
