def avg_turns(turns):
    played = sum(turns.values())
    if not played:
        return None
    return round(sum(int(turn) * count for turn, count in turns.items()) / played, 1)


def win_rates(countries_row, map_countries):
    countries_row = countries_row or {}
    played = countries_row.get("played", {})
    won = countries_row.get("won", {})
    return [
        (name, colour, won.get(name, 0) / played[name] * 100 if played.get(name) else None)
        for name, colour in map_countries.items()
    ]


def country_outcomes(countries_row, map_countries):
    countries_row = countries_row or {}
    fields = ("played", "won", "survived", "defeated", "drawn")
    return [
        (name, colour, *(int(countries_row.get(field, {}).get(name, 0)) for field in fields))
        for name, colour in map_countries.items()
    ]
