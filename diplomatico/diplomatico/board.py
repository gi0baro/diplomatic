from collections import defaultdict


class Board:
    __slots__ = [
        "seas", "coasts", "neutrals", "multi_coasts", "supply_centers", "links",
        "troops", "armies", "fleets", "coast_positions", "_convoy_routes",
    ]

    def __init__(self, map_data, troops, coast_positions):
        self.seas = set(map_data["seas"])
        self.coasts = set(map_data["coasts"])
        self.neutrals = set(map_data["neutrals"])
        self.multi_coasts = set(map_data["multi_coasts"])
        self.supply_centers = set(map_data["supply_centers"])
        self.links = map_data["links"]
        self.troops = troops
        self.armies = {territory for country in troops.values() for territory in country["armies"]}
        self.fleets = {territory for country in troops.values() for territory in country["fleets"]}
        self.coast_positions = coast_positions
        self._convoy_routes = {}

    def is_empty(self, territory):
        return territory not in self.armies and territory not in self.fleets

    def can_move(self, src, dst):
        if src not in self.fleets:
            return dst in self.links["armies"].get(src, [])
        return dst in self._fleet_links(src)

    def touches_coast(self, src, dst, coast):
        return src in self.links["multi_coasts"][dst][coast]

    def _fleet_links(self, src):
        if src in self.multi_coasts:
            return self.links["multi_coasts"][src][self.coast_positions[src]]
        return self.links["fleets"].get(src, [])

    def convoy_routes(self, src, dst):
        if src not in self._convoy_routes:
            self._convoy_routes[src] = self._walk_convoys(src)
        return self._convoy_routes[src].get(dst, [])

    def _walk_convoys(self, src):
        routes = defaultdict(list)
        convoyers = self.fleets & self.seas

        def walk(node, chain):
            for link in self.links["fleets"].get(node, []):
                if link in self.coasts and link != src:
                    routes[link].append(chain)
                elif link in convoyers and link not in chain:
                    walk(link, [*chain, link])

        for sea in self.links["fleets"].get(src, []):
            if sea in convoyers:
                walk(sea, [sea])
        return routes


class Player:
    __slots__ = ["troops", "territories", "build_centers"]

    def __init__(self, troops, territories, build_centers):
        self.troops = set(troops)
        self.territories = set(territories)
        self.build_centers = set(build_centers)
