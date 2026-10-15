"""Trace a variant's PNG label map into an SVG draft with shared edges.

Local dev tool, never run by the system. Inputs, all in the variant folder:

- ``<folder name>.yaml``: the variant (provinces, kinds, coasts, supply
  centres). It carries no coordinates and no colours. Other YAML files in the
  folder are ignored, except the sidecar.
- ``trace.yaml``: the sidecar, what reading the PNG needs and the variant
  does not carry (colours, hand-placed points), merged into the variant's
  provinces by name.
- ``map.png``: a flat-colour label map. Provinces are flat colours separated
  by 1 px border lines ([4, 2, 4]) or wider pure black ones; any other colour
  matching no province (and not the void) is treated as border too.

Sidecar format::

    void: [253, 253, 253]        # optional: background colour outside the map
    provinces:
      Warsaw:
        position: [664, 539]     # the anchor; required for sea, coast, inland
        center: [691, 534]       # optional, supply centres only
      St. Petersburg:
        position: [985, 192]
        png: [0, 200, 0]         # optional: default is the PNG colour at position
        coasts: {North: [843, 102], South: [764, 335]}  # one per YAML coast
      Crete:
        png: [240, 30, 255]      # required for neutral and child (no anchor)

Every YAML province needs an entry. Unknown provinces or keys, missing or
extra coasts, a ``center`` on a province that is not a supply centre, points
outside the image, and a colour that is a border colour or the void colour
(e.g. a sampled position sitting on a line) are errors: nothing is written.
A neutral or child may carry a ``position`` too; it is only a seed for the
shared-colour rule and is not emitted.

The geometry is built TopoJSON-style so neighbours share their edges:

1. Label image: every pixel gets a province.
   - A colour claimed by one province: all its pixels are that province.
   - A colour claimed by several (webDiplomacy seas share one colour): its
     mask is split into 4-connected components and each claimant takes the
     component holding its ``position`` (its seed). Components with no seed
     (islets) are left to the border rule below. Two seeds in one component
     (a missing border line) or a seed off its colour are anomalies.
   - The ``void`` colour is background, not map: labelled like the image
     outside (no path, empty in the SVG) and left out of the fidelity
     measurement.
   - Border pixels (and any colour matching no province) go to the nearest
     province pixel by iterative 4-neighbour dilation, ties broken by
     neighbour order up, left, down, right. The void does not grow, so an
     outline between the void and the map goes to the provinces and their
     edge lands where the void begins; border pixels no province reaches
     (enclosed by the void) become void.
2. Shared arcs: exact pixel-edge loops are traced per label; pixel corners
   where 3+ labels meet (the image outside and the void count as one) or
   where two labels touch diagonally (saddles) are nodes. Loops are cut at
   nodes into arcs; the two sides of a border trace the same unit edges in
   opposite directions, so each arc is stored once (canonical direction) and
   every province loop is a sequence of (arc, direction). A loop with no node
   is one closed arc. Arcs against the image edge or the void have one side.
3. Each arc is simplified once with OpenCV approxPolyDP (endpoints kept) and
   province loops are rebuilt from the simplified arcs, so both sides of every
   border have identical coordinates. By default arcs are emitted as quadratic
   B-splines through the simplified vertices (nodes stay exact); one-sided
   arcs (image edge, void) stay straight polylines.

``map.svg`` follows the SVG contract in docs/board-redesign.md: one group per
province with one ``fill-rule="evenodd"`` path holding all its loops (children
as ``class="water"`` paths inside the parent group), the anchors from the
sidecar (``position``, one per coast) and a ``center`` marker for supply
centres. Borders are drawn by stroking the province paths themselves: shared
edges coincide exactly, so the two strokes of a border overlap.

A supply centre without an explicit ``center`` gets a computed one: among the
province's label pixels between R and 2R from its anchor (``--center-offset
R``), the one deepest inside the province (distance transform), ties to the
one closest to the anchor. A province too small for that ring gets its pixel
farthest from the anchor and an anomaly asking for an explicit ``center``.
Also writes ``report.txt`` (fidelity per province) and ``preview.html``
(PNG under the inlined SVG, for eyeballing).

Fidelity is measured on the SVG as rendered: a measurement-only copy of the
document (same province paths, each filled with a unique index colour, no
stroke) is rasterised with cairosvg at the PNG size and each province's
rendered mask is compared with its mask in the label image.

Usage:
    uv run --with opencv-python-headless,numpy,pyyaml,cairosvg \
        python tools/png_to_svg.py variants/classic [--epsilon 1.0] [--min-area 0] [--no-smoothing] \
        [--center-offset 24]
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import cairosvg
import cv2
import numpy as np
import yaml


MANY_SHAPES = 3
IOU_THRESHOLD = 0.98
# Border line colours, absorbed into provinces and refused as a sampled province colour:
# classic's [4, 2, 4] and black, webDiplomacy's AncMed [3, 3, 3] and ColdWar [0, 2, 0].
BORDER_COLOURS = {(4, 2, 4), (0, 0, 0), (3, 3, 3), (0, 2, 0)}
GROWTH_WARN = 0.25  # flag provinces that absorbed more than this fraction of their own pixels
ANCHORED = ("sea", "coast", "inland")  # kinds with anchors in the SVG
TRACE_KEYS = ("png", "position", "center", "coasts")  # per-province keys of trace.yaml
VOID = -2  # void pixels while assigning labels; they end up -1, like the image outside

STYLE = """
g[data-kind="sea"] path { fill: #a9cbe0; }
g[data-kind="coast"] path, g[data-kind="inland"] path { fill: #e9dfbd; }
g[data-kind="neutral"] path { fill: #cfc8b0; }
.provinces path.water { fill: #a9cbe0; }
""".strip("\n")
STROKE_STYLE = ".provinces path { stroke: #6b6b6b; stroke-width: 0.6; stroke-linejoin: round; }"


# --------------------------------------------------------------------------
# 0. inputs: the variant YAML and its trace.yaml sidecar


class SidecarError(ValueError):
    """trace.yaml does not match the variant; the message lists every problem found."""


def is_rgb(value: object) -> bool:
    return isinstance(value, list) and len(value) == 3 and all(type(c) is int and 0 <= c <= 255 for c in value)


def is_point(value: object, width: int, height: int) -> bool:
    """[x, y] inside the image (numbers, booleans excluded)."""
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
        and 0 <= value[0] < width
        and 0 <= value[1] < height
    )


def pixel(point: list) -> tuple[int, int]:
    """(x, y) of the pixel holding a point: pixel (x, y) is the square [x, x+1] x [y, y+1]."""
    return int(point[0]), int(point[1])


def merge_entry(p: dict, entry: object, img: np.ndarray, void: tuple | None) -> list[str]:
    """Merge one trace.yaml entry into its (copied) province dict; returns the problems found."""
    where = f"trace.yaml: {p['name']}"
    if entry is None:
        return [f"{where}: missing (every province of the variant needs an entry)"]
    if not isinstance(entry, dict):
        return [f"{where}: must be a mapping"]
    height, width = img.shape[:2]
    bad_point = f"must be [x, y] inside the {width}x{height} image"
    errors = [f"{where}: unknown key '{key}'" for key in entry if key not in TRACE_KEYS]
    anchored = p["kind"] in ANCHORED
    if "position" in entry:
        if is_point(entry["position"], width, height):
            p["position"] = entry["position"]
        else:
            errors.append(f"{where}: 'position' {bad_point}")
    elif anchored:
        errors.append(f"{where}: 'position' is required for kind {p['kind']}")
    sampled = False
    if "png" in entry:
        if is_rgb(entry["png"]):
            p["png"] = entry["png"]
        else:
            errors.append(f"{where}: 'png' must be an RGB triple")
    elif not anchored:
        errors.append(f"{where}: 'png' is required for kind {p['kind']} (no anchor to sample it at)")
    elif "position" in p:
        x, y = pixel(p["position"])
        p["png"] = [int(c) for c in img[y, x]]
        sampled = True
    colour = tuple(p.get("png", ()))
    if colour in BORDER_COLOURS or colour == void:
        what = "a border colour" if colour in BORDER_COLOURS else "the void colour"
        how = f", sampled at position {p['position']}: move it off the line or set png" if sampled else ""
        errors.append(f"{where}: png {list(colour)} is {what}{how}")
    if "center" in entry:
        if not (anchored and p.get("supply_center")):
            errors.append(f"{where}: 'center' on a province that is not a supply centre")
        elif is_point(entry["center"], width, height):
            p["center"] = entry["center"]
        else:
            errors.append(f"{where}: 'center' {bad_point}")
    given = entry.get("coasts") or {}
    if not isinstance(given, dict):
        errors.append(f"{where}: 'coasts' must map coast names to [x, y]")
        given = {}
    declared = [c["name"] for c in p.get("coasts") or []]
    errors += [f"{where}: coast '{name}' is not declared in the variant" for name in given if name not in declared]
    for coast in p.get("coasts") or []:
        if coast["name"] not in given:
            errors.append(f"{where}: missing coast '{coast['name']}'")
        elif is_point(given[coast["name"]], width, height):
            coast["position"] = given[coast["name"]]
        else:
            errors.append(f"{where}: coast '{coast['name']}' {bad_point}")
    return errors


def merge_trace(provinces: list[dict], trace: object, img: np.ndarray) -> tuple[list[dict], tuple | None]:
    """The variant's provinces with trace.yaml merged in by name, and the void colour.

    The merged keys are the ones the rest of the tool reads: ``png``,
    ``position``, ``center`` and each coast's ``position``; the variant's own
    dicts are left untouched. Raises SidecarError listing every problem.
    """
    if not isinstance(trace, dict) or not isinstance(trace.get("provinces"), dict):
        raise SidecarError("trace.yaml: needs a 'provinces' mapping")
    errors = [f"trace.yaml: unknown key '{key}'" for key in trace if key not in ("void", "provinces")]
    void = trace.get("void")
    if void is not None:
        if not is_rgb(void):
            errors.append("trace.yaml: 'void' must be an RGB triple")
            void = None
        else:
            void = tuple(void)
            if void in BORDER_COLOURS:
                errors.append(f"trace.yaml: void {list(void)} is a border colour")
    entries = trace["provinces"]
    known = {p["name"] for p in provinces}
    errors += [f"trace.yaml: unknown province '{name}'" for name in entries if name not in known]
    merged = []
    for p in provinces:
        q = {**p, "coasts": [dict(c) for c in p["coasts"]]} if "coasts" in p else dict(p)
        errors += merge_entry(q, entries.get(p["name"]), img, void)
        merged.append(q)
    if errors:
        raise SidecarError("\n".join(errors))
    return merged, void


# --------------------------------------------------------------------------
# 1. label image


@dataclass
class SharedColour:
    colour: tuple[int, int, int]
    owners: list[str]  # provinces claiming it, in YAML order
    components: int  # 4-connected components of the colour
    unseeded: int  # ... holding no seed, left to the border rule
    unseeded_px: int


@dataclass
class LabelInfo:
    raw: np.ndarray  # province index per pixel from the PNG colours (and seeds), -1 elsewhere
    labels: np.ndarray  # every map pixel assigned (the partition); -1 on the void
    black: np.ndarray  # pure black pixels in the PNG
    assigned: int  # pixels that had no province label, assigned to one
    assigned_thin: int  # ... of which [4, 2, 4]
    assigned_black: int  # ... of which [0, 0, 0]
    ties: int  # pixels whose 4-neighbour candidates disagreed
    rounds: int  # dilation rounds
    dropped: dict[str, int]  # pixels relabelled by --min-area, per province
    own: list[int]  # pixels of each province before --min-area: its colour, or its seeded component
    void: np.ndarray  # void pixels: the void colour plus border pixels enclosed by it
    void_colour: int  # pixels of the void colour
    shared: list[SharedColour]
    anomalies: list[str]  # from the seed rule


def province_masks(img: np.ndarray, provinces: list[dict]) -> tuple[list[np.ndarray], list[SharedColour], list[str]]:
    """Each province's own pixels, before borders: its colour, or the seeded component of a shared one.

    A colour claimed by several provinces cannot say which pixel is whose, so
    it is split into 4-connected components (border lines are what separates
    them) and each claimant takes the component under its ``position``.
    Unseeded components get no label here and are absorbed by their
    neighbours like border pixels. Returns the masks, the shared colours and
    the seed anomalies.
    """
    claims: dict[tuple[int, int, int], list[int]] = {}
    for i, p in enumerate(provinces):
        claims.setdefault(tuple(int(c) for c in p["png"]), []).append(i)
    masks: list[np.ndarray] = [np.zeros(img.shape[:2], bool)] * len(provinces)  # replaced, never mutated
    shared: list[SharedColour] = []
    anomalies: list[str] = []
    for colour, owners in claims.items():
        mask = np.all(img == colour, axis=-1)
        if len(owners) == 1:
            masks[owners[0]] = mask
            continue
        n, comp = cv2.connectedComponents(mask.astype(np.uint8), connectivity=4)
        seeded: dict[int, str] = {}  # component -> province
        for i in owners:
            p = provinces[i]
            if "position" not in p:
                anomalies.append(f"{p['name']}: shares png colour {list(colour)} but has no position to seed it")
                continue
            x, y = pixel(p["position"])
            c = int(comp[y, x])
            if not c:
                anomalies.append(
                    f"{p['name']}: seed {p['position']} is in no component of its colour {list(colour)} "
                    "(position on a line, or wrong colour)"
                )
            elif c in seeded:
                anomalies.append(
                    f"shared colour {list(colour)}: {seeded[c]} and {p['name']} in the same component "
                    f"(missing border line?); {p['name']} gets no pixels"
                )
            else:
                seeded[c] = p["name"]
                masks[i] = comp == c
        sizes = np.bincount(comp.ravel(), minlength=n)
        free = [c for c in range(1, n) if c not in seeded]
        names = [provinces[i]["name"] for i in owners]
        shared.append(SharedColour(colour, names, n - 1, len(free), int(sizes[free].sum())))
    return masks, shared, anomalies


def assign_labels(img: np.ndarray, provinces: list[dict], min_area: int, void: tuple | None = None) -> LabelInfo:
    """Partition the image: province pixels keep their index, the rest go to the nearest one.

    Province pixels come from ``province_masks`` (colour, or seeded component
    of a shared colour). Iterative 4-neighbour dilation (city-block
    distance). In each round every unassigned pixel with an assigned
    4-neighbour takes it; if several are assigned, the first in the order up,
    left, down, right wins. A 1 px border thus always goes to the province
    above or to the left of it, i.e. shared edges sit consistently on the
    bottom/right side of the border lines. ``min_area`` relabels 4-connected
    components below that many pixels as unassigned first, so their
    neighbours absorb them.

    The ``void`` colour never grows: an outline between the void and the map
    is absorbed by the provinces alone, so their edge lands on the void.
    Pixels no province can reach (cut off by the void) become void. Void
    pixels end up -1, the label of the image outside.
    """
    h, w = img.shape[:2]
    masks, shared, anomalies = province_masks(img, provinces)
    raw = np.full((h, w), -1, np.int32)
    dropped: dict[str, int] = {}
    own: list[int] = []
    for i, (p, mask) in enumerate(zip(provinces, masks)):
        own.append(int(np.count_nonzero(mask)))
        if min_area > 0 and own[-1]:
            n, comp, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=4)
            small = np.flatnonzero(stats[:, cv2.CC_STAT_AREA] < min_area)
            small = small[small != 0]
            if len(small):
                gone = np.isin(comp, small)
                dropped[p["name"]] = int(np.count_nonzero(gone))
                mask = mask & ~gone
        raw[mask] = i
    black = np.all(img == 0, axis=-1)
    thin = np.all(img == (4, 2, 4), axis=-1)
    void_colour = np.all(img == void, axis=-1) if void is not None else np.zeros((h, w), bool)
    lab = raw.copy()
    lab[void_colour] = VOID
    ties = rounds = 0
    big = np.iinfo(np.int32).max
    while True:
        todo = lab == -1
        if not todo.any():
            break
        pad = np.pad(lab, 1, constant_values=-1)
        cands = np.stack([pad[:-2, 1:-1], pad[1:-1, :-2], pad[2:, 1:-1], pad[1:-1, 2:]])
        valid = cands >= 0
        new = np.full_like(lab, -1)
        for c in cands:  # priority: up, left, down, right
            new = np.where((new < 0) & (c >= 0), c, new)
        lo = np.where(valid, cands, big).min(axis=0)
        hi = np.where(valid, cands, -1).max(axis=0)
        ties += int(np.count_nonzero(todo & valid.any(axis=0) & (lo != hi)))
        upd = todo & (new >= 0)
        if not upd.any():
            if not void_colour.any() or not (raw >= 0).any():
                raise RuntimeError("label assignment: no province pixel to grow from")
            lab[todo] = VOID  # cut off from every province by the void (e.g. a legend outside the map)
            break
        lab[upd] = new[upd]
        rounds += 1
    voided = lab == VOID
    lab[voided] = -1
    gained = (raw < 0) & ~voided
    return LabelInfo(
        raw=raw,
        labels=lab,
        black=black,
        assigned=int(np.count_nonzero(gained)),
        assigned_thin=int(np.count_nonzero(gained & thin)),
        assigned_black=int(np.count_nonzero(gained & black)),
        ties=ties,
        rounds=rounds,
        dropped=dropped,
        own=own,
        void=voided,
        void_colour=int(np.count_nonzero(void_colour)),
        shared=shared,
        anomalies=anomalies,
    )


# --------------------------------------------------------------------------
# 2. pixel-edge loops and shared arcs


def edge_loops(mask: np.ndarray, corners_only: bool = True) -> list[np.ndarray]:
    """Closed loops of unit pixel edges between inside and outside pixels of ``mask``.

    Pixel (row y, column x) is the square [x, x+1] x [y, y+1], so every loop
    vertex is an integer pixel corner. Edges are oriented with the inside on
    the RIGHT when walking them in image coordinates (x right, y down), i.e.
    clockwise on screen: outer loops have a positive shoelace area, holes a
    negative one. Pixels outside the image count as outside (mask is padded).

    Chaining: every vertex has as many incoming as outgoing edges, 1 or 2.
    Two only happens at a saddle, where the inside pixels touch diagonally
    (inside at top-left and bottom-right, or the mirror). There we always take
    the RIGHT turn, i.e. turn towards the inside pixel the incoming edge
    borders, so each loop hugs its own pixel's corner: 4-connected inside
    regions stay one loop and diagonal-only contacts become separate loops
    (the inside is 4-connected, the outside 8-connected). Since every
    province is traced with the same rule, a loop never crosses itself; it
    can still touch itself at a saddle, which evenodd fills correctly.

    With ``corners_only`` the loops hold only the corners (collinear vertices
    dropped); otherwise every unit vertex, in walking order.
    """
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return []
    oy, ox = int(ys.min()), int(xs.min())
    crop = mask[oy : ys.max() + 1, ox : xs.max() + 1].astype(bool)
    m = np.pad(crop, 1)
    inside = m[1:-1, 1:-1]
    stride = crop.shape[1] + 1  # vertex id = y * stride + x (crop coordinates)
    # (outside neighbour, start corner offset, direction) per side, inside on the right
    sides = [
        (m[:-2, 1:-1], (0, 0), (1, 0)),  # top: walk east
        (m[1:-1, 2:], (1, 0), (0, 1)),  # right: walk south
        (m[2:, 1:-1], (1, 1), (-1, 0)),  # bottom: walk west
        (m[1:-1, :-2], (0, 1), (0, -1)),  # left: walk north
    ]
    sx, sy, dx, dy = [], [], [], []
    for neighbour, (ax, ay), (ddx, ddy) in sides:
        r, c = np.nonzero(inside & ~neighbour)
        sx.append(c + ax)
        sy.append(r + ay)
        dx.append(np.full(len(r), ddx))
        dy.append(np.full(len(r), ddy))
    sx, sy, dx, dy = (np.concatenate(a).astype(np.int64) for a in (sx, sy, dx, dy))
    start = sy * stride + sx
    end = (sy + dy) * stride + (sx + dx)

    # next edge: the outgoing edge at our end vertex; at a saddle (two outgoing),
    # the one whose direction is the right turn of ours: (dx, dy) -> (-dy, dx)
    order = np.argsort(start, kind="stable")
    sorted_start = start[order]
    first = np.searchsorted(sorted_start, end, "left")
    count = np.searchsorted(sorted_start, end, "right") - first
    if np.any((count < 1) | (count > 2)):
        raise RuntimeError("edge chaining: vertex with 0 or >2 outgoing edges")
    cand = order[first]
    second = order[np.minimum(first + 1, len(order) - 1)]
    right_turn = (dx[cand] == -dy) & (dy[cand] == dx)
    nxt = np.where((count == 2) & ~right_turn, second, cand)
    if np.any((count == 2) & ~((dx[nxt] == -dy) & (dy[nxt] == dx))):
        raise RuntimeError("edge chaining: saddle without a right turn")

    loops: list[np.ndarray] = []
    seen = np.zeros(len(start), bool)
    nxt_list = nxt.tolist()
    for e0 in order.tolist():  # deterministic: loops start at their lowest vertex id
        if seen[e0]:
            continue
        chain = []
        e = e0
        while not seen[e]:
            seen[e] = True
            chain.append(e)
            e = nxt_list[e]
        if e != e0:
            raise RuntimeError("edge chaining: loop did not close on its first edge")
        idx = np.array(chain)
        if corners_only:
            turn = (dx[idx] != np.roll(dx[idx], 1)) | (dy[idx] != np.roll(dy[idx], 1))
            idx = idx[turn]  # edges starting with a change of direction
        loops.append(np.stack([sx[idx] + ox, sy[idx] + oy], axis=1))
    return loops


def signed_area(loop: np.ndarray) -> float:
    """Shoelace area in image coordinates: > 0 for outers, < 0 for holes."""
    x, y = loop[:, 0].astype(np.int64), loop[:, 1].astype(np.int64)
    return float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) / 2


@dataclass
class Arc:
    points: np.ndarray  # (n, 2) unit pixel-corner vertices in canonical direction
    closed: bool  # node-less ring (points hold no repeated closing vertex)
    sides: list[tuple[int, int]] = field(default_factory=list)  # (label, direction +1/-1)
    exact: bool = False  # simplification reverted to the exact trace
    simple: np.ndarray | None = None  # simplified vertices, canonical direction
    frame: bool = False  # one-sided, along the image frame (one-sided and not frame: along the void)

    @property
    def internal(self) -> bool:  # between two provinces (not against the image edge or the void)
        return len(self.sides) == 2


@dataclass
class Topology:
    arcs: list[Arc]
    loops: dict[int, list[list[tuple[int, int]]]]  # label -> loops as (arc id, direction)
    outers: dict[int, int]  # label -> loops with positive exact area
    nodes: np.ndarray  # (k, 2) node vertices (x, y)
    degree: Counter  # node degree -> count
    saddles: int  # 2-label diagonal nodes
    border_nodes: int  # nodes on the image edge


def node_grid(labels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per pixel corner (H+1, W+1): is it a node, its boundary degree, is it a 2-label saddle."""
    pad = np.pad(labels, 1, constant_values=-1)
    tl, tr, bl, br = pad[:-1, :-1], pad[:-1, 1:], pad[1:, :-1], pad[1:, 1:]
    distinct = 1 + (tr != tl) + ((bl != tl) & (bl != tr)) + ((br != tl) & (br != tr) & (br != bl))
    saddle = (distinct == 2) & (tl == br) & (tr == bl) & (tl != tr)
    degree = (tl != tr).astype(np.int8) + (tr != br) + (bl != br) + (tl != bl)
    return (distinct >= 3) | saddle, degree, saddle


def canonical_open(ids: list[int]) -> tuple[tuple[int, ...], int]:
    fwd, rev = tuple(ids), tuple(reversed(ids))
    return (fwd, 1) if fwd <= rev else (rev, -1)


def rotate_min(ids: list[int]) -> tuple[int, ...]:
    k = ids.index(min(ids))
    return tuple(ids[k:] + ids[:k])


def canonical_ring(ids: list[int]) -> tuple[tuple[int, ...], int]:
    fwd, rev = rotate_min(ids), rotate_min(ids[::-1])
    return (fwd, 1) if fwd <= rev else (rev, -1)


def build_topology(labels: np.ndarray, count: int, void: np.ndarray | None = None) -> Topology:
    """Cut every label's exact loops at nodes into shared arcs.

    ``void`` pixels are labelled -1 like the image outside, so arcs against
    them are one-sided, like arcs against the image edge (and handled the
    same way downstream); the mask only makes them legal here.
    """
    h, w = labels.shape
    stride = w + 1
    has_void = void is not None and bool(void.any())
    is_node, degree, saddle = node_grid(labels)
    arcs: list[Arc] = []
    index: dict[tuple, int] = {}
    loops: dict[int, list[list[tuple[int, int]]]] = {}
    outers: dict[int, int] = {}

    def arc_id(key: tuple, closed: bool) -> int:
        if key not in index:
            pts = np.array([(v % stride, v // stride) for v in key], np.int64)
            index[key] = len(arcs)
            arcs.append(Arc(pts, closed))
        return index[key]

    for label in range(count):
        mask = labels == label
        if not mask.any():
            continue
        loops[label], outers[label] = [], 0
        for loop in edge_loops(mask, corners_only=False):
            if signed_area(loop) > 0:
                outers[label] += 1
            ids = (loop[:, 1] * stride + loop[:, 0]).tolist()
            flags = is_node[loop[:, 1], loop[:, 0]]
            seq: list[tuple[int, int]] = []
            if not flags.any():
                key, direction = canonical_ring(ids)
                seq.append((arc_id(key, True), direction))
            else:
                cut = np.flatnonzero(flags).tolist()
                k0 = cut[0]
                ids = ids[k0:] + ids[:k0]
                cut = [c - k0 for c in cut] + [len(ids)]
                ids.append(ids[0])
                for a, b in zip(cut, cut[1:]):
                    key, direction = canonical_open(ids[a : b + 1])
                    seq.append((arc_id(key, False), direction))
            for aid, direction in seq:
                arcs[aid].sides.append((label, direction))
            loops[label].append(seq)

    for i, arc in enumerate(arcs):
        dirs = sorted(d for _, d in arc.sides)
        if len(arc.sides) == 2 and dirs != [-1, 1]:
            raise RuntimeError(f"arc {i}: both sides walk it the same way")
        if len(arc.sides) == 1:
            x, y = arc.points[:, 0], arc.points[:, 1]
            on_edge = (x == 0) | (x == w) | (y == 0) | (y == h)
            arc.frame = bool(on_edge.all())
            if not arc.frame and not has_void:
                raise RuntimeError(f"arc {i}: one-sided but not on the image edge")
        if len(arc.sides) not in (1, 2):
            raise RuntimeError(f"arc {i}: {len(arc.sides)} sides")

    ny, nx = np.nonzero(is_node)
    on_edge = (nx == 0) | (nx == w) | (ny == 0) | (ny == h)
    return Topology(
        arcs=arcs,
        loops=loops,
        outers=outers,
        nodes=np.stack([nx, ny], axis=1),
        degree=Counter(degree[is_node].tolist()),
        saddles=int(np.count_nonzero(saddle)),
        border_nodes=int(np.count_nonzero(on_edge)),
    )


# --------------------------------------------------------------------------
# 3. simplification and reassembly


def drop_collinear(pts: np.ndarray, closed: bool) -> np.ndarray:
    if closed:
        d_in = pts - np.roll(pts, 1, axis=0)
        d_out = np.roll(pts, -1, axis=0) - pts
        return pts[np.any(d_in != d_out, axis=1)]
    if len(pts) <= 2:
        return pts
    d_in = pts[1:-1] - pts[:-2]
    d_out = pts[2:] - pts[1:-1]
    keep = np.concatenate([[True], np.any(d_in != d_out, axis=1), [True]])
    return pts[keep]


def dp(pts: np.ndarray, epsilon: float, closed: bool) -> np.ndarray:
    return cv2.approxPolyDP(pts.reshape(-1, 1, 2).astype(np.int32), epsilon, closed).reshape(-1, 2)


def simplify_arc(arc: Arc, epsilon: float) -> np.ndarray:
    """Simplified arc vertices (canonical direction); endpoints of open arcs kept.

    Open arcs: approxPolyDP on the open polyline. An open arc starting and
    ending at the same node is split at its farthest vertex first (DP cannot
    measure distances to a zero-length chord). Closed node-less arcs:
    approxPolyDP closed. Anything left with fewer than 3 distinct vertices or
    no area (rings), or fewer than 2 vertices (open), falls back to the exact
    trace (collinear vertices dropped).
    """
    pts = arc.points.astype(np.int64)
    exact = drop_collinear(pts, arc.closed)
    if epsilon <= 0 or arc.exact:
        return exact
    if arc.closed:
        out = dp(pts, epsilon, True).astype(np.int64)
        if len(np.unique(out, axis=0)) < 3 or signed_area(out) == 0:
            arc.exact = True
            return exact
        return out
    if len(pts) <= 2:
        return pts
    if (pts[0] == pts[-1]).all():
        far = int(np.argmax(((pts - pts[0]) ** 2).sum(axis=1)))
        out = np.vstack([dp(pts[: far + 1], epsilon, False), dp(pts[far:], epsilon, False)[1:]])
        out = out.astype(np.int64)
        if len(np.unique(out, axis=0)) < 3 or signed_area(out[:-1]) == 0:
            arc.exact = True
            return exact
    else:
        out = dp(pts, epsilon, False).astype(np.int64)
    if len(out) < 2 or (out[0] != pts[0]).any() or (out[-1] != pts[-1]).any():
        arc.exact = True
        return exact
    return out


def oriented(arc: Arc, direction: int) -> np.ndarray:
    assert arc.simple is not None
    return arc.simple if direction > 0 else arc.simple[::-1]


def assemble(seq: list[tuple[int, int]], arcs: list[Arc]) -> np.ndarray:
    """A province loop's vertices from its simplified arcs (no repeated closing vertex)."""
    if len(seq) == 1 and arcs[seq[0][0]].closed:
        return oriented(arcs[seq[0][0]], seq[0][1])
    return np.vstack([oriented(arcs[aid], d)[:-1] for aid, d in seq])


def loop_exact_area(seq: list[tuple[int, int]], arcs: list[Arc]) -> float:
    if len(seq) == 1 and arcs[seq[0][0]].closed:
        arc, d = arcs[seq[0][0]], seq[0][1]
        return signed_area(arc.points if d > 0 else arc.points[::-1])
    parts = [(arcs[a].points if d > 0 else arcs[a].points[::-1])[:-1] for a, d in seq]
    return signed_area(np.vstack(parts))


def simplify_all(topo: Topology, epsilon: float) -> int:
    """Simplify every arc once and guard the rebuilt loops; returns arcs reverted to exact.

    A rebuilt loop with fewer than 3 distinct vertices, no area or flipped
    orientation (e.g. an island of two arcs that both straighten to the same
    chord) gets all its arcs reverted to the exact trace, on both sides.
    """
    for arc in topo.arcs:
        arc.simple = simplify_arc(arc, epsilon)
    for _ in range(10):
        bad: set[int] = set()
        for seqs in topo.loops.values():
            for seq in seqs:
                pts = assemble(seq, topo.arcs)
                area = signed_area(pts)
                if (
                    len(np.unique(pts, axis=0)) < 3
                    or area == 0
                    or np.sign(area) != np.sign(loop_exact_area(seq, topo.arcs))
                ):
                    bad.update(a for a, _ in seq if not topo.arcs[a].exact)
        if not bad:
            break
        for aid in bad:
            topo.arcs[aid].exact = True
            topo.arcs[aid].simple = simplify_arc(topo.arcs[aid], epsilon)
    return sum(arc.exact for arc in topo.arcs)


# --------------------------------------------------------------------------
# 4. SVG path data


def fmt(v2: int) -> str:
    """A doubled coordinate as text: integer, or .5 for midpoints."""
    return str(v2 // 2) if v2 % 2 == 0 else f"{v2 // 2}.5"


def pt(p2: tuple[int, int] | list[int]) -> str:
    return f"{fmt(p2[0])} {fmt(p2[1])}"


def mid(a: list[int], b: list[int]) -> list[int]:
    return [(a[0] + b[0]) // 2, (a[1] + b[1]) // 2]  # doubled coordinates: exact


def doubled(points: np.ndarray) -> list[list[int]]:
    return (points.astype(np.int64) * 2).tolist()


def open_cmds(points: np.ndarray, smooth: bool) -> list[str]:
    """Commands continuing from points[0] (the current point) along an open arc.

    Smooth: quadratic B-spline, control point v_i and end point
    midpoint(v_i, v_i+1) for interior vertices, the last one ending at v_n.
    """
    p = doubled(points)
    if not smooth or len(p) == 2:
        return [f"L{pt(q)}" for q in p[1:]]
    last = len(p) - 2
    return [f"Q{pt(p[i])} {pt(p[i + 1] if i == last else mid(p[i], p[i + 1]))}" for i in range(1, len(p) - 1)]


def ring_d(points: np.ndarray, smooth: bool) -> str:
    """A closed subpath through ``points`` (no repeated closing vertex)."""
    p = doubled(points)
    if not smooth:
        return f"M{pt(p[0])} " + " ".join(f"L{pt(q)}" for q in p[1:]) + " Z"
    n = len(p)
    cmds = [f"Q{pt(p[i])} {pt(mid(p[i], p[(i + 1) % n]))}" for i in range(n)]
    return f"M{pt(mid(p[-1], p[0]))} " + " ".join(cmds) + " Z"


def loop_d(seq: list[tuple[int, int]], arcs: list[Arc], smooth: bool) -> str:
    """A province loop's subpath. Smooth applies to shared arcs only: arcs on the
    image edge run along the frame and stay straight (smoothing would cut the corners).
    Arcs along the void stay straight too: nothing on the other side shares the curve,
    so a spline cutting a corner would leave a strip of the map uncovered."""
    if len(seq) == 1 and arcs[seq[0][0]].closed:
        arc = arcs[seq[0][0]]
        return ring_d(oriented(arc, seq[0][1]), smooth and arc.internal)
    if not smooth:
        return ring_d(assemble(seq, arcs), False)
    first = oriented(arcs[seq[0][0]], seq[0][1])
    cmds = [f"M{pt(doubled(first[:1])[0])}"]
    for aid, d in seq:
        cmds += open_cmds(oriented(arcs[aid], d), arcs[aid].internal)
    return " ".join(cmds) + " Z"


def arc_d(arc: Arc, smooth: bool) -> str:
    assert arc.simple is not None
    smooth = smooth and arc.internal
    if arc.closed:
        return ring_d(arc.simple, smooth)
    return " ".join([f"M{pt(doubled(arc.simple[:1])[0])}"] + open_cmds(arc.simple, smooth))


PATH_CMD = re.compile(r"([MLQZ])([^MLQZ]*)")


def subpaths(d: str) -> list[list[str]]:
    """Flatten path data into subpaths of point tokens ("x y"), control points included.

    A trailing point equal to the subpath's first one (closing a ring) is dropped.
    """
    out: list[list[str]] = []
    for cmd, args in PATH_CMD.findall(d):
        nums = args.split()
        if cmd == "M":
            out.append([])
        if cmd == "Z":
            if len(out[-1]) > 1 and out[-1][-1] == out[-1][0]:
                out[-1].pop()
            continue
        out[-1] += [f"{nums[i]} {nums[i + 1]}" for i in range(0, len(nums), 2)]
    return out


def canon_tokens(tokens: list[str], ring: bool) -> tuple[str, ...]:
    if not ring:
        return min(tuple(tokens), tuple(reversed(tokens)))
    best: tuple[str, ...] | None = None
    for seq in (tokens, tokens[::-1]):
        low = min(seq)
        for k, t in enumerate(seq):
            if t == low:
                cand = tuple(seq[k:] + seq[:k])
                best = cand if best is None or cand < best else best
    assert best is not None
    return best


def arc_consistency(arcs: list[Arc], province_d: dict[str, str], smooth: bool) -> int:
    """Mismatches between each arc and its occurrences in the emitted SVG path data.

    Every province subpath is parsed back from its ``d`` text and cut at node
    coordinates; each piece (canonicalised for direction and, for node-less
    rings, rotation) must equal its arc's own emission token for token, and
    occur once per side (internal arcs twice, image-edge arcs once). Counts
    arcs that fail plus pieces that match no arc.
    """
    expected: dict[tuple[str, ...], int] = {}
    nodes: set[str] = set()
    for arc in arcs:
        toks = subpaths(arc_d(arc, smooth))[0]
        key = canon_tokens(toks, arc.closed)
        expected[key] = expected.get(key, 0) + len(arc.sides)
        if not arc.closed:
            nodes.update((toks[0], toks[-1]))
    seen: Counter = Counter()
    for d in province_d.values():
        for toks in subpaths(d):
            cut = [k for k, t in enumerate(toks) if t in nodes]
            if not cut:
                seen[canon_tokens(toks, True)] += 1
                continue
            toks = toks[cut[0] :] + toks[: cut[0]]
            cut = [k - cut[0] for k in cut] + [len(toks)]
            toks = toks + toks[:1]
            for a, b in zip(cut, cut[1:]):
                seen[canon_tokens(toks[a : b + 1], False)] += 1
    bad = sum(1 for key, n in expected.items() if seen.get(key, 0) != n)
    bad += sum(1 for key in seen if key not in expected)
    return bad


# --------------------------------------------------------------------------
# supply-centre markers


def default_center(mask: np.ndarray, anchor: list, offset: float) -> tuple[list[int], bool] | None:
    """A computed centre marker for a province's label mask: (point, found in the ring).

    Candidates are the mask pixels between ``offset`` and ``2 * offset`` from
    the anchor, so the marker clears the unit drawn on the anchor without
    drifting to the far end of the province. The one deepest inside the
    province wins (distance transform; the image edge counts as an edge), so
    the marker stays off borders and coastlines; ties go to the candidate
    closest to the anchor, then to the first in row order. With no candidate
    (a province too small for the ring): the mask pixel farthest from the
    anchor. None for an empty mask. Points are pixel coordinates (x, y).
    """
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return None
    d = np.hypot(xs - float(anchor[0]), ys - float(anchor[1]))
    ring = np.flatnonzero((d >= offset) & (d <= 2 * offset))
    if not len(ring):
        far = int(np.argmax(d))
        return [int(xs[far]), int(ys[far])], False
    oy, ox = int(ys.min()), int(xs.min())
    crop = np.pad(mask[oy : ys.max() + 1, ox : xs.max() + 1], 1).astype(np.uint8)
    depth = cv2.distanceTransform(crop, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)[1:-1, 1:-1]
    deep = depth[ys[ring] - oy, xs[ring] - ox]
    best = ring[np.lexsort((d[ring], -deep))[0]]  # lexsort: last key first; stable, so row order breaks ties
    return [int(xs[best]), int(ys[best])], True


@dataclass
class Centres:
    explicit: list[str] = field(default_factory=list)  # from trace.yaml
    computed: list[str] = field(default_factory=list)  # by default_center, in the ring
    fallback: list[str] = field(default_factory=list)  # by default_center, no ring candidate


def place_centers(provinces: list[dict], labels: np.ndarray, offset: float, anomalies: list[str]) -> Centres:
    """Set ``center`` on every supply centre lacking one; an explicit value always wins."""
    out = Centres()
    for i, p in enumerate(provinces):
        if p["kind"] not in ANCHORED or not p.get("supply_center"):
            continue
        if "center" in p:
            out.explicit.append(p["name"])
            continue
        spot = default_center(labels == i, p["position"], offset)
        if spot is None:  # no pixels at all (already an anomaly): keep the SVG valid
            p["center"] = p["position"]
            out.fallback.append(p["name"])
            anomalies.append(f"{p['name']}: no pixels, center placed on the anchor, set center in trace.yaml")
            continue
        p["center"], in_ring = spot
        if in_ring:
            out.computed.append(p["name"])
        else:
            out.fallback.append(p["name"])
            anomalies.append(f"{p['name']}: center placed at fallback, set center in trace.yaml")
    return out


def trace_notes(
    img: np.ndarray, provinces: list[dict], info: LabelInfo, void: tuple | None, centres: Centres, offset: float
) -> list[str]:
    """Informative report lines about what the sidecar drove: void, shared colours, centres, anchors."""
    total = img.shape[0] * img.shape[1]
    if void is None:
        notes = ["void             : none"]
    else:
        enclosed = int(np.count_nonzero(info.void)) - info.void_colour
        notes = [
            f"void             : {list(void)}, {pct(info.void_colour, total)} of the image, not traced; "
            f"{enclosed} px more enclosed by it (no province to reach)"
        ]
    claimants = sum(len(s.owners) for s in info.shared)
    notes.append(
        f"shared colours   : {len(info.shared)}"
        + (f" ({claimants} provinces, resolved by seed: their position's component)" if info.shared else "")
    )
    notes += [
        f"                   {list(s.colour)}: {len(s.owners)} provinces, {s.components} components, "
        f"{s.components - s.unseeded} seeded, {s.unseeded} unseeded ({s.unseeded_px} px, absorbed as border)"
        for s in info.shared
    ]
    notes.append(
        f"centres          : {len(centres.explicit)} explicit, {len(centres.computed) + len(centres.fallback)} "
        f"computed (offset {offset:g} px)" + (f"; fallback: {', '.join(centres.fallback)}" if centres.fallback else "")
    )
    off = []
    for p in provinces:
        if "position" in p:
            x, y = pixel(p["position"])
            if [int(c) for c in img[y, x]] != [int(c) for c in p["png"]]:
                off.append(p["name"])
    notes.append(
        f"anchors          : {len(off)} positions not on their own png colour" + (f" ({', '.join(off)})" if off else "")
    )
    return notes


# --------------------------------------------------------------------------
# measurement


@dataclass
class Traced:
    name: str
    kind: str
    parent: str | None
    water: bool
    png_pixels: int  # pixels of its PNG colour
    pixels: int  # pixels in the label image (border pixels absorbed)
    loops: list[np.ndarray]  # rebuilt simplified loops (vertices only, as the polygon)
    seqs: list[list[tuple[int, int]]]  # loops as (arc id, direction)
    outers: int  # loops with positive signed area (shapes)
    dropped: int  # pixels of components below --min-area
    iou: float = 0.0

    @property
    def holes(self) -> int:
        return len(self.loops) - self.outers

    @property
    def vertices(self) -> int:
        return sum(len(loop) for loop in self.loops)


def index_colour(index: int) -> str:
    """Flat fill encoding a province index (0-based) as 24-bit RGB; 0 is never used."""
    return f"#{index + 1:06x}"


def render(svg: str, width: int, height: int) -> np.ndarray:
    """Rasterise an SVG document with cairosvg at exactly width x height, as RGBA."""
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=width, output_height=height)
    bgra = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
    if bgra is None or bgra.shape != (height, width, 4):
        raise RuntimeError(f"unexpected cairosvg render: {None if bgra is None else bgra.shape}")
    return np.ascontiguousarray(bgra[:, :, [2, 1, 0, 3]])


def decode_labels(rgba: np.ndarray, count: int) -> np.ndarray:
    """Province index per pixel of a measurement render, -1 where no index colour matches.

    Only fully opaque pixels can match: antialiased edges (partial alpha, or
    blends of two index colours) are left unmatched.
    """
    rgb = rgba[:, :, :3].astype(np.int32)
    code = (rgb[:, :, 0] << 16) | (rgb[:, :, 1] << 8) | rgb[:, :, 2]
    labels = code - 1
    labels[(rgba[:, :, 3] != 255) | (code < 1) | (code > count)] = -1
    return labels


def iou(a: np.ndarray, b: np.ndarray) -> float:
    union = np.count_nonzero(a | b)
    return np.count_nonzero(a & b) / union if union else 0.0


def attr(value: object) -> str:
    return html.escape(str(value), quote=True)


def circle(cls: str, pos: list, coast: str | None = None) -> str:
    extra = f' data-coast="{attr(coast)}"' if coast is not None else ""
    return f'<circle class="{cls}"{extra} cx="{pos[0]}" cy="{pos[1]}" r="0"/>'


def build_svg(
    provinces: list[dict],
    province_d: dict[str, str],
    width: int,
    height: int,
    fills: dict[str, str] | None = None,
    strokes: bool = True,
) -> str:
    """The map SVG; with ``fills`` (name -> colour), the measurement-only variant.

    The measurement variant has the same province paths in the same order, but
    no style block, no anchors, and every path filled with its province's (or
    child's) flat colour and no stroke. ``strokes=False`` drops the stroke rule
    from the display style, leaving its fills only (gap measurement).
    """
    children: dict[str, list[dict]] = {}
    for p in provinces:
        if p["kind"] == "child":
            children.setdefault(p["parent"], []).append(p)

    def paint(name: str) -> str:
        return f' fill="{fills[name]}" stroke="none"' if fills is not None else ""

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">']
    if fills is None:
        style = f"{STYLE}\n{STROKE_STYLE}" if strokes else STYLE
        out.append(f"  <style>\n{style}\n  </style>")
    out.append('  <g class="provinces">')
    for p in provinces:
        if p["kind"] == "child":
            continue
        name = p["name"]
        out.append(f'    <g data-province="{attr(name)}" data-kind="{attr(p["kind"])}">')
        own_class = ' class="water"' if p.get("water") else ""
        if province_d.get(name):
            out.append(f'      <path{own_class}{paint(name)} fill-rule="evenodd" d="{province_d[name]}"/>')
        for child in children.get(name, []):
            cls = ' class="water"' if child.get("water") else ""
            if province_d.get(child["name"]):
                out.append(
                    f'      <path{cls}{paint(child["name"])} data-child="{attr(child["name"])}" '
                    f'fill-rule="evenodd" d="{province_d[child["name"]]}"/>'
                )
        if p["kind"] != "neutral" and fills is None:
            if "position" in p:
                out.append("      " + circle("anchor", p["position"]))
            for coast in p.get("coasts") or []:
                out.append("      " + circle("anchor", coast["position"], coast["name"]))
            if p.get("supply_center"):
                out.append("      " + circle("center", p["center"]))
        out.append("    </g>")
    out.append("  </g>")
    out += ["</svg>", ""]
    return "\n".join(out)


@dataclass
class RenderStats:
    total: int  # pixels in the image, void excluded (every count below excludes the void too)
    unmatched: int  # measurement render: pixels matching no index colour
    unmatched_empty: int  # ... of which fully transparent (no fill at all)
    background: int  # map.svg render without strokes: fully transparent pixels
    background_on_province: int  # ... of which a province colour in the PNG
    background_on_black: int  # ... of which black (border) in the PNG
    partial: int  # map.svg render without strokes: partially transparent pixels
    outside: int  # measurement render: province pixels outside its label mask, summed
    outside_worst: tuple[str, int]  # ... largest single province contribution
    uncovered: int  # label-image pixels left fully transparent by the measurement render
    uncovered_partial: int  # label-image pixels only partly covered (alpha < 255)


@dataclass
class TopoStats:
    labels: LabelInfo
    arcs: int
    internal: int
    edge_arcs: int
    closed: int
    void_arcs: int  # one-sided arcs along the void
    exact: int  # arcs reverted to the exact trace
    nodes: int
    border_nodes: int
    saddles: int
    degree: Counter
    mismatches: int


def pct(n: int, total: int) -> str:
    return f"{n} px ({100 * n / total:.2f}%)"


def build_report(
    traced: dict[str, Traced],
    anomalies: list[str],
    svg_bytes: int,
    epsilon: float,
    min_area: int,
    smooth: bool,
    stats: RenderStats,
    topo: TopoStats,
    notes: list[str],
) -> str:
    """The report text; ``notes`` are informative Totals lines (void, shared colours, centres)."""
    rows = sorted(traced.values(), key=lambda t: (t.iou, t.name))
    name_w = max(len(t.name) for t in rows) + 2
    lab = topo.labels
    lines = [
        f"png_to_svg fidelity report (epsilon={epsilon}, min-area={min_area}, smooth={'on' if smooth else 'off'})",
        "IoU: cairosvg render of the SVG (index-colour fills, no stroke) vs the expanded label",
        "image (PNG colour masks with every border pixel assigned to its nearest province),",
        "not the raw colour masks. 'pixels' is the expanded mask, 'absorbed' the border pixels",
        "it gained.",
        "",
        f"{'province':<{name_w}}{'kind':<16}{'pixels':>8}{'absorbed':>10}{'IoU':>8}{'shapes':>8}"
        f"{'vertices':>10}{'dropped px':>13}",
        "-" * (name_w + 73),
    ]
    for t in rows:
        kind = f"child<{t.parent}" if t.kind == "child" else t.kind
        if len(kind) > 15:
            kind = kind[:14] + "…"
        lines.append(
            f"{t.name:<{name_w}}{kind:<16}{t.pixels:>8}{t.pixels - t.png_pixels:>10}{t.iou:>8.4f}"
            f"{t.outers:>8}{t.vertices:>10}{t.dropped:>13}"
        )
    ious = [t.iou for t in rows]
    below = [t for t in rows if t.iou < IOU_THRESHOLD]
    degrees = ", ".join(f"degree {d}: {n}" for d, n in sorted(topo.degree.items()))
    lines += [
        "",
        "Totals",
        "------",
        f"provinces traced : {len(rows)} ({sum(t.kind != 'child' for t in rows)} groups, "
        f"{sum(t.kind == 'child' for t in rows)} children)",
        f"SVG bytes        : {svg_bytes}",
        f"total vertices   : {sum(t.vertices for t in rows)} in province paths",
        f"total shapes     : {sum(t.outers for t in rows)} outer loops (+ {sum(t.holes for t in rows)} hole loops)",
        f"total dropped    : {sum(t.dropped for t in rows)} px",
        *notes,
        f"border pixels    : {pct(lab.assigned, stats.total)} assigned to a province "
        f"({lab.assigned_thin} [4,2,4], {lab.assigned_black} black, "
        f"{lab.assigned - lab.assigned_thin - lab.assigned_black} other) in {lab.rounds} rounds; "
        f"{lab.ties} px tied (2+ different 4-neighbours, first of up/left/down/right wins)",
        f"arcs             : {topo.arcs} ({topo.internal} shared, {topo.edge_arcs} on the image "
        f"edge{f', {topo.void_arcs} along the void' if topo.void_arcs else ''}; {topo.closed} closed "
        f"node-less; {topo.exact} kept exact by the collapse guard)",
        f"nodes            : {topo.nodes} ({degrees}; {topo.saddles} two-label saddles; "
        f"{topo.border_nodes} on the image edge)",
        f"arc consistency  : {topo.mismatches} mismatches (each arc parsed back from every "
        "province path, byte-identical on both sides)",
        f"mean IoU         : {np.mean(ious):.4f}",
        f"min IoU          : {min(ious):.4f} ({rows[0].name})",
        f"below {IOU_THRESHOLD}      : {len(below)}" + (f" ({', '.join(t.name for t in below)})" if below else ""),
        f"render unmatched : {pct(stats.unmatched, stats.total)} matching no province colour "
        f"({stats.unmatched_empty} px unfilled, {stats.unmatched - stats.unmatched_empty} px "
        "antialiased)",
        f"render outside   : {stats.outside} px rendered as a province outside its label mask "
        f"(summed over provinces; worst {stats.outside_worst[0]} {stats.outside_worst[1]} px)",
        f"PNG uncovered    : {stats.uncovered} px of the label image with nothing rendered "
        f"(alpha 0; {stats.uncovered_partial} px more only partly covered)",
        "",
        "Gaps (cairosvg render of map.svg with its display style, fills only, without strokes)",
        "-------------------------------------------------------------------------------------",
        f"background       : {pct(stats.background, stats.total)} not covered by any province "
        f"(on PNG province colours {stats.background_on_province} px, on PNG black "
        f"{stats.background_on_black} px, on other PNG colours "
        f"{stats.background - stats.background_on_province - stats.background_on_black} px)",
        f"partly covered   : {pct(stats.partial, stats.total)} (antialiased, alpha < 255)",
        "",
        "Anomalies",
        "---------",
    ]
    lines += [f"- {a}" for a in anomalies] or ["none"]
    return "\n".join(lines) + "\n"


PREVIEW = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} - SVG trace preview</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 12px; background: #f4f4f4; }}
  #controls {{ margin-bottom: 8px; display: flex; gap: 16px; align-items: center; }}
  #stages {{ display: flex; gap: 12px; align-items: flex-start; }}
  .stage {{ position: relative; width: {w}px; height: {h}px; border: 1px solid #999; flex: none;
            background: var(--ground, #f4f4f4); }}
  .stage > img, .stage > svg {{ position: absolute; left: 0; top: 0; width: {w}px; height: {h}px; }}
  .stage > img {{ image-rendering: pixelated; }}
  #twin {{ display: none; }}
  body.side #twin {{ display: block; }}
  body.nopng #stage > img {{ visibility: hidden; }}
  body.dark .stage {{ --ground: #111; }}
  .cross {{ position: absolute; pointer-events: none; display: none; }}
  .cross::before, .cross::after {{ content: ''; position: absolute; background: #f0f; }}
  .cross::before {{ left: -12px; top: 0; width: 25px; height: 1px; }}
  .cross::after {{ left: 0; top: -12px; width: 1px; height: 25px; }}
  #label {{ position: fixed; top: 8px; right: 8px; padding: 6px 10px; background: #222;
            color: #fff; font-size: 14px; border-radius: 4px; min-width: 120px; }}
  #label:empty {{ display: none; }}
  g[data-province].hl path {{ fill: #ffd54a !important; stroke: #c00 !important; stroke-width: 1.5 !important; }}
  g[data-province].hl path[data-child] {{ fill: #ff9f43 !important; }}
  circle.anchor, circle.center {{ r: 3px; pointer-events: none; stroke: #000; stroke-width: 0.6; }}
  circle.anchor {{ fill: #e53935; }}
  circle.anchor[data-coast] {{ fill: #1e88e5; }}
  circle.center {{ fill: #fff; r: 3.5px; }}
  pre {{ background: #fff; border: 1px solid #ccc; padding: 8px; font-size: 12px; }}
  .legend span {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%;
                  border: 1px solid #000; margin: 0 4px 0 10px; vertical-align: middle; }}
</style>
</head>
<body>
<div id="controls">
  <label>SVG opacity <input id="opacity" type="range" min="0" max="1" step="0.05" value="0.7">
    <output id="opacity-value">0.70</output></label>
  <label><input id="hide" type="checkbox"> hide SVG</label>
  <label><input id="nopng" type="checkbox"> hide PNG</label>
  <label><input id="side" type="checkbox"> PNG side by side</label>
  <label><input id="dark" type="checkbox"> dark ground</label>
  <label>scale <input id="scale" type="range" min="0.25" max="3" step="0.25" value="1">
    <output id="scale-value">1.00</output></label>
  <span class="legend"><span style="background:#e53935"></span>anchor
    <span style="background:#1e88e5"></span>coast anchor
    <span style="background:#fff"></span>supply centre</span>
</div>
<div id="label"></div>
<div id="stages">
<div id="stage" class="stage">
  <img src="map.png" alt="label map" width="{w}" height="{h}">
{svg}
</div>
<div id="twin" class="stage">
  <img src="map.png" alt="label map" width="{w}" height="{h}">
  <div class="cross"></div>
</div>
</div>
<h3>Report</h3>
<pre>{report}</pre>
<script>
  const svg = document.querySelector('#stage > svg');
  const opacity = document.getElementById('opacity');
  const opacityValue = document.getElementById('opacity-value');
  const hide = document.getElementById('hide');
  const label = document.getElementById('label');
  const stages = document.getElementById('stages');
  const scale = document.getElementById('scale');
  const scaleValue = document.getElementById('scale-value');
  const cross = document.querySelector('#twin .cross');
  const apply = () => {{
    svg.style.opacity = opacity.value;
    opacityValue.textContent = Number(opacity.value).toFixed(2);
    svg.style.visibility = hide.checked ? 'hidden' : 'visible';
    stages.style.zoom = scale.value;
    scaleValue.textContent = Number(scale.value).toFixed(2);
    for (const id of ['nopng', 'side', 'dark']) {{
      document.body.classList.toggle(id, document.getElementById(id).checked);
    }}
  }};
  for (const id of ['opacity', 'hide', 'nopng', 'side', 'dark', 'scale']) {{
    document.getElementById(id).addEventListener('input', apply);
  }}
  apply();
  const stage = document.getElementById('stage');
  stage.addEventListener('mousemove', (event) => {{
    const box = stage.getBoundingClientRect();
    cross.style.display = 'block';
    cross.style.left = ((event.clientX - box.left) / box.width * {w}) + 'px';
    cross.style.top = ((event.clientY - box.top) / box.height * {h}) + 'px';
  }});
  stage.addEventListener('mouseleave', () => {{ cross.style.display = 'none'; }});
  let current = null;
  svg.addEventListener('mouseover', (event) => {{
    const path = event.target.closest('path');
    const group = path && path.closest('g[data-province]');
    if (current && current !== group) current.classList.remove('hl');
    current = group;
    if (!group) {{ label.textContent = ''; return; }}
    group.classList.add('hl');
    group.parentNode.appendChild(group);  // paint last: a stroke is half outside, later siblings would cover it
    let text = group.dataset.province + ' (' + group.dataset.kind + ')';
    if (path.dataset.child) text += ' / ' + path.dataset.child;
    label.textContent = text;
  }});
  svg.addEventListener('mouseleave', () => {{
    if (current) current.classList.remove('hl');
    current = null;
    label.textContent = '';
  }});
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        epilog="Reads <variant>/<folder name>.yaml, <variant>/trace.yaml (colours, anchors, centres, void) "
        "and <variant>/map.png; writes map.svg, report.txt and preview.html next to them. The trace.yaml "
        "format, the shared-colour seed rule and the void are described in the module docstring.",
    )
    parser.add_argument(
        "variant", type=Path, help="variant folder (contains <folder name>.yaml, trace.yaml and map.png)"
    )
    parser.add_argument("--epsilon", type=float, default=1.0, help="approxPolyDP epsilon (px), per arc")
    parser.add_argument(
        "--min-area",
        type=int,
        default=0,
        help="relabel 4-connected components with fewer pixels than this as border, "
        "absorbed by their neighbours (0 keeps all)",
    )
    parser.add_argument(
        "--no-smoothing",
        dest="smooth",
        action="store_false",
        help="emit arcs as straight polylines instead of quadratic B-splines through the simplified vertices",
    )
    parser.add_argument(
        "--center-offset",
        type=float,
        default=24.0,
        metavar="R",
        help="supply centres without a center in trace.yaml get one computed between R and 2R px from "
        "their anchor, as deep inside the province as possible (default 24)",
    )
    args = parser.parse_args()

    folder: Path = args.variant
    variant_file = folder / f"{folder.resolve().name}.yaml"
    trace_file = folder / "trace.yaml"
    for path in (variant_file, trace_file):
        if not path.is_file():
            parser.error(f"missing {path}")
    doc = yaml.safe_load(variant_file.read_text())
    img_bgr = cv2.imread(str(folder / "map.png"), cv2.IMREAD_COLOR)
    if img_bgr is None:
        parser.error(f"cannot read {folder / 'map.png'}")
    img = np.ascontiguousarray(img_bgr[:, :, ::-1])
    height, width = img.shape[:2]
    try:
        provinces, void = merge_trace(doc["provinces"], yaml.safe_load(trace_file.read_text()), img)
    except SidecarError as e:
        print(e, file=sys.stderr)
        return 2
    names = {p["name"] for p in provinces}

    # 1. label image
    info = assign_labels(img, provinces, args.min_area, void)
    labels = info.labels

    # 2.-3. shared arcs, simplification
    topo = build_topology(labels, len(provinces), info.void)
    simplify_all(topo, args.epsilon)
    arcs = topo.arcs

    anomalies: list[str] = list(info.anomalies)
    traced: dict[str, Traced] = {}
    province_colours: set[tuple] = set()
    province_d: dict[str, str] = {}
    for i, p in enumerate(provinces):
        colour = tuple(int(c) for c in p["png"])
        province_colours.add(colour)
        png_pixels = info.own[i]  # its colour, or its seeded component of a shared colour
        seqs = topo.loops.get(i, [])
        t = Traced(
            p["name"],
            p["kind"],
            p.get("parent"),
            bool(p.get("water")),
            png_pixels,
            int(np.count_nonzero(labels == i)),
            [assemble(s, arcs) for s in seqs],
            seqs,
            topo.outers.get(i, 0),
            info.dropped.get(p["name"], 0),
        )
        traced[p["name"]] = t
        province_d[p["name"]] = " ".join(loop_d(s, arcs, args.smooth) for s in seqs)
        if not np.all(img == colour, axis=-1).any():
            anomalies.append(f"{p['name']}: png colour {list(colour)} matches zero pixels")
        elif not seqs and t.dropped:  # no seeded pixels at all is already a seed anomaly
            anomalies.append(f"{p['name']}: {png_pixels} px but no component survived min-area")
        if t.outers > MANY_SHAPES:
            anomalies.append(f"{p['name']}: {t.outers} shapes (> {MANY_SHAPES})")
        own = png_pixels - t.dropped
        if own and (t.pixels - own) > GROWTH_WARN * own:
            anomalies.append(
                f"{p['name']}: absorbed {t.pixels - own} border px, "
                f"{100 * (t.pixels - own) / own:.0f}% of its own {own} px"
            )
        if p["kind"] == "child":
            if p.get("parent") not in names:
                anomalies.append(f"{p['name']}: child of unknown parent {p.get('parent')!r}")
            if not p.get("water"):
                anomalies.append(f"{p['name']}: child without water: true")
        elif p.get("water"):
            anomalies.append(
                f'{p["name"]}: water: true on kind {p["kind"]} (not a child); own paths emitted with class="water"'
            )

    colours, counts = np.unique(img.reshape(-1, 3), axis=0, return_counts=True)
    for colour, count in zip(colours.tolist(), counts.tolist()):
        if tuple(colour) in BORDER_COLOURS or tuple(colour) in province_colours or tuple(colour) == void:
            continue
        anomalies.append(f"PNG colour {colour} ({count} px) matches no province; assigned as border")

    centres = place_centers(provinces, labels, args.center_offset, anomalies)
    notes = trace_notes(img, provinces, info, void, centres, args.center_offset)

    svg = build_svg(provinces, province_d, width, height)
    svg_bytes = len(svg.encode())
    mismatches = arc_consistency(arcs, province_d, args.smooth)

    # fidelity: measurement render, one index colour per province / child, vs the label image
    # (the void is not map: IoU and the coverage counts leave it out; "outside" keeps it, since a
    # province spilling into the void is rendered where it should not be, like into a neighbour)
    fills = {p["name"]: index_colour(i) for i, p in enumerate(provinces)}
    measure = render(build_svg(provinces, province_d, width, height, fills), width, height)
    decoded = decode_labels(measure, len(provinces))
    keep = ~info.void
    outside: dict[str, int] = {}
    for i, p in enumerate(provinces):
        t = traced[p["name"]]
        mask = labels == i
        outside[p["name"]] = int(np.count_nonzero((decoded == i) & ~mask))
        if t.pixels:
            t.iou = iou((decoded == i) & keep, mask)

    # gaps: the real document as displayed, fills only (no stroke to mask gaps)
    real = render(build_svg(provinces, province_d, width, height, strokes=False), width, height)
    alpha = real[:, :, 3]
    empty = alpha == 0
    province_px = info.raw >= 0
    m_alpha = measure[:, :, 3]
    stats = RenderStats(
        total=int(np.count_nonzero(keep)),
        unmatched=int(np.count_nonzero((decoded == -1) & keep)),
        unmatched_empty=int(np.count_nonzero((m_alpha == 0) & keep)),
        background=int(np.count_nonzero(empty & keep)),
        background_on_province=int(np.count_nonzero(empty & province_px)),
        background_on_black=int(np.count_nonzero(empty & info.black & keep)),
        partial=int(np.count_nonzero((alpha > 0) & (alpha < 255) & keep)),
        outside=sum(outside.values()),
        outside_worst=max(outside.items(), key=lambda kv: kv[1]),
        uncovered=int(np.count_nonzero((m_alpha == 0) & keep)),
        uncovered_partial=int(np.count_nonzero((m_alpha > 0) & (m_alpha < 255) & keep)),
    )
    internal = [a for a in arcs if a.internal]
    frame = [a for a in arcs if a.frame]
    tstats = TopoStats(
        labels=info,
        arcs=len(arcs),
        internal=len(internal),
        edge_arcs=len(frame),
        void_arcs=len(arcs) - len(internal) - len(frame),
        closed=sum(a.closed for a in arcs),
        exact=sum(a.exact for a in arcs),
        nodes=len(topo.nodes),
        border_nodes=topo.border_nodes,
        saddles=topo.saddles,
        degree=topo.degree,
        mismatches=mismatches,
    )
    report = build_report(traced, anomalies, svg_bytes, args.epsilon, args.min_area, args.smooth, stats, tstats, notes)

    (folder / "map.svg").write_text(svg)
    (folder / "report.txt").write_text(report)
    inline_svg = "\n".join("  " + line for line in svg.splitlines())
    (folder / "preview.html").write_text(
        PREVIEW.format(
            title=attr(doc.get("name", folder.name)),
            w=width,
            h=height,
            svg=inline_svg,
            report=html.escape(report),
        )
    )
    print(report, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
