class Act
    constructor: ->
        @jgid = null
        @jce = {}
        @jLastMsg = ""

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

    joinGame: (gid, bet, chcountry="nope", password="none") ->
        @jgid = gid
        $('#betwarn').html bet
        if chcountry isnt "nope"
            $('#joincountrysel').html ''
            $('#joincountry').removeClass 'nulled'
            clist = @jce[@jgid]
            for i in clist
                $('#joincountrysel').append '<option value="'+i+'">'+i+'</option>'
        else
            $('#joincountry').addClass 'nulled'
        if password isnt "none"
            $('#joinpsw').removeClass 'nulled'
        else
            $('#joinpsw').addClass 'nulled'
        $('#joinerr').addClass 'nulled'
        @_showJoinFrame()
        return

    confirmJoinGame: (gid) ->
        $('#joinerr').addClass 'nulled'
        psw = null
        country = null
        @jLastMsg = $('#joinmsg').html()
        $('#joinmsg').html "Joining.."
        $($('#joinbtn').children()[0]).attr
            disabled: 'disabled'
        if not $('#joinpsw').hasClass('nulled')
            psw = $('#joinpswinput').val()
        if not $('#joincountry').hasClass('nulled')
            country = $('#joincountrysel').val()
        api.join(gid, country, psw)
        return

    joinedGame: ->
        self = this
        $('#joinmsg').html "You joined the game successfully."
        $('#joinpsw').addClass 'nulled'
        $('#joincountry').addClass 'nulled'
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
        $('#joinmsg').html @jLastMsg
        $('#joinerr').html msg
        $('#joinerr').removeClass 'nulled'
        $($('#joinbtn').children()[0]).attr
            disabled: false
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
        $('#games_players_number').change ->
            act._gameFormNPChange()
            return
        $('#games_countries_assignment').change ->
            act._gameFormCAChange()
            return
        $('#games_countries_enabled').change ->
            $('#games_countries_enabled_hide').html '{"me": "'+$('#games_countries').val()+'"}'
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
        #: set map preview
        $('#games_map_img').attr('src', mapdata[map_id].thumb)
        #: set nplayers
        nplayers = mapdata[map_id].players_number
        $('#games_players_number').html ''
        for i in [nplayers[0]..nplayers[1]].reverse()
            $('#games_players_number').append '<option value="'+i+'">'+i+'</option>'
        #: set enabled countries
        $('#games_countries_enabled').html('')
        for el in mapdata[map_id].countries
            $('#games_countries_enabled').append '<div class="col-sm-4"><div class="col-sm-8">'+ el + '</div><div class="col-sm-4">' +
                '<input class="boolean checkbox countrycheck" type="checkbox" value="'+el+'" checked="checked" /></div></div>'
        enabled_countries_map = {}
        for country in mapdata[map_id].countries
            enabled_countries_map[country] = true
        $('#games_countries_enabled_hide').html JSON.stringify(enabled_countries_map)
        $('.countrycheck').change ->
            act._gameFormCEUpdate()
            return
        $('.daycheck').change ->
            act._gameFormSPUpdate()
            return
        return

    _gameFormNPChange: ->
        val = $('#games_players_number').val()
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
        $('#games_countries_enabled_hide').html JSON.stringify(data)
        @_gameFormCAChange()
        return

    _gameFormSPUpdate: (el) ->
        data = {}
        $('.daycheck').each ->
            if $(this).prop('checked')
                data[$(this).val()] = true
        $('#games_sp_hide').html JSON.stringify(data)
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
        val = $('#games_countries_assignment').val()
        console.log(val)
        $('#games_countries_choice_selection').html ''
        $('#games_countries_choice_hide').html ''
        if val is "0"
            $('#games_countries_choice').addClass 'nulled'
        else
            chs = []
            $('.countrycheck').each ->
                if $(this).prop('checked')
                    chs.push $(this).val()
            for c in chs
                $('#games_countries_choice_selection').append '<option class="cchoice" value="'+c+'">'+c+'</option>'
            $('#games_countries_choice_hide').html $('#games_countries_choice_selection').val()
            $('#games_countries_choice').removeClass 'nulled'
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
