Array.prototype.insert = (item, index=0) ->
    @splice(index, 0, item)
    return

Array.prototype.last = ->
    this[-1..][0]
