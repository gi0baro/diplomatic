# -*- coding: utf-8 -*-

import yaml


KINDS = ("sea", "coast", "inland", "neutral", "child")
PAINTED = ("neutral", "child")
LAND = ("coast", "inland")
WATER = ("sea", "coast")
UNITS = {"army": "armies", "fleet": "fleets"}


class VariantError(ValueError):
    pass


def load(path):
    with open(path) as f:
        doc = yaml.safe_load(f)
    _check_structure(doc)
    _check_references(doc)
    return _compile(doc)


def _field(mapping, key, where, kind=None, optional=False):
    if key not in mapping:
        if optional:
            return None
        raise VariantError(f"{where}: missing '{key}'")
    value = mapping[key]
    if kind is not None and not isinstance(value, kind):
        raise VariantError(f"{where}: '{key}' must be a {kind.__name__}")
    return value


def _is_point(value):
    return isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) for v in value)


def _is_rgb(value):
    return isinstance(value, list) and len(value) == 3 and all(isinstance(v, int) and 0 <= v <= 255 for v in value)


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
    if not _is_rgb(_field(province, "png", where)):
        raise VariantError(f"{where}: 'png' must be an RGB triple")
    if kind in PAINTED:
        for key in ("position", "supply_center", "coasts", "links"):
            if key in province:
                raise VariantError(f"{where}: {kind} provinces cannot have '{key}'")
        if not isinstance(province.get("water", False), bool):
            raise VariantError(f"{where}: 'water' must be a boolean")
        if kind == "child":
            _field(province, "parent", where, str)
        return
    if "water" in province:
        raise VariantError(f"{where}: only {' and '.join(PAINTED)} provinces take 'water'")
    if not _is_point(_field(province, "position", where)):
        raise VariantError(f"{where}: 'position' must be a pair of coordinates")
    center = _field(province, "supply_center", where, optional=True)
    if center is not None and (kind == "sea" or not _is_point(center)):
        raise VariantError(f"{where}: 'supply_center' must be a pair of coordinates on a land province")
    coasts = _field(province, "coasts", where, list, optional=True)
    if coasts is not None:
        if kind != "coast" or len(coasts) < 2:
            raise VariantError(f"{where}: 'coasts' needs a coast province with at least two entries")
        for coast in coasts:
            cwhere = f"{where}/{_field(coast, 'name', where, str)}"
            if not _is_point(_field(coast, "position", cwhere)):
                raise VariantError(f"{cwhere}: 'position' must be a pair of coordinates")
            _check_links(_field(coast, "links", cwhere, dict), cwhere, army=False)
    links = _field(province, "links", where, dict, optional=True) or {}
    _check_links(links, where, army=kind != "sea", fleet=kind != "inland" and coasts is None)


def _check_country(country):
    where = _field(country, "name", "country", str)
    if not _is_rgb(_field(country, "color", where)):
        raise VariantError(f"{where}: 'color' must be an RGB triple")
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
    for province in _field(doc, "provinces", where, list):
        _check_province(province)
    for country in _field(doc, "countries", where, list):
        _check_country(country)


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
            if "supply_center" not in resolve(target, where, with_coast=False):
                raise VariantError(f"{where}: home center '{target}' is not a supply center")
        for unit, kind in country["units"].items():
            province = resolve(unit, where, with_coast=kind == "fleet")
            if province["name"] not in owned:
                raise VariantError(f"{where}: unit on '{unit}' which it does not own")
            if province["kind"] != "coast" and (kind == "fleet" or province["kind"] != "inland"):
                raise VariantError(f"{where}: {kind} cannot start on '{unit}'")


def _compile(doc):
    ids = {p["name"]: str(i) for i, p in enumerate(doc["provinces"])}
    coast_ids = {p["name"]: {c["name"]: i for i, c in enumerate(p.get("coasts", []))} for p in doc["provinces"]}

    def ref(text):
        name, _, coast = text.partition("/")
        return ids[name], coast_ids[name].get(coast)

    def point(value):
        return {"x": value[0], "y": value[1]}

    def unique(items):
        return list(dict.fromkeys(items))

    row = {
        "name": doc["name"],
        "revision": doc["revision"],
        "year": doc["year"],
        "scs_to_win": doc["centers_to_win"],
        "min_players": doc["min_players"],
        "names": {},
        "seas": [],
        "coasts": [],
        "neutrals": [],
        "supply_centers": {},
        "oxy": {},
        "multi_coasts": {},
        "colors": {},
        "same": {},
        "links": {"armies": {}, "fleets": {}, "multi_coasts": {}},
        "home_centers": {},
        "countries": {},
        "init": {"territories": {}, "troops": {}, "coasts": {}},
    }
    for province in doc["provinces"]:
        pid, kind = ids[province["name"]], province["kind"]
        row["names"][pid] = province["name"]
        row["colors"][pid] = province["png"]
        if kind == "neutral":
            row["neutrals"].append(pid)
        if kind == "child":
            row["same"][pid] = ids[province["parent"]]
        if kind == "sea" or province.get("water"):
            row["seas"].append(pid)
        if kind in PAINTED:
            continue
        if kind == "coast":
            row["coasts"].append(pid)
        row["oxy"][pid] = point(province["position"])
        if "supply_center" in province:
            row["supply_centers"][pid] = point(province["supply_center"])
        links = province.get("links", {})
        if "army" in links:
            row["links"]["armies"][pid] = [ids[t] for t in links["army"]]
        if "fleet" in links:
            row["links"]["fleets"][pid] = unique(ref(t)[0] for t in links["fleet"])
        if "coasts" in province:
            row["multi_coasts"][pid] = [point(c["position"]) for c in province["coasts"]]
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
