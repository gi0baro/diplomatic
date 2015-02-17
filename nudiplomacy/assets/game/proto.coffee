Array.prototype.insert = (index, item) ->
    @splice(index, 0, item)
    return

Array.prototype.last = ->
    this[-1..][0]
