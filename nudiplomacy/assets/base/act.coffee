class Act
    constructor: ->
        @jgid = null

    _showJoinFrame: ->
        $('#joinframe').fadeToggle 350
        return

    hideJoinFrame: ->
        @jgid = null
        $('#joinframe').fadeToggle(
            350
            (event) ->
                return
            )
        return

    joinGame: (gid, bet) ->
        @jgid = gid
        $('#betwarn').html bet
        @_showJoinFrame()
        return

    confirmJoinGame: (gid) ->
        $('#joinmsg').html "Joining.."
        $('#joinbtn').attr
            disabled: 'disabled'
        api.join(gid)
        return

    joinedGame: ->
        self = this
        $('#joinmsg').html "You joined the game successfully."
        $('#joinbtn').css
            display: 'none'
        setTimeout(
            ->
                window.location.replace(api.urls.game+"/"+self.jgid)
                return
            1000
        )
        return

    cannotJoin: (msg) ->
        $('#joinmsg').html msg
        $('#joinbtn').html "Error"
        return

    createGame: ->
        $('#games_map').change ->
            act._gameFormChange()
            return
        $("#phase_slider").slider
            tooltip: 'hide'
        $("#phase_slider").on "slide", (slideEvt) ->
            act._gameFormSlideUpdate("#phase_slider_text", slideEvt.value)
            return
        $("#join_slider").slider
            tooltip: 'hide'
        $("#join_slider").on "slide", (slideEvt) ->
            act._gameFormSlideUpdate("#join_slider_text", slideEvt.value)
            return
        $('#bet_slider').slider
            tooltip: 'hide'
        $("#bet_slider").on "slide", (slideEvt) ->
            $("#bet_slider_text").text slideEvt.value
            $("#bet_slider_hide").html slideEvt.value
            return
        $('#games_nplayers').change ->
            act._gameFormNPChange()
            return
        $('#games_countriesassign').change ->
            act._gameFormCAChange()
            return
        $('#games_countries').change ->
            $('#games_countries_hide').html '{"me": "'+$('#games_countries').val()+'"}'
            return
        $('#games_access').change ->
            val = $(this).val()
            if val is "free"
                $('#games_psw_c').addClass 'nulled'
                $('#games_psw_hide').val('')
            else
                $('#games_psw_c').removeClass 'nulled'
            return
        return

    _gameFormChange: ->
        map_id = $('#games_map').val()
        #: set nplayers
        nplayers = mapdata[map_id].nplayers
        $('#games_nplayers').html ''
        for i in [nplayers[0]..nplayers[1]].reverse()
            $('#games_nplayers').append '<option value="'+i+'">'+i+'</option>'
        #: set enabled countries
        $('#games_ce').html('')
        for el in mapdata[map_id].countries
            $('#games_ce').append '<div class="col-sm-4"><div class="col-sm-8">'+ el + '</div><div class="col-sm-4">' +
                '<input class="boolean checkbox countrycheck" type="checkbox" value="'+el+'" checked="checked" /></div></div>'
        $('#games_ce_hide').html JSON.stringify(mapdata[map_id].countries)
        $('.countrycheck').change ->
            act._gameFormCEUpdate()
        return

    _gameFormNPChange: ->
        val = $('#games_nplayers').val()
        if val is '2'
            $('#bet_slider').slider "disable"
            $('#bet_slider_text').text '1 (max for 2 players)'
            $("#bet_slider_hide").html 1
        else
            $('#bet_slider').slider "enable"
            $('#bet_slider_text').text $('#bet_slider').slider 'getValue'
            $("#bet_slider_hide").html $('#bet_slider').slider 'getValue'
        return

    _gameFormCEUpdate: (el) ->
        data = []
        $('.countrycheck').each ->
            if $(this).prop('checked')
                data.push $(this).val()
        $('#games_ce_hide').html JSON.stringify(data)
        @_gameFormCAChange()
        return

    _gameFormSlideUpdate: (id, val) ->
        values =
            '1': 10
            '2': 15
            '3': 20
            '4': 30
            '5': 45
            '6': 60
            '7': 90
            '8': 60*2
            '9': 60*3
            '10': 60*4
            '11': 60*5
            '12': 60*6
            '13': 60*8
            '14': 60*10
            '15': 60*12
            '16': 60*14
            '17': 60*16
            '18': 60*18
            '19': 60*20
            '20': 60*22
            '21': 60*24
            '22': 60*30
            '23': 60*36
            '24': 60*42
            '25': 60*24*2
            '26': 60*60
            '27': 60*24*3
            '28': 60*24*4
            '29': 60*24*5
            '30': 60*24*6
            '31': 60*24*7
            '32': 60*24*8
            '33': 60*24*9
            '34': 60*24*10
        val = values[val]
        $(id.split("_")[0]+"_slider_hide").html val
        d = Math.floor(val/(60*24))
        h = Math.floor(val/60) % 24
        m = val % 60
        s = ""
        if d
            ds = if d > 1 then " days " else " day "
            s += d+ds
        if h
            hs = if h > 1 then " hours " else " hour "
            s += h+hs
        if m
            s += m+" minutes"
        $(id).text s
        return

    _gameFormCAChange: ->
        val = $('#games_countriesassign').val()
        $('#games_countries').html ''
        $('#games_countries_hide').html ''
        if val is "random"
            $('#games_countries_c').addClass 'nulled'
        else
            chs = []
            $('.countrycheck').each ->
                if $(this).prop('checked')
                    chs.push $(this).val()
            for c in chs
                $('#games_countries').append '<option class="cchoice" value="'+c+'">'+c+'</option>'
            $('#games_countries_hide').html '{"me": "'+$('#games_countries').val()+'"}'
            $('#games_countries_c').removeClass 'nulled'
        return

    _gameFormToggleAdv: ->
        if $('#advancedblock').hasClass('nulled')
            # is hidden, we show it up
            $('#advancedblock').removeClass('nulled')
            $('#advanced-btn').html 'Hide them'
            $('#advanced-btn-i').removeClass('fa-angle-down')
            $('#advanced-btn-i').addClass('fa-angle-up')
        else
            # is visible, hide it
            $('#advancedblock').addClass('nulled')
            $('#advanced-btn').html 'Show them'
            $('#advanced-btn-i').addClass('fa-angle-down')
            $('#advanced-btn-i').removeClass('fa-angle-up')
        return


window.act = new Act()
