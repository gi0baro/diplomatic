import math
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter

import yaml


KINDS = ("sea", "coast", "inland", "neutral", "child")
PAINTED = ("neutral", "child")
LAND = ("coast", "inland")
WATER = ("sea", "coast")
UNITS = {"army": "armies", "fleet": "fleets"}
SVG_NS = "http://www.w3.org/2000/svg"
REMOVED = ("png", "position")
CODE = re.compile(r"[A-Z]{2,4}")
# The board ground (the darkest surface country colours are drawn on). Codes
# and labels are drawn in the owner's colour on it; the thresholds encode what
# was judged legible by eye on the approved design (docs/design), not a WCAG
# level: classic's Russia [138,95,181] sits at 4.2 and reads fine.
GROUND = (5, 8, 12)
MIN_CONTRAST = 4.0
# Euclidean RGB distance below which two countries are near-duplicates. RGB is
# not perceptual, so the threshold is deliberately loose and only catches clear
# collisions: classic's closest pair, Germany [160,138,117] vs Austria
# [196,143,133] (~40), was judged distinct on the design; England vs the old
# Russia [168,126,159] (~104) was the pair that looked too close for other
# reasons (same hue, differing only in lightness) and is not what this catches.
MIN_DISTANCE = 35


class VariantError(ValueError):
    pass


def load(path):
    with open(path) as f:
        doc = yaml.safe_load(f)
    _check_structure(doc)
    _check_references(doc)
    with open(os.path.join(os.path.dirname(path), "map.svg"), encoding="utf-8", newline="") as f:
        svg = f.read()
    _check_svg(doc, svg)
    row = _compile(doc)
    row["svg"] = svg
    return row


def _field(mapping, key, where, kind=None, optional=False):
    if key not in mapping:
        if optional:
            return None
        raise VariantError(f"{where}: missing '{key}'")
    value = mapping[key]
    if kind is not None and not isinstance(value, kind):
        raise VariantError(f"{where}: '{key}' must be a {kind.__name__}")
    return value


def _is_rgb(value):
    return isinstance(value, list) and len(value) == 3 and all(isinstance(v, int) and 0 <= v <= 255 for v in value)


def _channel(value):
    c = value / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    """WCAG relative luminance of an sRGB triple (0-255)."""
    r, g, b = (_channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG contrast ratio between two sRGB triples, from 1 to 21."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def distance(a, b):
    """Euclidean distance between two sRGB triples."""
    return math.dist(a, b)


def _check_names(values, where):
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise VariantError(f"{where}: must be a list of names")


def _check_links(links, where, army=True, fleet=True):
    for key in links:
        if key not in ("army", "fleet"):
            raise VariantError(f"{where}: unknown link type '{key}'")
        _check_names(links[key], f"{where}: {key} links")
    if not army and "army" in links:
        raise VariantError(f"{where}: cannot have army links")
    if not fleet and "fleet" in links:
        raise VariantError(f"{where}: cannot have fleet links")


def _check_province(province):
    where = _field(province, "name", "province", str)
    kind = _field(province, "kind", where, str)
    if kind not in KINDS:
        raise VariantError(f"{where}: unknown kind '{kind}'")
    _check_removed(province, where)
    if kind == "child":
        if "code" in province:
            raise VariantError(f"{where}: child provinces cannot have 'code'")
    elif not CODE.fullmatch(_field(province, "code", where, str)):
        raise VariantError(f"{where}: 'code' must be 2 to 4 uppercase letters")
    if kind in PAINTED:
        for key in ("supply_center", "coasts", "links"):
            if key in province:
                raise VariantError(f"{where}: {kind} provinces cannot have '{key}'")
        if not isinstance(province.get("water", False), bool):
            raise VariantError(f"{where}: 'water' must be a boolean")
        if kind == "child":
            _field(province, "parent", where, str)
        return
    if "water" in province:
        raise VariantError(f"{where}: only {' and '.join(PAINTED)} provinces take 'water'")
    center = _field(province, "supply_center", where, optional=True)
    if center is not None and not isinstance(center, bool):
        raise VariantError(f"{where}: 'supply_center' must be a boolean")
    if center and kind == "sea":
        raise VariantError(f"{where}: 'supply_center' needs a land province")
    coasts = _field(province, "coasts", where, list, optional=True)
    if coasts is not None:
        if kind != "coast" or len(coasts) < 2:
            raise VariantError(f"{where}: 'coasts' needs a coast province with at least two entries")
        for coast in coasts:
            cwhere = f"{where}/{_field(coast, 'name', where, str)}"
            _check_removed(coast, cwhere)
            _check_links(_field(coast, "links", cwhere, dict), cwhere, army=False)
    links = _field(province, "links", where, dict, optional=True) or {}
    _check_links(links, where, army=kind != "sea", fleet=kind != "inland" and coasts is None)


def _check_removed(mapping, where):
    for key in REMOVED:
        if key in mapping:
            raise VariantError(f"{where}: '{key}' is not supported, coordinates live in map.svg")


def _check_country(country):
    where = _field(country, "name", "country", str)
    if not _is_rgb(_field(country, "color", where)):
        raise VariantError(f"{where}: 'color' must be an RGB triple")
    ratio = contrast(country["color"], GROUND)
    if ratio < MIN_CONTRAST:
        raise VariantError(f"{where}: 'color' contrast against the ground is {ratio:.1f}, needs {MIN_CONTRAST}")
    _check_names(_field(country, "home_centers", where), f"{where}: home_centers")
    _check_names(_field(country, "provinces", where), f"{where}: provinces")
    units = _field(country, "units", where, dict)
    for unit, kind in units.items():
        if not isinstance(unit, str) or kind not in UNITS:
            raise VariantError(f"{where}: unit '{unit}' must be an army or a fleet")


def _check_structure(doc):
    where = _field(doc, "name", "variant", str)
    for key in ("revision", "year", "centers_to_win", "min_players"):
        if _field(doc, key, where, int) < 1:
            raise VariantError(f"{where}: '{key}' must be positive")
    codes = {}
    for province in _field(doc, "provinces", where, list):
        _check_province(province)
        code = province.get("code")
        if code in codes:
            raise VariantError(f"{province['name']}: code '{code}' already used by '{codes[code]}'")
        if code is not None:
            codes[code] = province["name"]
    countries = _field(doc, "countries", where, list)
    for i, country in enumerate(countries):
        _check_country(country)
        for other in countries[:i]:
            gap = distance(country["color"], other["color"])
            if gap < MIN_DISTANCE:
                raise VariantError(
                    f"{country['name']}: 'color' too close to {other['name']} (distance {gap:.1f}, needs {MIN_DISTANCE})"
                )


def _fleet_refs(province):
    if "coasts" in province:
        return [(f"{province['name']}/{coast['name']}", coast["links"]["fleet"]) for coast in province["coasts"]]
    return [(province["name"], province.get("links", {}).get("fleet", []))]


def _check_references(doc):
    provinces = {}
    for province in doc["provinces"]:
        if province["name"] in provinces:
            raise VariantError(f"{province['name']}: duplicate province")
        provinces[province["name"]] = province
    coasts = {p["name"]: [c["name"] for c in p.get("coasts", [])] for p in doc["provinces"]}
    fleet_links = {ref: targets for p in doc["provinces"] for ref, targets in _fleet_refs(p)}

    def resolve(text, where, with_coast=None):
        name, _, coast = text.partition("/")
        if name not in provinces:
            raise VariantError(f"{where}: unknown province '{name}'")
        if coast and coast not in coasts[name]:
            raise VariantError(f"{where}: unknown coast '{text}'")
        if with_coast is not None and bool(coast) != (with_coast and bool(coasts[name])):
            raise VariantError(f"{where}: '{text}' {'needs' if with_coast and coasts[name] else 'cannot take'} a coast")
        return provinces[name]

    for province in doc["provinces"]:
        where = province["name"]
        if province["kind"] == "child":
            parent = resolve(province["parent"], where, with_coast=False)
            if parent["kind"] in PAINTED:
                raise VariantError(f"{where}: parent '{province['parent']}' cannot have children")
        for target in province.get("links", {}).get("army", []):
            other = resolve(target, where, with_coast=False)
            if other["kind"] not in LAND:
                raise VariantError(f"{where} -> {target}: army link into a {other['kind']}")
            if where not in other["links"]["army"]:
                raise VariantError(f"{where} -> {target}: army link is one-way")
        for ref, targets in _fleet_refs(province):
            for target in targets:
                other = resolve(target, ref, with_coast=True)
                if other["kind"] not in WATER:
                    raise VariantError(f"{ref} -> {target}: fleet link into a {other['kind']}")
                if ref not in fleet_links[target]:
                    raise VariantError(f"{ref} -> {target}: fleet link is one-way")

    names = set()
    for country in doc["countries"]:
        where = country["name"]
        if where in names:
            raise VariantError(f"{where}: duplicate country")
        names.add(where)
        owned = country["provinces"]
        for target in owned:
            resolve(target, where, with_coast=False)
        for target in country["home_centers"]:
            if not resolve(target, where, with_coast=False).get("supply_center"):
                raise VariantError(f"{where}: home center '{target}' is not a supply center")
        for unit, kind in country["units"].items():
            province = resolve(unit, where, with_coast=kind == "fleet")
            if province["name"] not in owned:
                raise VariantError(f"{where}: unit on '{unit}' which it does not own")
            if province["kind"] != "coast" and (kind == "fleet" or province["kind"] != "inland"):
                raise VariantError(f"{where}: {kind} cannot start on '{unit}'")


def _svg(tag):
    return f"{{{SVG_NS}}}{tag}"


def _classes(element):
    return element.get("class", "").split()


def _is_number(value):
    try:
        float(value)
    except TypeError, ValueError:
        return False
    return True


def _svg_groups(root, provinces):
    groups = {}
    for group in root.iter(_svg("g")):
        name = group.get("data-province")
        if name is None:
            continue
        where = f"map.svg: group '{name}'"
        if name not in provinces or provinces[name]["kind"] == "child":
            raise VariantError(f"{where}: no such province in the variant")
        if name in groups:
            raise VariantError(f"{where}: duplicate group")
        if group.find(f".//{_svg('g')}[@data-province]") is not None:
            raise VariantError(f"{where}: province groups cannot be nested")
        groups[name] = group
    for name, province in provinces.items():
        if province["kind"] != "child" and name not in groups:
            raise VariantError(f"map.svg: missing group for province '{name}'")
    return groups


def _check_svg_children(root, provinces, groups):
    owners = {path: name for name, group in groups.items() for path in group.iter(_svg("path"))}
    seen = set()
    for path in root.iter(_svg("path")):
        name = path.get("data-child")
        if name is None:
            continue
        where = f"map.svg: child path '{name}'"
        if name not in provinces or provinces[name]["kind"] != "child":
            raise VariantError(f"{where}: no such child province in the variant")
        if name in seen:
            raise VariantError(f"{where}: duplicate path")
        seen.add(name)
        parent = provinces[name]["parent"]
        if owners.get(path) != parent:
            raise VariantError(f"{where}: must be inside the group of its parent '{parent}'")
        if ("water" in _classes(path)) != provinces[name].get("water", False):
            raise VariantError(f"{where}: class 'water' must match the variant's 'water'")
    for name, province in provinces.items():
        if province["kind"] == "child" and name not in seen:
            raise VariantError(f"map.svg: missing path for child province '{name}'")


def _check_svg_group(province, group):
    where = f"map.svg: group '{province['name']}'"
    kind = province["kind"]
    if group.get("data-kind") != kind:
        raise VariantError(f"{where}: data-kind must be '{kind}'")
    paths = [path for path in group.iter(_svg("path")) if path.get("data-child") is None]
    if not paths:
        raise VariantError(f"{where}: needs at least one path")
    for path in paths:
        if ("water" in _classes(path)) != province.get("water", False):
            raise VariantError(f"{where}: class 'water' on its paths must match the variant's 'water'")
    circles = list(group.iter(_svg("circle")))
    anchors = [c for c in circles if "anchor" in _classes(c)]
    centers = [c for c in circles if "center" in _classes(c)]
    for circle in anchors + centers:
        if not (_is_number(circle.get("cx")) and _is_number(circle.get("cy"))):
            raise VariantError(f"{where}: anchor and center circles need numeric 'cx' and 'cy'")
    if kind == "neutral":
        if anchors or centers:
            raise VariantError(f"{where}: neutral provinces have no anchors and no center")
        return
    defaults = [c for c in anchors if c.get("data-coast") is None]
    if len(defaults) != 1:
        raise VariantError(f"{where}: needs exactly one default anchor, found {len(defaults)}")
    found = Counter(c.get("data-coast") for c in anchors if c.get("data-coast") is not None)
    for coast in province.get("coasts", []):
        if found.pop(coast["name"], 0) != 1:
            raise VariantError(f"{where}: needs exactly one anchor for coast '{coast['name']}'")
    if found:
        raise VariantError(f"{where}: anchor for undeclared coast '{next(iter(found))}'")
    expected = 1 if province.get("supply_center") else 0
    if len(centers) != expected:
        raise VariantError(f"{where}: needs {expected} center marker(s), found {len(centers)}")


def _check_svg(doc, text):
    try:
        root = ET.fromstring(text)  # noqa: S314 - the document comes from the variant folder
    except ET.ParseError as e:
        raise VariantError(f"map.svg: {e}")
    if root.tag != _svg("svg"):
        raise VariantError(f"map.svg: root element must be an <svg> in the {SVG_NS} namespace")
    provinces = {p["name"]: p for p in doc["provinces"]}
    groups = _svg_groups(root, provinces)
    _check_svg_children(root, provinces, groups)
    for name, group in groups.items():
        _check_svg_group(provinces[name], group)


def _compile(doc):
    ids = {p["name"]: str(i) for i, p in enumerate(doc["provinces"])}
    coast_ids = {p["name"]: {c["name"]: i for i, c in enumerate(p.get("coasts", []))} for p in doc["provinces"]}

    def ref(text):
        name, _, coast = text.partition("/")
        return ids[name], coast_ids[name].get(coast)

    def unique(items):
        return list(dict.fromkeys(items))

    row = {
        "name": doc["name"],
        "revision": doc["revision"],
        "year": doc["year"],
        "scs_to_win": doc["centers_to_win"],
        "min_players": doc["min_players"],
        "names": {},
        "codes": {},
        "seas": [],
        "coasts": [],
        "neutrals": [],
        "supply_centers": [],
        "multi_coasts": [],
        "coast_names": {},
        "links": {"armies": {}, "fleets": {}, "multi_coasts": {}},
        "home_centers": {},
        "countries": {},
        "init": {"territories": {}, "troops": {}, "coasts": {}},
    }
    for province in doc["provinces"]:
        pid, kind = ids[province["name"]], province["kind"]
        row["names"][pid] = province["name"]
        if "code" in province:
            row["codes"][pid] = province["code"]
        if kind == "neutral":
            row["neutrals"].append(pid)
        if kind == "sea" or province.get("water"):
            row["seas"].append(pid)
        if kind in PAINTED:
            continue
        if kind == "coast":
            row["coasts"].append(pid)
        if province.get("supply_center"):
            row["supply_centers"].append(pid)
        links = province.get("links", {})
        if "army" in links:
            row["links"]["armies"][pid] = [ids[t] for t in links["army"]]
        if "fleet" in links:
            row["links"]["fleets"][pid] = unique(ref(t)[0] for t in links["fleet"])
        if "coasts" in province:
            row["multi_coasts"].append(pid)
            row["coast_names"][pid] = [c["name"] for c in province["coasts"]]
            row["links"]["multi_coasts"][pid] = [[ids[t] for t in c["links"]["fleet"]] for c in province["coasts"]]
            row["links"]["fleets"][pid] = unique(t for reach in row["links"]["multi_coasts"][pid] for t in reach)
    for country in doc["countries"]:
        name = country["name"]
        row["countries"][name] = {"r": country["color"][0], "g": country["color"][1], "b": country["color"][2]}
        row["home_centers"][name] = [ids[t] for t in country["home_centers"]]
        row["init"]["territories"][name] = [ids[t] for t in country["provinces"]]
        troops = row["init"]["troops"][name] = {"armies": [], "fleets": []}
        for unit, kind in country["units"].items():
            pid, coast = ref(unit)
            troops[UNITS[kind]].append(pid)
            if coast is not None:
                row["init"]["coasts"][pid] = coast
    return row
