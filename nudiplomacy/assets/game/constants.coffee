class Constants
    constructor: ->
        @_reversed = {}
        for key, val of this
            if typeof(val) isnt "number"
                continue
            @_reversed[val] = key

    internal_to_remote: (val) ->
        return this[val]

    remote_to_internal: (val) ->
        return @_reversed[val]


class TConstants extends Constants
    translator_namespace: 'constants'

    translate: (val) ->
        return T.get(@translator_namespace + '.' + @remote_to_internal(val))


class PhaseTypes extends TConstants
    translator_namespace: 'phase_type'
    diplomacy: 0
    retreats: 1
    builds: 2
    # pregame: 10
    # won: 20


class Seasons extends TConstants
    translator_namespace: 'season'
    spring: 0
    autumn: 1


class OrderTypes extends TConstants
    translator_namespace: 'order_type'
    hold: 0
    move: 1
    support_hold: 2
    support_move: 3
    convoy: 4
    retreat: 5
    build: 6
    disband: 7


class TroopTypes extends TConstants
    translator_namespace: 'troop_type'
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
