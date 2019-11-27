class Translator
    constructor: ->
        @data = {}

    register_item: (key, val) ->
        @data[key+''] = val

    register: (data, namespace=null) ->
        prefix = if namespace is null then '' else namespace + '.'
        for key, val of data
            @register_item(prefix + key, val)

    get: (key) ->
        return @data[key+''] or key

window.T = new Translator()
