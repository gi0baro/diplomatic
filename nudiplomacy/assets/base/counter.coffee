class Counter
    constructor: (id, @s=0, @m=0, @h=0, @d=0) ->
        @div = $('#'+id)
        @resets = 0

    draw: ->
        @div.html(@d+':'+@h+':'+@m+':'+@s)
        return

    start: ->
        if @d is 0
            @resets++
            if @h is 0
                @resets++
                if @m is 0
                    @resets++
        @draw()
        div = @div.attr('id')
        setInterval(->
            counters.istances[div].count()
            return
        , 1000)
        return

    count: ->
        if @resets < 4
            if @s is 0
                if @resets < 3
                    @s = 59
                    if @m is 0
                        if @resets < 2
                            @m = 59
                            if @h is 0
                                if @resets < 1
                                    @h = 23
                                    if @d is 0
                                        @resets++
                                    else
                                        @d--
                                else
                                    @resets++
                            else
                                @h--
                        else
                            @resets++
                    else
                        @m--
                else
                    @resets++
            else
                @s--
            @draw()
        return

window.counters =
    istances: {}

    add: (id, s, m, h, d) ->
        counters.istances[id] = new Counter id, s, m, h, d
        counters.istances[id].start()
