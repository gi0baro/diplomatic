Array.prototype.insert = (index, item) ->
    @splice(index, 0, item)
    return

Array.prototype.last = ->
    this[-1..][0]

window.isObjectEmpty = window.isObjectEmpty || (obj) ->
    return !obj or Object.keys(obj).length is 0
