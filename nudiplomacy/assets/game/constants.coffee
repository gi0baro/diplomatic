class Constants
    constructor: ->
        @_reversed = {}
        for key, val of this
            @_reversed[val] = key

    internal_to_remote: (val) ->
        return this[val]

    remote_to_internal: (val) ->
        return @_reversed[val]


class PhaseTypes extends Constants
    diplomacy: 0
    retreats: 1
    builds: 2
    pregame: 10
    won: 20


class Seasons extends Constants
    spring: 0
    autumn: 1


class OrderTypes extends Constants
    hold: 0
    move: 1
    support_hold: 2
    support_move: 3
    convoy: 4
    retreat: 5
    build: 6
    disband: 7


class TroopTypes extends Constants
    army: 0
    fleet: 1


class OrderStates extends Constants
    planned: 0
    successful: 1
    failed: 2


window.PHASE_TYPES = new PhaseTypes()
window.SEASONS = new Seasons()
window.ORDER_TYPES = new OrderTypes()
window.TROOP_TYPES = new TroopTypes()
window.ORDER_STATES = new OrderStates()
