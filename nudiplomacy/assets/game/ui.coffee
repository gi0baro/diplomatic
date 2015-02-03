
class UI
    constructor: ->
        @w = 0
        @h = 0
        @zoom = 0
        @scroll =
            x: 0
            y: 0
        @img = ''
        @menuStatus =
            left: "closed"
            right: "closed"
        @mouseTimer = null
        @barsOpened = 0
        @statsBar = "closed"
        @saveTimer = null
        @isSaving = false
        @isSettingReady = false
        @_statsCharts = {}
        return

    init: ->
        @img = document.getElementById("map_img")
        return

    setProps: ->
        @_setOverflow()
        #@_setTopMenu()
        @_getPageDim()
        @_evalZoom()
        return

    _setOverflow: ->
        #: we need to evaluate screen size because of the zoom eval (seems that the scroll bars make width wrong when overflow is auto)
        i_ch_h = app.screen.img.height
        console.log(i_ch_h)
        console.log($(window).height())
        if i_ch_h > $(window).height()
            $('#cont_wrapper').css 'overflow-y': 'scroll'
        else
            $('#cont_wrapper').css 'overflow-y': 'hidden'
        return

    _setTopMenu: ->
        ww = $(window).width()
        mw = $('#top_wrapper').width()
        per = (((ww/2)-(mw/2))/ww)*100
        $('#top_wrapper').css 'left': per+'%'
        $('#top_sensor').css 'left': per+'%'
        return

    _getPageDim: ->
        @w = $("#map_wrapper").width()
        @h = $("#map_wrapper").height()
        console.log(@w)
        console.log(@h)
        return

    _evalZoom: ->
        @zoom = @w/app.screen.img.width
        console.log(@zoom)
        return

    ## useless??
    evalScroll: ->
        @scroll.x = document.getElementById('map_wrapper').scrollTop
        @scroll.y = document.getElementById('map_wrapper').scrollLeft
        return

    showMap: (canvasHeight) ->
        $("#map_img").css
            opacity: "1"
            height: canvasHeight*@zoom+"px"
        return

    setHandlers: ->
        self = this
        ## Action on mouse move
        $("#map_wrapper").mousemove (e) ->
            clearTimeout(self.mouseTimer)
            self.hideTerritoryName()
            self.mouseTimer = setTimeout (->
                mpos = app.act.getMousePosition(e)
                self.showTerritoryName(mpos)
                return
            ), 300
            return
        $("#map_wrapper").mouseleave ->
            clearTimeout(self.mouseTimer)
            self.hideTerritoryName()
            return
        ## Action on map click
        $("#map_wrapper").click (e) ->
            app.act.click(e)
            return
        #: move menu clicks handlers
        $('.btn_m').click ->
            app.act.uiClick("move")
            return
        $('.btn_sm').click ->
            app.act.uiClick("sup_move")
            return
        $('.btn_sh').click ->
            app.act.uiClick("sup_hold")
            return
        $('.btn_c').click ->
            app.act.uiClick("convoy")
            return
        $('.btn_x').click ->
            app.act.uiClick("close")
            return
        #: build menu clicks handlers
        $('.btn_build_a').click ->
            app.act.uiClick("build_army")
            return
        $('.btn_build_f').click ->
            app.act.uiClick("build_fleet")
            return
        $('#btn_b_d').click ->
            app.act.uiClick("disband")
            return
        #: retreat menu clicks handlers
        $('#btn_r_r').click ->
            app.act.uiClick("retreat")
            return
        $('#btn_r_d').click ->
            app.act.uiClick("disband")
            return
        ## left menu handler
        $('#msg_button').click ->
            console.log('msg click')
            if self.menuStatus.left is "closed"
                self.openBar("left")
                self.menuStatus.left = "open"
            else
                self.closeBar("left")
                self.menuStatus.left = "closed"
            return
        $('#msg_ext_button').click ->
            console.log('msg ext click')
            if self.menuStatus.left is "open"
                self.extendBar("left")
                self.menuStatus.left = "extend"
            else
                self.compressBar("left")
                self.menuStatus.left = "open"
            return
        $('.msg_select_child').click ->
            country = this.id.split("_")[-1..][0]
            console.log(this.id)
            console.log(this.id.split("_"))
            self.openChat(country)
            return
        $('.msg_back').click ->
            country = this.parentNode.id.split("_")[-1..][0]
            self.closeChat(country)
            return
        ## right menu handler
        $('#ord_button').click ->
            console.log('ord click')
            if self.menuStatus.right is "closed"
                self.openBar("right")
                self.menuStatus.right = "open"
            else
                self.closeBar("right")
                self.menuStatus.right = "closed"
            return
        $('.ord_pin_head').click ->
            console.log('pin click from '+this.id)
            self.ordersClick(this.id)
            return
        ## top menu handler
        #$('#top_wrapper').mouseenter ->
        #    self.openTopMenu()
        #    return
        #$('#top_wrapper').mouseleave ->
        #    self.closeTopMenu()
        #    return
        $('#stats_button').click ->
            if self.statsBar is "closed"
                self.statsBar = "open"
                self.openStats()
            else
                self.statsBar = "closed"
                self.closeStats()
        $('#phase_rr').click ->
            buttoff = $('#phase_rr').hasClass 'disabled'
            if not buttoff
                newphase = 0
                app.game.loadPhase(newphase)
            return
        $('#phase_r').click ->
            console.log("phase_r click")
            buttoff = $('#phase_r').hasClass 'disabled'
            if not buttoff
                if app.game.phase().id is "next"
                    newphase = app.game._nphases-1
                else
                    newphase = app.game.phase().id - 1
                app.game.loadPhase(newphase)
            return
        $('#phase_f').click ->
            buttoff = $('#phase_f').hasClass 'disabled'
            if not buttoff
                if app.game.isLastPhase()
                    newphase = "next"
                else
                    newphase = app.game.phase().id + 1
                app.game.loadPhase(newphase)
            return
        $('#phase_ff').click ->
            buttoff = $('#phase_ff').hasClass 'disabled'
            if not buttoff
                if app.game.gotOrders()
                    newphase = "next"
                else
                    newphase = app.game._nphases-1
                app.game.loadPhase(newphase)
            return
        ## Pop-Up Multicoasts Menu clicks handlers
        $('.btn_mc_n').click ->
            app.act.mcClick("mc_n")
            return
        $('.btn_mc_s').click ->
            app.act.mcClick("mc_s")
            return
        return

    _componentToHex: (c) ->
        hex = c.toString(16)
        if hex.length == 1
            return "0"+hex
        return hex

    _rgbToHex: (r, g, b) ->
        "#" + @_componentToHex(r) + @_componentToHex(g) + @_componentToHex(b)

    _initMessagesDims: (country) ->
        toth = $('#msg_conv_'+country).innerHeight
        mbut = $($('#msg_conv_'+country).children()[0])
        mlist = $($('#msg_conv_'+country).children()[1])
        mtext = $($('#msg_conv_'+country).children()[2])
        mtext.css
            height: '100px'
        h = toth-mbut.height()-100-10
        mlist.css
            height: h+"px"
        return

    initMessages: ->
        if app.game.presstype isnt "none"
            $('#left_wrapper').removeClass('nulled')
            $('#msg_sel_global').removeClass('nulled')
            cid = $('#msg_conv_global').data('cid')
            @_initMessagesDims('global')
            app.net.getMessages(cid, 'global')
            if app.game.presstype is "all"
                for key, val of app.env.countries
                    if key is app.game.country
                        continue
                    color = @_rgbToHex(val.r, val.g, val.b)
                    $("#msg_sel_"+key).css
                        "box-shadow": "0 0 6px "+color
                        "border-color": color
                        "border-style": "solid"
                        "border-width": "1px"
                    $("#msg_sel_"+key).removeClass('nulled')
                    @_initMessagesDims(key)
                    cid = $('#msg_conv_'+key).data('cid')
                    app.net.getMessages(cid, key)
            setInterval(->
                app.ui.setMessagesRead()
            , 10000)
            #: refresh chats every 30s
            setInterval(->
                app.net.getMessages($('#msg_conv_global').data('cid'), 'global')
                if app.game.presstype is "all"
                    for key, val of app.env.countries
                        if key is app.game.country
                            continue
                        cid = $('#msg_conv_'+key).data('cid')
                        app.net.getMessages(cid, key)
            , 30000)
        return

    _initStatsChart: (country, color) ->
        ctx = document.getElementById('stats_'+country+'_canv').getContext('2d')
        n = 0
        for terr in app.game.phase().territories[country]
            if terr in app.env._supplylist
                n++
        data = [
            {value: n, color: color},
            {value: app.game.scsToWin-n, color: "transparent"}
        ]
        options =
            segmentShowStroke: false
        @_statsCharts[country] = new Chart(ctx).Doughnut(data, options)
        $('#stats_'+country+'_perc').html n
        if country is app.game.country
            $('#stats_c').html n+"/"+app.game.scsToWin
            $('#stats_dot').css
                'background-color': color
        return

    initStats: ->
        if preGame
            return
        $('#stats_wrapper').removeClass 'nulled'
        for key, val of app.env.countries
            color = @_rgbToHex(val.r, val.g, val.b)
            $('#stats_'+key+"_name").css
                color: color
            w = $($('#stats_'+key+"_canv").parent()).innerWidth()
            document.getElementById('stats_'+key+'_canv').width = w*0.7
            document.getElementById('stats_'+key+'_canv').height = w*0.7
            $('#stats_'+key+"_perc").css
                color: color
                width: w*0.7+"px"
                height: w*0.7+"px"
                top: -w*0.7+"px"
                'line-height': w*0.7+"px"
            $($('#stats_'+key+"_canv").parent()).css
                height: w*0.7+"px"
            @_initStatsChart(key, color)
        return

    hideLoader: ->
        $('#loader').animate
            opacity:'0'
            500
            'linear'
            ->
                $('#loader').remove()
                return
        if preGame
            @_preGame()
        return

    _preGame: ->
        $('#pregame').removeClass 'nulled'
        return

    setPhase: (id) ->
        $('#phase_ind').empty()
        if id isnt "next"
            #$('#phase_ind').append '<span>'+id+'/'+app.phase.id+'</span>'
            phase = app.game.phase(id)
            console.log(phase)
            if phase.type is "diplomacy"
                $('#phase_ind').append '<span>'+phase.season+' '+phase.year+'</span>'
            else
                if phase.year
                    $('#phase_ind').append '<span>'+phase.type+' '+phase.year+'</span>'
                else
                    $('#phase_ind').append '<span>'+phase.type+'</span'
        else
            $('#phase_ind').append '<span><em>Next</em></span>'
        @setPhaseStats(id)
        return

    setPhaseStats: (id) ->
        if preGame
            return
        #if id is "next"
        #    id = app.game._nextPhase.previous
        for country of app.env.countries
            n = 0
            if id isnt 0
                for terr in app.game.phase(id).territories[country]
                    if terr in app.env._supplylist
                        n++
            @_statsCharts[country].segments[0].value = n
            @_statsCharts[country].segments[1].value = app.game.scsToWin-n
            @_statsCharts[country].update()
            $('#stats_'+country+'_perc').html n
        return

    setOrdersPhase: (phase) ->
        #last = app.game.phase().id
        console.log(phase)
        #console.log(last)
        #if last isnt "next"
        #    last--
        if phase isnt "next"
            #last--
            phase--
        if phase is -1
            phase = 0
        console.log(phase)
        #console.log(last)
        ###
        $('#orders_'+last+' .ord_pin').each(
            ->
                console.log(this.id)
                app.OrdersPinClose('#'+this.id)
                return
        )
        ###
        #: off open phase
        $('.ord_phase_wrapper').each ->
            if $(this).hasClass('on')
                $(this).removeClass 'on'
                $(this).css
                    visibility: 'hidden'
            return
        if phase
            $('#ord_date').removeClass 'nulled'
            $('#noorders').addClass 'nulled'
            #$('#orders_'+last).css
            #    visibility: 'hidden'
            $('#orders_'+phase).addClass 'on'
            $('#orders_'+phase).css
                visibility: 'visible'
            if phase isnt "next"
                pphase = app.game._phases[phase]
                if pphase.id
                    s = "Resulting from "
                    if pphase.type is "diplomacy"
                        s += pphase.season+' '+pphase.year
                    else if pphase.type is "retreats"
                        s += 'retreats in '+pphase.season+' '+pphase.year
                    else
                        s += pphase.type+' '+pphase.year
                    $('#ord_date').html s
            else
                $('#ord_date').html 'For next phase'
        else
            $('#ord_date').addClass 'nulled'
            $('#noorders').removeClass 'nulled'
        ###
        $('#orders_'+phase+' .ord_pin').each(
            ->
                console.log(this.id)
                app.OrdersPinOpen('#'+this.id)
                return
        )
        ###

    _translatePosition: (pos) ->
        x = (pos.x) * 1/@zoom
        y = (pos.y) * 1/@zoom
        x = Math.round(x)
        y = Math.round(y)
        datapos = x: x, y: y

    _mousePosition: (pos) ->
        x = (pos.x) * @zoom
        y = (pos.y) * @zoom
        x = Math.round(x)
        y = Math.round(y)
        datapos = x: x, y: y

    showTerritoryName: (mpos) ->
        pos = @_translatePosition(mpos)
        refcolor = app.screen.getColor(pos)
        id = app.env.getTerritoryByColor(refcolor)
        if app.env.names[id]
            name = app.env.names[id]
            #m_x = mpos.x + 10
            m_x = mpos.x + $('#map_wrapper').offset().left - 10
            #m_y = mpos.y + 15
            m_y = mpos.y + $('#map_wrapper').offset().top - 15
            divid = "terr_name"
            div = '<div id="'+divid+'">'+name+'</div>'
            #$('#cont_wrapper').append div
            $('#main').append div
            $('#'+divid).css
                top: m_y+'px'
                left: m_x+'px'
                visibility: 'visible'
            $('#'+divid).animate
                opacity:'0.7'
                300
                'linear'
        return

    hideTerritoryName: ->
        if $('#terr_name').length != 0
            $('#terr_name').animate
                opacity:'0'
                300
                'linear'
                ->
                    $('#terr_name').remove()
        return

    setMenuButtons: (act, id) ->
        if act is "open"
            if app.game.phase().type is "diplomacy"
                if app.game.phase().canConvoy(id)
                    $('#btn_c').removeClass 'ninja'
                move = app.game.hasMove(id)
                if move
                    switch move
                        when "move"
                            $('#btn_m').addClass 'btn-primary'
                        when "sup_hold"
                            $('#btn_sh').addClass 'btn-primary'
                        when "sup_move"
                            $('#btn_sm').addClass 'btn-primary'
                        when "convoy"
                            $('#btn_c').addClass 'btn-primary'
            if app.game.phase().type is "builds"
                if id in app.game.phase().getCountryTroops()
                    build = app.game.hasBuild(id)
                    if build
                        $('#btn_b_d').addClass 'btn-primary'
                else
                    if app.env.isCoast(id)
                        $('#btn_b_f').removeClass 'ninja'
                    build = app.game.hasBuild(id)
                    if build
                        switch build
                            when "build_army"
                                $('#btn_b_a').addClass 'btn-primary'
                            when "build_fleet"
                                $('#btn_b_f').addClass 'btn-primary'
            if app.game.phase().type is "retreats"
                move = app.game.hasMove(id)
                if move
                    $('#btn_r_r').addClass 'btn-primary'
                else
                    $('#btn_r_d').addClass 'btn-primary'
        else if act is "close"
            if app.game.phase().type is "diplomacy"
                $('#btn_c').addClass 'ninja'
            if app.game.phase().type is "builds"
                $('#btn_b_f').addClass 'ninja'
        else if act is "reset"
            if app.game.phase().type is "diplomacy"
                for bid in ["btn_m", "btn_sh", "btn_sm", "btn_c"]
                    $('#'+bid).removeClass 'btn-primary'
            else if app.game.phase().type is "retreats"
                $('#btn_r_r').removeClass 'btn-primary'
                $('#btn_r_d').removeClass 'btn-primary'
            else
                $('#btn_b_a').removeClass 'btn-primary'
                $('#btn_b_f').removeClass 'btn-primary'
                $('#btn_b_d').removeClass 'btn-primary'
        return

    setTopButtons: (act, dis) ->
        if act is "enable"
            $('#phase_r').removeClass 'disabled'
            $('#phase_rr').removeClass 'disabled'
            $('#phase_f').removeClass 'disabled'
            $('#phase_ff').removeClass 'disabled'
        else
            if dis is "f"
                $('#phase_f').addClass 'disabled'
                $('#phase_ff').addClass 'disabled'
            else
                $('#phase_r').addClass 'disabled'
                $('#phase_rr').addClass 'disabled'
        return

    openMenu: (mpos) ->
        ## load buttons state
        m_x = mpos.x - 40
        m_y = mpos.y - 60
        if app.game.phase().type is "diplomacy"
            menu_id = "#terr_menu"
        if app.game.phase().type is "builds"
            pos = @_translatePosition(mpos)
            refcolor = app.screen.getColor(pos)
            tid = app.env.getTerritoryByColor(refcolor)
            if tid in app.game.phase().getCountryTroops()
                menu_id = "build_menu_d"
            else
                menu_id = "#build_menu"
        if app.game.phase().type is "retreats"
            menu_id = "#retreat_menu"
        $(menu_id).css
            top: m_y+'px'
            left: m_x+'px'
            visibility: 'visible'
        $(menu_id).animate
            opacity:'1'
            500
            'linear'
        $(menu_id).addClass 'menuopened'
        return

    closeMenu: ->
        @setMenuButtons("close", false)
        menu = $('.menuopened')[0]
        #if app.game.phase().type is "diplomacy"
        #    menu_id = "#terr_menu"
        #if app.game.phase().type is "builds"
        #    menu_id = "#build_menu"
        #if app.game.phase().type is "retreats"
        #    menu_id = "#retreat_menu"
        $(menu).animate
            opacity:'0'
            500
            'linear'
        $(menu).css visibility: 'hidden'
        return

    openMCMenu: (pos) ->
        mpos = @_mousePosition(pos)
        ## load buttons state
        m_x = mpos.x - 40
        m_y = mpos.y - 60
        $('#mcoast_menu').css
            top: m_y+'px'
            left: m_x+'px'
            visibility: 'visible'
        $('#mcoast_menu').animate
            opacity:'1'
            500
            'linear'
        return

    closeMCMenu: ->
        $('#mcoast_menu').animate
            opacity:'0'
            500
            'linear'
        $('#mcoast_menu').css visibility: 'hidden'
        return

    openTopMenu: ->
        #if @statsBar is "closed"
        $('#top_wrapper').stop()
        $('#top_wrapper').animate
            top: '0px'
            300
            'linear'
        return

    closeTopMenu: ->
        #if @statsBar is "closed"
        $('#top_wrapper').stop()
        $('#top_wrapper').animate
            top: '-40px'
            300
            'linear'
        return

    openStats: ->
        #$('#stats_wrapper').stop()
        #$('#stats_wrapper').css
        #    top: '-50%'
        $('#stats_wrapper').animate
            bottom: '0px'
            500
            'linear'
        #$('#top_wrapper').animate
        #    top: '50%'
        #    500
        #    'linear'
        return

    closeStats: ->
        #$('#stats_wrapper').stop()
        $('#stats_wrapper').animate
            bottom: '-50%'
            500
            'linear'
        return

    openBar: (side) ->
        self = this
        @barsOpened += 1
        val = 1 - 0.18*@barsOpened
        newzoom = @w*val/app.screen.img.width
        @zoom = newzoom
        switch side
            when "left"
                $('#left_wrapper').animate
                    #left: '0px'
                    left: '-20%'
                    300
                    'linear'
                $('#cont_wrapper').animate
                    #width: '83%'
                    width: (100-17*self.barsOpened)+'%'
                    #height: app.screen.img.height*newzoom
                    left: '17%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.screen.img.height*self.zoom
                    300
                    'linear'
            when "right"
                $('#right_wrapper').animate
                    right: '0px'
                    300
                    'linear'
                $('#cont_wrapper').animate
                    #width: '83%'
                    width: (100-17*self.barsOpened)+'%'
                    #height: app.screen.img.height*newzoom
                    right: '17%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.screen.img.height*self.zoom
                    300
                    'linear'
        $('.menu_butt').each(
            ->
                c_off = $(this).offset().top
                c_top = c_off+$('#cont_wrapper').scrollTop()
                console.log(c_top)
                console.log(app.screen.img.height*self.zoom)
                if c_top >= (app.screen.img.height*self.zoom-40)
                    $(this).offset
                        top: c_off*self.zoom
                c_off = $(this).offset().left
                c_left = c_off+$('#cont_wrapper').scrollLeft()
                if c_left >= (app.screen.img.width*self.zoom-40)
                    $(this).offset
                        left: c_off*self.zoom
                return
        )
        return

    extendBar: (side) ->
        switch side
            when "left"
                $('#left_wrapper').animate
                    #left: '0px'
                    left: '0%'
                    300
                    'linear'
                $('#msg_content').animate
                    left: '2%'
                    width: '96%'
                    300
                    'linear'
        return

    compressBar: (side) ->
        switch side
            when "left"
                $('#left_wrapper').animate
                    #left: '0px'
                    left: '-20%'
                    300
                    'linear'
                $('#msg_content').animate
                    left: '54%'
                    width: '46%'
                    300
                    'linear'
        return

    closeBar: (side) ->
        self = this
        @barsOpened -= 1
        val = 1 - 0.18*@barsOpened
        newzoom = @w*val/app.screen.img.width
        @zoom = newzoom
        switch side
            when "left"
                $('#left_wrapper').animate
                    left: '-38%'
                    300
                    'linear'
                    ->
                        $('#msg_content').css
                            left: '54%'
                            width: '46%'
                        return
                $('#cont_wrapper').animate
                    #width: '100%'
                    width: (100-17*self.barsOpened)+'%'
                    #height: app.screen.img.height*app.page.zoom
                    left: '0%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.screen.img.height*self.zoom
                    300
                    'linear'
            when "right"
                $('#right_wrapper').animate
                    right: '-18%'
                    300
                    'linear'
                $('#cont_wrapper').animate
                    #width: '100%'
                    width: (100-17*self.barsOpened)+'%'
                    #height: app.screen.img.height*self.zoom
                    right: '0%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.screen.img.height*self.zoom
                    300
                    'linear'
        return

    buildOrders: ->
        ## TODO: implement other steps filling
        if app.game.phase().id
            pphase = app.game.phase().previous()
            for id, data of app.game.orders
                order_str = @_buildOrderString(id, data)
                $('#orders_next_me_data').append '<div class="order" id="ord_next_'+id+'">'+order_str+'</div>'
            @ordersClick("orders_next_me_head")
            #for i in [1..app.phase.orders.length-1]
            for phase, pdata of app.game._phases
                if phase not in ["0", app.game.phase().id+""]
                    #$('#ord_wrapper').append '<div class="ord_phase_wrapper" id="orders_'+phase+'"></div>'
                    for country, orders of pdata.orders
                        for id, data of orders
                            order_str = @_buildOrderString(id, data)
                            $('#orders_'+phase+'_'+country+'_data').append '<div class="order" id="ord_'+phase+'_'+id+'">'+order_str+'</div>'
                    @ordersClick("orders_"+phase+"_"+app.game.country+"_head")
            #$('#orders_next').css
            #   visibility: 'visible'
            $('#readyorders').css
                'line-height': ($('#orders_next').height()-12)+"px"
            p = if app.game.phase().id isnt "next" then app.game.phase().id-1 else "next"
            $('#orders_'+p).addClass 'on'
            $('#orders_'+p).css
                visibility: 'visible'
        else
            $('#noorders').removeClass 'nulled'
        return

    _buildOrderString: (id, data) ->
        order_str = app.env.names[id]+' '+data.type
        if data.type isnt "hold"
            if data.type is "move"
                order_str += ' to '+app.env.names[data.to]
                if data.viaConvoy
                    order_str += ' via convoy'
                if data.mc isnt undefined
                    if data.mc is 0
                        order_str += ' north coast'
                    else
                        order_str += ' south coast'
            else if data.type is "build_army"
                order_str = "build a new army in " + app.env.names[id]
            else if data.type is "build_fleet"
                order_str = "build a new fleet in " + app.env.names[id]
            else
                order_str += ' from '+app.env.names[data.from]+' to '+app.env.names[data.to]
        return order_str

    addOrder: (id, data) ->
        order_str = @_buildOrderString(id, data)
        $('#ord_next_'+id).html order_str
        #@autoSave()
        return

    delOrder: (id) ->
        $('#ord_'+id).remove()
        #@autoSave()
        return

    ordersClick: (id) ->
        ## id finish with _head
        sid = id.split("_")
        sid.pop()
        pid = '#'+sid.join("_")
        closed = $(pid+"_text").hasClass 'ord_pin_text_off'
        if closed
            @ordersOpen(pid)
        else
            @ordersClose(pid)

    ordersOpen: (id) ->
        $(id+'_text').removeClass 'ord_pin_text_off'
        $(id+'_text').addClass 'ord_pin_text_on'
        $($(id+'_icon').children()[0]).removeClass 'fa-caret-right'
        $($(id+'_icon').children()[0]).addClass 'fa-caret-down'
        #$(id+'_icon').addClass 'ord_pin_icon_on'
        new_height = $(id+'_data').height()+20
        $(id).animate
            height: new_height
            200
            ->
                $(id).css
                    height: 'auto'
                return
        $(id+'_data').animate
            #visibility: 'visible'
            opacity: 1
            200

    ordersClose: (id) ->
        $(id+'_data').animate
            #visibility: 'hidden'
            opacity: 0
            200
        $(id).animate
            height: 20
            200
        $(id+'_text').removeClass('ord_pin_text_on')
        $(id+'_text').addClass('ord_pin_text_off')
        #$(id+'_icon').removeClass('ord_pin_icon_on')
        #$(id+'_icon').addClass('ord_pin_icon_off')
        $($(id+'_icon').children()[0]).removeClass 'fa-caret-down'
        $($(id+'_icon').children()[0]).addClass 'fa-caret-right'

    openChat: (country) ->
        console.log(country)
        $('#msg_conv_'+country).removeClass('ninja')
        $('.msg_select').animate
            opacity: 0
            200
        $('#msg_conv_'+country).animate
            opacity: 1
            200
        $('.msg_select').addClass('ninja')
        return

    closeChat: (country) ->
        $('.msg_select').removeClass('ninja')
        $('#msg_conv_'+country).animate
            opacity: 0
            200
        $('.msg_select').animate
            opacity: 1
            200
        $('#msg_conv_'+country).addClass('ninja')
        return

    autoSave: ->
        @iconOff('ord')
        @iconOn('save')
        clearTimeout(@saveTimer)
        self = this
        @saveTimer = setTimeout (->
            app.net.postOrders()
            return
        ), 3000
        return

    saveOrders: ->
        if $('#icon_save').hasClass('off') or $('#icon_save').hasClass('light')
            return
        if @isSaving
            return
        console.log('manually saving orders')
        clearTimeout(@saveTimer)
        app.net.postOrders()
        return

    saving: ->
        @isSaving = true
        @iconOff('ready')
        $('#readyorders').addClass 'nulled'
        $('#icon_save').removeClass 'fa-save'
        $('#icon_save').removeClass 'fa-border'
        @iconSpin('save')
        $('#icon_ord').removeClass 'fa-check-square-o'
        @iconSpin('ord')
        #$('#icon_ord').css
        #    color: '#000'
        return

    saved: (data) ->
        @iconUnspin('save')
        $('#icon_save').addClass 'fa-save'
        $('#icon_save').addClass 'fa-border'
        @iconUnspin('ord')
        $('#icon_ord').addClass 'fa-check-square-o'
        @iconLight('save')
        @iconOn('ready')
        $('#readyorders').addClass 'nulled'
        @isSaving = false
        return

    iconSpin: (id) ->
        @iconOn(id)
        $('#icon_'+id).addClass 'fa-spinner fa-spin'
        return

    iconUnspin: (id) ->
        $('#icon_'+id).removeClass 'fa-spin'
        $('#icon_'+id).removeClass 'fa-spinner'
        return

    iconOff: (id) ->
        $('#icon_'+id).removeClass 'light'
        $('#icon_'+id).removeClass 'on'
        $('#icon_'+id).addClass 'off'
        return

    iconOn: (id) ->
        $('#icon_'+id).removeClass 'light'
        $('#icon_'+id).removeClass 'off'
        $('#icon_'+id).addClass 'on'
        return

    iconLight: (id) ->
        $('#icon_'+id).removeClass 'on'
        $('#icon_'+id).removeClass 'off'
        $('#icon_'+id).addClass 'light'
        return

    setReady: ->
        if $('#icon_ready').hasClass('off')
            return
        if @isSettingReady
            return
        @isSettingReady = true
        $('#icon_ready').removeClass 'fa-check'
        $('#icon_ready').removeClass 'fa-border'
        isReady = $('#icon_ready').hasClass('light')
        @iconSpin('ready')
        console.log(isReady)
        if isReady
            app.net.setUnready()
        else
            app.net.setReady()
        return

    didReady: (isReady) ->
        app.game.ready = isReady
        console.log(isReady)
        @iconUnspin('ready')
        $('#icon_ready').addClass 'fa-check'
        $('#icon_ready').addClass 'fa-border'
        if isReady
            @iconLight('ready')
            @iconLight('ord')
            $('#readyorders').removeClass 'nulled'
        else
            @iconOn('ready')
            $('#readyorders').addClass 'nulled'
            if not $('#icon_ord').hasClass('off')
                @iconOn('ord')
        @iconOff('save')
        @isSettingReady = false
        return

    _renderMessage: (country, text, from, date, read) ->
        isauthor = from is app.game.country
        head = if not read and not isauthor then '<div class="msg_el unread">' else '<div class="msg_el">'
        rdiv = if not read and not isauthor then '<div class="dotunread"></div>' else '<div class="dotunread nulled"></div>'
        ddiv = '<div class="msg_date">'+date+'</div>'
        cdiv = '<div class="row msg_row">'
        if isauthor
            cdiv += '<div class="col-md-2">'
            cdiv += '<div class="msg_from is_me pull-left">'+from.charAt(0).toUpperCase()+'</div>'
            cdiv += '</div>'
            cdiv += '<div class="msg_me col-md-10">'+text+'</div>'
        else
            cdiv += '<div class="msg_re col-md-10">'+rdiv+text+'</div>'
            cdiv += '<div class="col-md-2">'
            cdiv += '<div class="msg_from pull-right">'+from.charAt(0).toUpperCase()+'</div>'
            cdiv += '</div>'
        cdiv += '</div>'
        foot = '</div>'
        return head+ddiv+cdiv+foot

    gotMessages: (country, data) ->
        chat = $($('#msg_conv_'+country).children()[1])
        for m in data
            #: read
            if country is "global"
                read = app.game.country in m.read
            else
                read = m.read
            chat.append(@_renderMessage(country, m.text, m.from, m.timeref, read))
        open_msgs = chat.children()
        for msg in open_msgs
            if msg.classList.contains("unread")
                unread = msg
                break
        if unread
            chat.scrollTop($(unread).offset().top)
            #: enlight messages and chat icons if unread
            $('#msg_sel_'+country).addClass "light"
            $($('#msg_button').children[0]).addClass "light"
        return

    setMessagesRead: ->
        allRead = true
        $(".msg_list").each (i, list) ->
            if $($(list).parent()).hasClass("ninja")
                return
            chatRead = true
            size = $(list).scrollTop() + $(list).height()
            cid = $($(list).parent()).data("cid")
            isglob = $($(list).parent()).attr("id").split("_")[last] is "global"
            $(list).children().each (j, el) ->
                if $(el).hasClass("unread")
                    chatRead = false
                    if $(el).offset().top < size
                        $(el).removeClass("unread")
                        $(el).find(".dotunread").addClass("nulled")
                        app.net.setRead(cid, j, isglob)
                return
            if chatRead
                country = $($(list).parent()).attr("id").split("_")[last]
                $('#msg_sel_'+country).removeClass 'light'
            else
                allRead = false
            return
        if allRead
            $($('#msg_button').children()[0]).removeClass 'light'
        return

    sendMessage: (country, cid) ->
        text = $('#msg_text_'+country).val()
        app.net.postMessage(cid, text)
        chat = $($('#msg_conv_'+country).children()[1])
        # update next line with real date
        chat.append(@_renderMessage(country, text, app.game.country, 'now', false))
        $('#msg_text_'+country).val ''
        return

    win: ->
        $('#win').html "Game won by "+app.game.win
        return

window.UI = UI
