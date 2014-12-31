###
#           nuDiplomacy interface
#
#   This is the code responsible of handling
#   nuDiplomacy interface.
#
#   This is just awesome.
#   /gi0baro
#
###

window.app =
    # -- GLOBAL VARS DEF --
    page:
        w: 0
        h: 0
        zoom: 0
        scroll:
            x: 0
            y: 0
        img: ''
        menu_status:
            left: "closed"
            right: "closed"
        mouse_timer: null
        bars_open: 0
        stats_bar: "closed"
    ## Canvas legend:
    ##  - ref: reference map png file
    ##  - base: to set terr colors
    ##  - ov: for supply centers dots
    ##  - arms: for armies
    ##  - arws: for arrows
    ##  - res: to draw the final canvas composed of layers from previous
    canv:
        img: ''
        ref:
            layer: ''
            ctx: ''
            pix: ''
            pixdata: ''
        base:
            layer: ''
            ctx: ''
            pix: ''
            pixdata: ''
        ov:
            layer: ''
            ctx: ''
        arms:
            layer: ''
            ctx: ''
        arws:
            layer: ''
            ctx: ''
        res:
            layer: ''
            ctx: ''
        img_army: ''
        img_fleet: ''
    play:
        action: "none"
        active_terr: "none"
        track_terrs: []
        track_convoy: {}
        track_cterrs: []
        moves: {}
        moves_mc: {}
        orders: {}
    ## next vars are for map data
    map:
        ## --- map globals
        ## ---- terr id and color
        colors: ''
        ## ---- pixels of terrs
        pix: {}
        ## ---- allowed movements
        moves:
            armies: ''
            fleets: ''
            mc: ''
        ## ---- coord ref for armies
        oxy: ''
        ## ---- game countries
        countries: ''
        ## ---- starting countries terrs
        countries_init: ''
        ## --- map terrs type
        neutrals: ''
        seas: ''
        coasts: ''
        mcoasts: ''
        mcoasts_oxy: ''
        same: ''
        ## --- map suppl centers
        supply: ''
        ## --- map names
        names: ''
        ## --- terr current colors obj
        colors_now: {}
        ## --- current showing phase
        phase:
            id: ''
            ## type could be "spring", "autumn", "retreats", "builds", "pre-game"
            type: ''
            year: ''
        ## --- current view map data
        ## ---- country terrs
        countries_terr: ''
        ## ---- armies details
        troops: {}
        armies_lst: []
        fleets_lst: []
        ## ---- current positions on multi-coasts terrs
        mc_pos: {}
        ## ---- currents movements
        moves_last: {}
        moves_last_mc: {}
        ## ---- dislodged
        dislodged: {}
    phase:
        ## --- current phase
        id: ''
        step: 0
        ## --- phases data
        type: {}
        year: {}
        season: {}
        countries_terr: {}
        troops: {}
        mc_pos: {}
        moves: {}
        moves_mc: {}
        dislodged: {}
        orders: {}


    ## -- PAGE execution
    ## maybe we want to use $(window).load() ??
    #$(document).ready ->
    Start: ->
        #app.ShowLoader()
        app.GetMapVars()
        ## we load also the previous phase for correctly drawing arrows
        #if app.phase.id > 1
        #   app.GetPhaseVars(app.phase.id-1)
        #app.GetPhaseVars(app.phase.id)
        app.GetGameVars()
        app.GetPhaseVars(app.phase.id)
        app.GetOrders()
        app.GetMessages()
        app.PreInit()
        ## wait till it's loaded and redraw it into canvas (still neither canvas nor img are displayed)
        app.canv.img.onload = ->
            app.Init()
            app.TopPhase(app.phase.id)
            app.HideLoader()
            return
        return

    ShowLoader: ->
        loader = '<div id="loader"><div id="loader_cont"><h1>Loading..</h1></div></div>'
        $('#main').append loader
        $('#loader').css
            opacity: '1'
        return

    HideLoader: ->
        $('#loader').animate
            opacity:'0'
            500
            'linear'
            ->
                $('#loader').remove()
                return
        return


    ## -- INIT functions --
    GetMapVars: ->
        ## map data
        $.ajax 'jsdata/map_data.json',
            type: 'GET'
            async: false
            success: (data) ->
                app.map.colors = data.colors
                app.map.moves.armies = data.nears_a
                app.map.moves.fleets = data.nears_f
                app.map.moves.mc = data.nears_mc
                app.map.oxy = data.oxy
                app.map.neutrals = data.neutrals
                app.map.same = data.same
                app.map.seas = data.seas
                app.map.coasts = data.coasts
                #app.map.mcoasts
                app.map.mcoasts_oxy = data.mcoasts
                console.log(data.mcoasts)
                app.map.supply = data.supply
                app.map.names = data.names
                app.map.countries = data.countries
                app.map.countries_init = data.countries_init
                #app.phase.year["0"] = data.year
                #app.phase.type["0"] = "pre-game"
                app.map.mcoasts = (key for key of app.map.mcoasts_oxy)
                return
        ## game data
        ###
        $.ajax 'jsdata/game_data.json',
            type: 'GET'
            async: false
            success: (data) ->
                app.play.country = data.curr_play
                app.phase.id = data.curr_phase
                return
        ###
        console.log(app.map)
        return

    GetGameVars: (step=0) ->
        ## game data
        phases = []
        console.log("load game data step "+step+" from json")
        $.ajax 'jsdata/game_data_'+step+'.json',
            type: 'GET'
            async: false
            success: (data) ->
                app.play.country = data.curr_play
                app.phase.id = data.curr_phase
                phases = data.phases
                return
            error: (request, status, error) ->
                #console.log(request.responseText)
                console.log(status)
                console.log(error)
                return
        #console.log(app.map)
        count = app.phase.id-(phases.length-1)
        console.log(count)
        pstr = count+''
        for phase in phases
            app.phase.type[pstr] = phase.type
            app.phase.year[pstr] = phase.year
            app.phase.season[pstr] = phase.season
            app.phase.countries_terr[pstr] = phase.terrs
            app.phase.troops[pstr] = phase.troops or {}
            app.phase.mc_pos[pstr] = phase.mc_pos or {}
            app.phase.moves[pstr] = phase.moves or {}
            app.phase.moves_mc[pstr] = phase.moves_mc or {}
            app.phase.dislodged[pstr] = phase.dislodged or {}
            app.phase.orders[pstr] = phase.orders or {}
            ## generate map movements
            ###
            for country, orders of phase.orders
                for id, odata of orders
                    if odata['type'] isnt 'hold'
                        app.phase.moves
            ###
            count++
            pstr = count+''
        app.play.orders = app.phase.orders[app.phase.id][app.play.country]
        return

    GetPhaseVars: (phase) ->
        ## this will need a modification for db itnerface!!
        ## get data if not present
        console.log(phase)
        if phase
            if not app.phase.countries_terr[phase]
                app.play.step++
                app.GetGameVars(app.play.step)
                ###
                console.log("load phase "+phase+" from json")
                phasefile = 'jsdata/phase_'+phase+'.json'
                $.ajax phasefile,
                    type: 'GET'
                    async: false
                    success: (data) ->
                        console.log(data)
                        app.phase.countries_terr[phase] = data.terrs
                        app.phase.troops[phase] = data.troops
                        app.phase.mc_pos[phase] = data.mc_pos
                        app.phase.moves[phase] = data.moves
                        app.phase.moves_mc[phase] = data.moves_mc
                        app.phase.type[phase] = data.phase.type
                        app.phase.year[phase] = data.phase.year
                        app.phase.dislodged[phase] = data.dislodged or {}
                        app.phase.orders[phase] = data.orders
                        return
                    error: (request, status, error) ->
                        #console.log(request.responseText)
                        console.log(status)
                        console.log(error)
                        return
            ###
            #console.log(app.phase)
            ## load data in map obj
            app.map.countries_terr = app.phase.countries_terr[phase]
            for key, value of app.map.countries_terr
                for i of value
                    app.map.countries_terr[key][i] = value[i]+''
            app.map.troops = app.phase.troops[phase]
            app.map.mc_pos = app.phase.mc_pos[phase]
            ## generate last phase movements
            app.map.moves_last = {}
            app.map.moves_last_mc = {}
            if phase-1
                for country, orders of app.phase.orders[phase-1]
                    for id, odata of orders
                        if odata.type isnt "hold"
                            w = odata
                            w.from = odata.from or id
                            app.map.moves_last[id] = w
                            ## TODO: use only moves_last
                            if w.mc isnt undefined
                                app.map.moves_last_mc[id] = w.mc
            #app.map.moves_last = app.phase.moves[phase]
            #app.map.moves_last_mc = app.phase.moves_mc[phase]
            ## build armies and fleets lists
            app.map.troops_lst = []
            app.map.fleets_lst = []
            for key, value of app.map.troops
                for t, l of value
                    for i in l
                        if t is "armies"
                            app.map.troops_lst.push(i)
                        else
                            app.map.fleets_lst.push(i)
            app.map.dislodged = app.phase.dislodged[phase]
            #app.play.orders = app.phase.orders[phase][app.play.country]
        else
            #app.map.countries_terr = app.map.countries_init
            app.map.countries_terr = app.phase.countries_terr[phase]
            app.map.troops = {}
            app.map.mc_pos = {}
            app.map.moves_last = {}
            app.map.moves_last_mc = {}
            app.map.troops_lst = []
            app.map.fleets_lst = []
            app.map.dislodged = {}
        app.map.phase.id = phase
        app.map.phase.type = app.phase.type[phase]
        app.map.phase.year = app.phase.year[phase]
        ## TEMP
        #for key of app.map.troops[app.play.country]
        #   app.play.orders[key] = type: "hold"
        return

    GetOrders: ->
        ## TODO: implement other steps filling
        if app.phase.id
            $('#ord_wrapper').append '''
                <div class="ord_phase_wrapper" id="orders_next">
                    <div class="ord_pin" id="orders_next_me">
                        <div class="ord_pin_head" id="orders_next_me_head">
                            <div class="ord_pin_icon ord_pin_icon_off" id="orders_next_me_icon"></div>
                            <div class="ord_pin_text ord_pin_text_off" id="orders_next_me_text">
                                My orders
                            </div>
                        </div>
                        <div class="orders" id="orders_next_me_data"></div>
                    </div>
                </div>'''
            for id, data of app.play.orders
                order_str = app.BuildOrderStr(id, data)
                $('#orders_next_me_data').append '<div class="order" id="ord_next_'+id+'">'+order_str+'</div>'
            app.OrdersPinClick("orders_next_me_head")
            #for i in [1..app.phase.orders.length-1]
            for phase, pdata of app.phase.orders
                if phase not in ["0", app.phase.id+""]
                    $('#ord_wrapper').append '<div class="ord_phase_wrapper" id="orders_'+phase+'"></div>'
                    #$('#ord_wrapper').append '<div class="orders" id="orders_'+phase+'"></div>'
                    for country, orders of pdata
                        $('#orders_'+phase).append(
                            '<div class="ord_pin" id="orders_'+phase+'_'+country+'">
                            <div class="ord_pin_head" id="orders_'+phase+'_'+country+'_head">
                                    <div class="ord_pin_icon ord_pin_icon_off" id="orders_'+phase+'_'+country+'_icon"></div>
                                    <div class="ord_pin_text ord_pin_text_off" id="orders_'+phase+'_'+country+'_text">
                                        '+country+' orders
                                    </div>
                                </div>
                                <div class="orders" id="orders_'+phase+'_'+country+'_data"></div>
                            </div>'
                        )
                        #$('#orders_'+phase).append '<div class="orders_sub" id="orders_sub_'+phase+'_'+country+'"></div>'
                        for id, data of orders
                            order_str = app.BuildOrderStr(id, data)
                            $('#orders_'+phase+'_'+country+'_data').append '<div class="order" id="ord_'+phase+'_'+id+'">'+order_str+'</div>'
                    app.OrdersPinClick("orders_"+phase+"_"+app.play.country+"_head")
        #$('#orders_next').css
        #   visibility: 'visible'
        p = app.phase.id-1
        $('#orders_'+p).css
            visibility: 'visible'

    GetMessages: ->
        $(".msg_select").append '<div class="msg_select_child" id="msg_select_GLOBAL"></div>'
        $("#msg_select_GLOBAL").css
            "box-shadow": "0 0 5px #000"
            "-webkit-box-shadow": "0 0 5px #000"
            "border-color": "#000"
            "border-style": "solid"
            "border-width": "1px"
        for key, val of app.map.countries
            color = app.rgbToHex(val.r, val.g, val.b)
            $(".msg_select").append '<div class="msg_select_child" id="msg_select_'+key+'"></div>'
            $("#msg_select_"+key).css
                "box-shadow": "0 0 5px "+color
                "border-color": color
                "border-style": "solid"
                "border-width": "1px"
            $("#msg_content").append(
                '<div id="msg_conv_'+key+'" class="msg_conv ninja">
                    <div class="msg_back">back</div>
                    <div class="msg_list">
                        <div id="msg_msg_1" class="msg_me">Test msg 1</div>
                        <div id="msg_msg_2" class="msg_re">Test msg 2</div>
                    </div>
                    <textarea id="msg_text_'+key+'" class="msg_text"></textarea>
                </div>'
            )
        return

    BuildPixArr: ->
        filter = (list, color) ->
            #x for x in [0..list.length-1] when (list[x].r is color[0] and list[x].g is color[1] and list[x].b is color[2])
            l = []
            for x in [0..list.length-1]
                if list[x].r is color[0]
                    if list[x].g is color[1]
                        if list[x].b is color[2]
                            l.push(x)
            return l
        ## build an array of objects for pixs
        pixa = []
        j = 0
        time_start = new Date().getTime()
        for i in [0..app.canv.ref.pixdata.length-1] by 4
            pixa[j] = r: app.canv.ref.pixdata[i], g: app.canv.ref.pixdata[i+1], b: app.canv.ref.pixdata[i+2]
            j += 1
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("1time "+time_ex)
        time_start = new Date().getTime()
        for key, color of app.map.colors
            app.map.pix[key] = filter(pixa, color)
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("2time "+time_ex)
        return

    BuildPixArr2: ->
        filter = (obj, color) ->
            #x for x, val of obj when (val[0] is color.r and val[1] is color.g and val[2] is color.b)
            for x, val of obj
                if val[0] is color.r and val[1] is color.g and val[2] is color.b
                    return x
            return null
        pixa = []
        j = 0
        for i in [0..app.canv.ref.pixdata.length-1] by 4
            pixa[j] = r: app.canv.ref.pixdata[i], g: app.canv.ref.pixdata[i+1], b: app.canv.ref.pixdata[i+2]
            j += 1
        for key of app.map.colors
            #console.log(key)
            app.map.pix[key] = []
        j = 0
        for pix in pixa
            #color = key for key, val of app.map.colors when (val[0] is pix.r and val[1] is pix.g and val[2] is pix.b)
            color = filter(app.map.colors, pix)
            if color isnt null
                app.map.pix[color].push(j)
            j += 1
        return

    PreInit: ->
        ## load page image
        app.page.img = document.getElementById("map_img")
        ## create canvas
        app.canv.ref.layer = document.createElement("canvas")
        app.canv.base.layer = document.createElement("canvas")
        app.canv.ov.layer = document.createElement("canvas")
        app.canv.arms.layer = document.createElement("canvas")
        app.canv.arws.layer = document.createElement("canvas")
        app.canv.res.layer = document.createElement("canvas")
        ## create a ref img
        app.canv.img = document.createElement("img")
        app.canv.img.src = "map.png"
        #app.canv.img_army = document.createElement("img")
        app.canv.img_army = document.getElementById("army_img")
        app.canv.img_fleet = document.getElementById("ship_img")
        #app.canv.img_army.src = "tank.png"
        #app.canv.img_army.onload = ->
        #   console.log("army loaded")
        return

    SetOverflow: ->
        ## we need to evaluate screen size because of the zoom eval (seems that the scroll bars make width wrong when overflow is auto)
        i_ch_h = app.canv.img.height
        console.log(i_ch_h)
        console.log($(window).height())
        if i_ch_h > $(window).height()
            $('#cont_wrapper').css 'overflow-y': 'scroll'
        else
            $('#cont_wrapper').css 'overflow-y': 'hidden'
        return

    SetTopMenuPos: ->
        ww = $(window).width()
        mw = $('#top_wrapper').width()
        per = (((ww/2)-(mw/2))/ww)*100
        $('#top_wrapper').css 'left': per+'%'
        $('#top_sensor').css 'left': per+'%'

    EvalZoom: (screen_w, screen_h, img_w, img_h) ->
        console.log(screen_w)
        console.log(img_w)
        app.page.zoom = screen_w/img_w
        console.log(app.page.zoom)
        return

    GetPageDim: ->
        app.page.w = $("#map_wrapper").width()
        app.page.h = $("#map_wrapper").height()

    ## useless??
    EvalScroll: ->
        app.page.scroll.x = document.getElementById('map_wrapper').scrollTop
        app.page.scroll.y = document.getElementById('map_wrapper').scrollLeft
        return

    GetEventPos: (e) ->
        if not e.hasOwnProperty('offsetX')
            e.offsetX = e.layerX
        if not e.hasOwnProperty('offsetY')
            e.offsetY = e.layerY
        pos = x: e.offsetX, y: e.offsetY

    SetEventHandlers: ->
        ## Action on mouse move
        $("#map_wrapper").mousemove (e) ->
            clearTimeout(app.page.mouse_timer)
            app.HideTerrName()
            app.page.mouse_timer = setTimeout (->
                mpos = app.GetEventPos(e)
                pos = app.GetPos(mpos, app.canv.img, app.page.w, app.page.h)
                app.LoadTerrName(mpos, pos)
                return
            ), 300
            return
        $("#map_wrapper").mouseleave ->
            clearTimeout(app.page.mouse_timer)
            app.HideTerrName()
            return
        ## Action on map click
        $("#map_wrapper").click (e) ->
            mpos = app.GetEventPos(e)
            app.page.cur_mpos = mpos
            pos = app.GetPos(mpos, app.canv.img, app.page.w, app.page.h)
            app.Action(mpos, pos, app.page.img)
            return
        ## Pop-Up Menu clicks handlers
        $('.btn_m').click ->
            console.log('move click')
            app.ClickEvent("move")
            return
        $('.btn_sm').click ->
            console.log('sm click')
            app.ClickEvent("sup_move")
            return
        $('.btn_sh').click ->
            console.log('sh click')
            app.ClickEvent("sup_hold")
            return
        $('.btn_c').click ->
            console.log('c click')
            app.ClickEvent("convoy")
            return
        $('.btn_x').click ->
            console.log('move click')
            app.ClickEvent("close")
            return
        ## left menu handler
        $('#msg_button').click ->
            console.log('msg click')
            if app.page.menu_status.left is "closed"
                app.OpenBar("left")
                app.page.menu_status.left = "open"
            else
                app.CloseBar("left")
                app.page.menu_status.left = "closed"
            return
        $('#msg_ext_button').click ->
            console.log('msg ext click')
            if app.page.menu_status.left is "open"
                app.ExtendBar("left")
                app.page.menu_status.left = "extend"
            else
                app.CompressBar("left")
                app.page.menu_status.left = "open"
            return
        $('.msg_select_child').click ->
            app.ChatLoad(this.id)
            return
        $('.msg_back').click ->
            app.ChatBack(this.parentNode.id)
            return
        ## right menu handler
        $('#ord_button').click ->
            console.log('ord click')
            if app.page.menu_status.right is "closed"
                app.OpenBar("right")
                app.page.menu_status.right = "open"
            else
                app.CloseBar("right")
                app.page.menu_status.right = "closed"
            return
        $('.ord_pin_head').click ->
            console.log('pin click from '+this.id)
            app.OrdersPinClick(this.id)
            return
        ## top menu handler
        $('#top_wrapper').mouseenter ->
            app.OpenTopMenu()
            return
        $('#top_wrapper').mouseleave ->
            app.CloseTopMenu()
            return
        $('#top_menu_stats').click ->
            if app.page.stats_bar is "closed"
                app.page.stats_bar = "open"
                app.OpenStats()
            else
                app.page.stats_bar = "closed"
                app.CloseStats()
        $('#phase_rr').click ->
            buttoff = $('#phase_rr').hasClass 'disabled'
            if not buttoff
                newphase = 0
                app.LoadPhase(newphase)
            return
        $('#phase_r').click ->
            console.log("phase_r click")
            buttoff = $('#phase_r').hasClass 'disabled'
            if not buttoff
                if app.map.phase.id is "next"
                    newphase = app.phase.id
                else
                    newphase = app.map.phase.id - 1
                app.LoadPhase(newphase)
            return
        $('#phase_f').click ->
            buttoff = $('#phase_f').hasClass 'disabled'
            if not buttoff
                if app.map.phase.id is app.phase.id
                    newphase = "next"
                else
                    newphase = app.map.phase.id + 1
                app.LoadPhase(newphase)
            return
        $('#phase_ff').click ->
            buttoff = $('#phase_ff').hasClass 'disabled'
            if not buttoff
                if app.TheresOrders()
                    newphase = "next"
                else
                    newphase = app.phase.id
                app.LoadPhase(newphase)
            return
        ## Pop-Up Multicoasts Menu clicks handlers
        $('.btn_mc_n').click ->
            app.MCClick("mc_n")
            return
        $('.btn_mc_s').click ->
            app.MCClick("mc_s")
            return
        return

    Init: ->
        ## set canvas size
        app.canv.ref.layer.width = app.canv.img.width
        app.canv.ref.layer.height = app.canv.img.height
        app.canv.base.layer.width = app.canv.img.width
        app.canv.base.layer.height = app.canv.img.height
        app.canv.ov.layer.width = app.canv.img.width
        app.canv.ov.layer.height = app.canv.img.height
        app.canv.arms.layer.width = app.canv.img.width
        app.canv.arms.layer.height = app.canv.img.height
        app.canv.arws.layer.width = app.canv.img.width
        app.canv.arws.layer.height = app.canv.img.height
        app.canv.res.layer.width = app.canv.img.width
        app.canv.res.layer.height = app.canv.img.height
        ## set some props
        app.SetOverflow()
        app.SetTopMenuPos()
        app.GetPageDim()
        console.log(app.page.w)
        console.log(app.page.h)
        app.EvalZoom(app.page.w, app.page.h, app.canv.img.width, app.canv.img.height)
        ## set canvas contexts
        app.canv.ref.ctx = app.canv.ref.layer.getContext('2d')
        app.canv.base.ctx = app.canv.base.layer.getContext('2d')
        app.canv.ov.ctx = app.canv.ov.layer.getContext('2d')
        app.canv.arms.ctx = app.canv.arms.layer.getContext('2d')
        app.canv.arws.ctx = app.canv.arws.layer.getContext('2d')
        app.canv.res.ctx = app.canv.res.layer.getContext('2d')
        ## draw ref image in base and ref canvas
        app.canv.base.ctx.drawImage(app.canv.img, 0, 0)
        app.canv.ref.ctx.drawImage(app.canv.img, 0, 0)
        ## init pixel datas
        app.GetMapData()
        ## init the pixel array (we don't load it from json anymore)
        app.BuildPixArr()
        ## draw the current map in canvas
        app.SetMap()
        ## show the map
        $("#map_img").css
            opacity: "1"
            height: app.canv.ref.layer.height*app.page.zoom+"px"
        ## set events handlers
        app.SetEventHandlers()
        return


    ## -- MAP functions --
    GetMapData: ->
        ## --- this initialize canvas pixel data
        app.canv.base.pix = app.canv.base.ctx.getImageData(0,0,app.canv.base.layer.width,app.canv.base.layer.height)
        app.canv.ref.pix = app.canv.ref.ctx.getImageData(0,0,app.canv.base.layer.width,app.canv.base.layer.height)
        app.canv.base.pixdata = app.canv.base.pix.data
        app.canv.ref.pixdata = app.canv.ref.pix.data
        return

    UpdateMap: ->
        ## --- this update the rendered image in page
        app.canv.base.ctx.putImageData(app.canv.base.pix,0,0)
        app.canv.res.ctx.drawImage(app.canv.base.layer,0,0)
        app.canv.res.ctx.drawImage(app.canv.ov.layer,0,0)
        app.canv.res.ctx.drawImage(app.canv.arws.layer,0,0)
        app.canv.res.ctx.drawImage(app.canv.arms.layer,0,0)
        ##img.src = app.canv.base.layer.toDataURL()
        app.page.img.src = app.canv.res.layer.toDataURL()
        return

    LoadMapColors: ->
        ## draw all terrs to ground color
        color = r: 226, g: 198, b: 158
        for i of app.map.colors
            app.map.colors_now[i] = color
        ## draw neutrals
        color = r: 0, g: 0, b: 0
        for i in app.map.neutrals
            app.map.colors_now[i] = color
        ## draw seas
        color = r: 197, g: 223, b: 234
        for i in app.map.seas
            app.map.colors_now[i] = color
        ## draw countries terrs
        for key, color of app.map.countries
            for i in app.map.countries_terr[key]
                app.map.colors_now[i] = color
        return

    UpdMapColors: (grounds) ->
        ## draw all terrs to ground color
        color = r: 226, g: 198, b: 158
        for i in grounds
            app.map.colors_now[i] = color
        ## draw countries terrs
        for key, color of app.map.countries
            for i in app.map.countries_terr[key]
                app.map.colors_now[i] = color
        return

    SetMap: ->
        ## --- this re-color the map based on the reference object for colors
        time_start = new Date().getTime()
        app.LoadMapColors()
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("LoadMapColors time "+time_ex)
        time_start = new Date().getTime()
        for key, color of app.map.colors_now
            app.ColorTerr(key, color)
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("ColorTerr for time "+time_ex)
        time_start = new Date().getTime()
        app.DrawSPL()
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("DrawSPL time "+time_ex)
        time_start = new Date().getTime()
        app.DrawArmies()
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("DrawArmies time "+time_ex)
        time_start = new Date().getTime()
        app.DrawLines()
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("DrawLines time "+time_ex)
        time_start = new Date().getTime()
        app.UpdateMap()
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("UpdateMap time "+time_ex)
        return

    ChangeMap: (old_c_terrs, old_tcolors) ->
        DiffColor = (color1, color2) ->
            return !(color1.r is color2.r and color1.g is color2.g and color1.b is color2.b)
        ## --- this re-color the map based on the reference object for colors
        time_start = new Date().getTime()
        c_terrs = []
        for key, terr_list of app.map.countries_terr
            for terr in terr_list
                c_terrs.push(terr)
        c_diff_list = old_c_terrs.filter (x) -> x not in c_terrs
        app.UpdMapColors(c_diff_list)
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("LoadMapColors time "+time_ex)
        time_start = new Date().getTime()
        ## color diff country terrs only
        c_diff_list = []
        for key, color of app.map.colors_now
            if DiffColor(old_tcolors[key], color)
                c_diff_list.push(key)
        for terr in c_diff_list
            app.ColorTerr(terr, app.map.colors_now[terr])
        time_end = new Date().getTime()
        time_ex = time_end - time_start
        console.log("ColorTerr for time "+time_ex)
        app.DrawSPL()
        app.DrawArmies()
        app.DrawLines()
        app.UpdateMap()
        return

    DrawSPL: ->
        ## --- this draw the supply centers dots
        for key, value of app.map.supply
            x = value.x
            y = value.y
            radius = 5
            startangle = 0
            endangle = Math.PI*2
            app.canv.ov.ctx.beginPath()
            app.canv.ov.ctx.arc(x,y,radius,startangle,endangle,true)
            #app.canv.ov.ctx.closePath()
            app.canv.ov.ctx.fillStyle= "#000000"
            app.canv.ov.ctx.fill()
            radius = 4
            app.canv.ov.ctx.beginPath()
            app.canv.ov.ctx.arc(x,y,radius,startangle,endangle,true)
            #app.canv.ov.ctx.closePath()
            app.canv.ov.ctx.fillStyle= "#FFFFFF"
            app.canv.ov.ctx.fill()
            radius = 2.5
            app.canv.ov.ctx.beginPath()
            app.canv.ov.ctx.arc(x,y,radius,startangle,endangle,true)
            #app.canv.ov.ctx.closePath()
            app.canv.ov.ctx.fillStyle= "#000000"
            app.canv.ov.ctx.fill()
        return

    DrawArmies: ->
        app.ClearARMMap()
        for country, troops of app.map.troops
            for type, tlist of troops
                for id in tlist
                    if type is "fleets" and app.IsMCoast(id)
                        mc_pos = app.map.mc_pos[id]
                        x = app.map.mcoasts_oxy[id][mc_pos].x
                        y = app.map.mcoasts_oxy[id][mc_pos].y
                    else
                        x = app.map.oxy[id].x
                        y = app.map.oxy[id].y
                    console.log(x+' '+y)
                    ## check if country color is different from the army country
                    console.log(country)
                    if country isnt app.GetCountryByTerr(id)
                        ## draw color square under the army
                        ccolor = app.map.countries[country]
                        app.canv.arms.ctx.beginPath()
                        app.canv.arms.ctx.rect(x-8, y-16, 16, 16)
                        app.canv.arms.ctx.lineWidth = 1
                        app.canv.arms.ctx.fillStyle = 'rgb('+ccolor.r+','+ccolor.g+','+ccolor.b+')'
                        app.canv.arms.ctx.fill()
                        app.canv.arms.ctx.strokeStyle = 'black'
                        app.canv.arms.ctx.stroke()
                    if type is "armies"
                        app.canv.arms.ctx.drawImage(app.canv.img_army, x-15, y-9, 29, 17)
                    else
                        app.canv.arms.ctx.drawImage(app.canv.img_fleet, x-13, y-11, 25, 22)
                    ## dislodgement circle
                    if app.map.dislodged[country]
                        console.log(app.map.dislodged[country])
                        if id in app.map.dislodged[country]
                            console.log("dislodge circle draw..")
                            app.canv.arms.ctx.beginPath()
                            app.canv.arms.ctx.arc(x, y, 22, 0, Math.PI*2, true)
                            #app.canv.arms.ctx.closePath()
                            app.canv.arms.ctx.lineWidth = 2
                            app.canv.arms.ctx.strokeStyle = 'rgb(255,127,0)'
                            app.canv.arms.ctx.stroke()
        return

    DrawLines: ->
        app.ClearARWMap()
        for id, obj of app.map.moves_last
            app.NewLine("past", obj.type, id, obj.from, obj.to, obj.success or false)
        if app.map.phase.id is "next"
            for id, obj of app.play.moves
                app.NewLine("future", obj.type, id, obj.from, obj.to)
        return

    NewLine: (time, act, id, f_id, t_id, success=true) ->
        DrawLine = (x, y, x_t, y_t, color, success)->
            app.canv.arws.ctx.beginPath()
            if not success
                app.canv.arws.ctx.setLineDash([5])
            else
                app.canv.arws.ctx.setLineDash([0])
            app.canv.arws.ctx.moveTo(x, y)
            app.canv.arws.ctx.lineTo(x_t, y_t)
            #app.canv.arws.ctx.closePath()
            app.canv.arws.ctx.strokeStyle = color
            app.canv.arws.ctx.stroke()
            return
        DrawCircle = (x, y, r, color) ->
            app.canv.arws.ctx.beginPath()
            app.canv.arws.ctx.arc(x, y, r, 0, Math.PI*2, true)
            #app.canv.arws.ctx.closePath()
            app.canv.arws.ctx.strokeStyle = color
            app.canv.arws.ctx.stroke()
            return
        DrawTriangle = (angle, headlen, x, y, color) ->
            app.canv.arws.ctx.beginPath()
            app.canv.arws.ctx.moveTo(x,y)
            app.canv.arws.ctx.lineTo(x-headlen*Math.cos(angle-Math.PI/6),y-headlen*Math.sin(angle-Math.PI/6))
            app.canv.arws.ctx.lineTo(x-headlen*Math.cos(angle+Math.PI/6),y-headlen*Math.sin(angle+Math.PI/6))
            app.canv.arws.ctx.closePath()
            app.canv.arws.ctx.fillStyle = color
            app.canv.arws.ctx.fill()
            return
        SupMoveEPoint = (p0, p1, p2) ->
            slen = 50
            angle = Math.atan2(p2.y-p1.y,p2.x-p1.x)
            x_f1 = Math.round(p1.x-slen*Math.cos(angle+Math.PI/2))
            y_f1 = Math.round(p1.y-slen*Math.sin(angle+Math.PI/2))
            x_f2 = Math.round(p1.x-slen*Math.cos(angle-Math.PI/2))
            y_f2 = Math.round(p1.y-slen*Math.sin(angle-Math.PI/2))
            pt0 = new Point2D(x_f1, y_f1)
            pt1 = new Point2D(x_f2, y_f2)
            intersect = Intersection.intersectCircleLine(p1, 10, pt0, pt1)
            pt0 = new Point2D(Math.round(intersect.points[0].x), Math.round(intersect.points[0].y))
            pt1 = new Point2D(Math.round(intersect.points[1].x), Math.round(intersect.points[1].y))
            d1 = Math.sqrt(Math.pow(p0.x-pt0.x,2)+Math.pow(p0.y-pt0.y,2))
            d2 = Math.sqrt(Math.pow(p0.x-pt1.x,2)+Math.pow(p0.y-pt1.y,2))
            if d1 >= d2
                x_f = pt1.x
                y_f = pt1.y
            else
                x_f = pt0.x
                y_f = pt0.y
            p3 = new Point2D(x_f, y_f)
            #slen = 50
            #angle = Math.atan2(p2.y-p1.y,p2.x-p1.x)
            x_f1 = Math.round(p2.x-slen*Math.cos(angle+Math.PI/2))
            y_f1 = Math.round(p2.y-slen*Math.sin(angle+Math.PI/2))
            x_f2 = Math.round(p2.x-slen*Math.cos(angle-Math.PI/2))
            y_f2 = Math.round(p2.y-slen*Math.sin(angle-Math.PI/2))
            pt0 = new Point2D(x_f1, y_f1)
            pt1 = new Point2D(x_f2, y_f2)
            intersect = Intersection.intersectCircleLine(p2, 10, pt0, pt1)
            pt0 = new Point2D(Math.round(intersect.points[0].x), Math.round(intersect.points[0].y))
            pt1 = new Point2D(Math.round(intersect.points[1].x), Math.round(intersect.points[1].y))
            d1 = Math.sqrt(Math.pow(p0.x-pt0.x,2)+Math.pow(p0.y-pt0.y,2))
            d2 = Math.sqrt(Math.pow(p0.x-pt1.x,2)+Math.pow(p0.y-pt1.y,2))
            if d1 >= d2
                x_f = pt1.x
                y_f = pt1.y
            else
                x_f = pt0.x
                y_f = pt0.y
            p4 = new Point2D(x_f, y_f)
            intersect = Intersection.intersectCircleLine(p2, 18, p1, p2)
            p5 = new Point2D(Math.round(intersect.points[0].x), Math.round(intersect.points[0].y))
            #slen = 100
            x_f1 = Math.round(p5.x-slen*Math.cos(angle+Math.PI/2))
            y_f1 = Math.round(p5.y-slen*Math.sin(angle+Math.PI/2))
            x_f2 = Math.round(p5.x-slen*Math.cos(angle-Math.PI/2))
            y_f2 = Math.round(p5.y-slen*Math.sin(angle-Math.PI/2))
            pt0 = new Point2D(x_f1, y_f1)
            pt1 = new Point2D(x_f2, y_f2)
            intersect = Intersection.intersectLineLine(p3, p4, pt0, pt1)
            p6 = new Point2D(Math.round(intersect.points[0].x), Math.round(intersect.points[0].y))
            x_m = Math.round((p3.x+p6.x)/2)
            y_m = Math.round((p3.y+p6.y)/2)
            p7 = new Point2D(x_m, y_m)
            return {angle: angle, p0: p7, p1: p6}

        country_troops = app.GetCountryTroops(app.play.country)
        console.log(country_troops)
        if time is "past"
            mc_pos_data = app.phase.mc_pos[app.phase.id-1]
            console.log(mc_pos_data)
            mc_move_data = app.map.moves_last_mc
            Fleet = (id) ->
                app.WasFleet(id)
        else
            mc_pos_data = app.map.mc_pos
            mc_move_data = app.play.moves_mc
            Fleet = (id) ->
                app.IsFleet(id)
            #if id not in (key for key of app.map.troops[app.play.country])
            if id not in country_troops
                success = false

        switch act
            when "move"
                if Fleet(f_id) and app.IsMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.map.mcoasts_oxy[f_id][mc_pos].x, app.map.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.map.oxy[f_id].x, app.map.oxy[f_id].y)
                if Fleet(f_id) and app.IsMCoast(t_id)
                    #if f_id in (key for key of app.map.troops[app.play.country])
                    ##if f_id in country_troops
                    mc_pos = mc_move_data[f_id]
                    p2 = new Point2D(app.map.mcoasts_oxy[t_id][mc_pos].x, app.map.mcoasts_oxy[t_id][mc_pos].y)
                    ##else
                    ##  p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                else
                    p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                #p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                intersect = Intersection.intersectCircleLine(p2, 18, p1, p2)
                #intersect1 = Intersection.intersectCircleLine(app.map.oxy[f_id], 10, p1, p2)
                x = p1.x
                y = p1.y
                x_t = intersect.points[0].x
                y_t = intersect.points[0].y
                if time is "past" and app.map.phase.id is "next"
                    color = "#7F7F7F"
                else
                    color = "#FF0000"
                DrawLine(x, y, x_t, y_t, color, success)
                angle = Math.atan2(y_t-y,x_t-x)
                DrawTriangle(angle, 10, x_t, y_t, color)
            when "sup_hold"
                if Fleet(f_id) and app.IsMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.map.mcoasts_oxy[f_id][mc_pos].x, app.map.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.map.oxy[f_id].x, app.map.oxy[f_id].y)
                p1 = new Point2D(app.map.oxy[f_id].x, app.map.oxy[f_id].y)
                if Fleet(t_id) and app.IsMCoast(t_id)
                    mc_pos = mc_pos_data[t_id]
                    p2 = new Point2D(app.map.mcoasts_oxy[t_id][mc_pos].x, app.map.mcoasts_oxy[t_id][mc_pos].y)
                else
                    p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                #p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                intersect = Intersection.intersectCircleLine(p2, 18, p1, p2)
                x = p1.x
                y = p1.y
                x_t = intersect.points[0].x
                y_t = intersect.points[0].y
                angle = Math.atan2(y_t-y,x_t-x)
                if time is "past" and app.map.phase.id is "next"
                    color = "#7F7F7F"
                else
                    color = "#00FF00"
                DrawLine(x, y, x_t, y_t, color, success)
                DrawTriangle(angle, 10, x_t, y_t, color)
                #x_t = app.map.oxy[t_id].x
                #y_t = app.map.oxy[t_id].y
                x_t = p2.x
                y_t = p2.y
                DrawCircle(x_t, y_t, 18, color)
            when "sup_move"
                if Fleet(id) and app.IsMCoast(id)
                    mc_pos = mc_pos_data[id]
                    p0 = new Point2D(app.map.mcoasts_oxy[id][mc_pos].x, app.map.mcoasts_oxy[id][mc_pos].y)
                else
                    p0 = new Point2D(app.map.oxy[id].x, app.map.oxy[id].y)
                if Fleet(f_id) and app.IsMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.map.mcoasts_oxy[f_id][mc_pos].x, app.map.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.map.oxy[f_id].x, app.map.oxy[f_id].y)
                if Fleet(f_id) and app.IsMCoast(t_id)
                    #if f_id in (key for key of app.map.troops[app.play.country])
                    if f_id in country_troops
                        mc_pos = mc_move_data[f_id]
                        p2 = new Point2D(app.map.mcoasts_oxy[t_id][mc_pos].x, app.map.mcoasts_oxy[t_id][mc_pos].y)
                    else
                        p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                else
                    p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                res = SupMoveEPoint(p0, p1, p2)
                p3 = res.p0
                p4 = res.p1
                angle = res.angle
                if time is "past" and app.map.phase.id is "next"
                    color = "#7F7F7F"
                else
                    color = "#FFFF00"
                DrawLine(p0.x, p0.y, p3.x, p3.y, color, success)
                DrawLine(p3.x, p3.y, p4.x, p4.y, color, success)
                DrawTriangle(angle, 10, p4.x, p4.y, color)
            when "convoy"
                p0 = new Point2D(app.map.oxy[id].x, app.map.oxy[id].y)
                p1 = new Point2D(app.map.oxy[f_id].x, app.map.oxy[f_id].y)
                p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                res = SupMoveEPoint(p0, p1, p2)
                p3 = res.p0
                p4 = res.p1
                angle = res.angle
                if time is "past" and app.map.phase.id is "next"
                    color = "#7F7F7F"
                else
                    color = "#0000FF"
                DrawLine(p0.x, p0.y, p3.x, p3.y, color, success)
                DrawLine(p3.x, p3.y, p4.x, p4.y, color, success)
                DrawTriangle(angle, 10, p4.x, p4.y, color)
            when "retreat"
                if Fleet(f_id) and app.IsMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.map.mcoasts_oxy[f_id][mc_pos].x, app.map.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.map.oxy[f_id].x, app.map.oxy[f_id].y)
                if Fleet(f_id) and app.IsMCoast(t_id)
                    mc_pos = mc_move_data[f_id]
                    p2 = new Point2D(app.map.mcoasts_oxy[t_id][mc_pos].x, app.map.mcoasts_oxy[t_id][mc_pos].y)
                else
                    p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                #p2 = new Point2D(app.map.oxy[t_id].x, app.map.oxy[t_id].y)
                intersect = Intersection.intersectCircleLine(p2, 22, p1, p2)
                #intersect1 = Intersection.intersectCircleLine(app.map.oxy[f_id], 10, p1, p2)
                x = p1.x
                y = p1.y
                x_t = intersect.points[0].x
                y_t = intersect.points[0].y
                if time is "past" and app.map.phase.id is "next"
                    color = "#7F7F7F"
                else
                    color = "#FF7F00"
                DrawLine(x, y, x_t, y_t, color, success)
                angle = Math.atan2(y_t-y,x_t-x)
                DrawTriangle(angle, 10, x_t, y_t, color)
        return

    ClearOVMap: ->
        app.canv.ov.ctx.clearRect(0,0,app.canv.ov.layer.width,app.canv.ov.layer.height)
        return

    ClearARMMap: ->
        app.canv.arms.ctx.clearRect(0,0,app.canv.arms.layer.width,app.canv.arms.layer.height)
        return

    ClearARWMap: ->
        app.canv.arws.ctx.clearRect(0,0,app.canv.ov.layer.width,app.canv.ov.layer.height)
        return


    ###
    -- GLOBAL utility functions
    ###
    GetPos: (pos, img, wind_w, wind_h) ->
        ## -- This get the position on the image coordinate sys. from the mouse coord.
        ##EvalScroll();
        ## refer position to real img size
        ##console.log(e.offsetY);
        ##console.log(e.offsetX);
        ## get coordinates in img oxy
        ##var x = e.offsetX * img.width / wind_w;
        ##var y = e.offsetY * img.height / wind_h;
        x = (pos.x) * 1/app.page.zoom
        y = (pos.y) * 1/app.page.zoom
        x = Math.round(x)
        y = Math.round(y)
        datapos = x: x, y: y

    GetPagePos: (pos) ->
        x = pos.x * app.page.zoom
        y = pos.y * app.page.zoom
        x = Math.round(x)
        y = Math.round(y)
        datapos = x: x, y: y

    GetColor: (pos) ->
        ## -- This get the real image color from the given position
        ##var map = ctx.getImageData(0,0,canvas.width,canvas.height);
        console.log(pos.x)
        console.log(pos.y)
        s_map = app.canv.ref.ctx.getImageData(pos.x,pos.y,1,1)
        ##var color = imdata[pos];
        color = s_map.data
        res_color = r: color[0], g: color[1], b: color[2]
        ##console.log(color)
        ##return res_color;

    GetTerrId: (color) ->
        ## -- This get the territory id from color
        for key, value of app.map.colors
            db_color = r: value[0], g: value[1], b: value[2]
            if db_color.r is color.r and db_color.g is color.g and db_color.b is color.b
                Id = key
                break
        return Id

    ValidColor: (color) ->
        ## -- This check that the color is not black
        res = false
        if color.r > 20 or color.g > 20 or color.b > 20
            res = true
        return res

    ColorTerr: (id, color) ->
        ## -- This color the terr in the base canvas
        get_pix = app.map.pix[id]
        for p in [0..get_pix.length]
            app.canv.base.pixdata[get_pix[p]*4] = color.r
            app.canv.base.pixdata[get_pix[p]*4+1] = color.g
            app.canv.base.pixdata[get_pix[p]*4+2] = color.b
        return

    GetCountryByTerr: (id) ->
        for country, list of app.map.countries_terr
            if id in list
                console.log(country)
                return country
        return false

    IsSame: (id) ->
        return id in (key for key of app.map.same)

    IsArmy: (id) ->
        return id in app.map.troops_lst

    IsFleet: (id) ->
        return id in app.map.fleets_lst

    WasArmy: (id) ->
        list = []
        for key, value of app.phase.troops[app.phase.id-1]
            for i in value["armies"]
                list.push(i)
        return id in list

    WasFleet: (id) ->
        list = []
        for key, value of app.phase.troops[app.phase.id-1]
            for i in value["fleets"]
                list.push(i)
        return id in list

    IsSea: (id) ->
        return id in app.map.seas

    IsCoast: (id) ->
        return id in app.map.coasts

    IsMCoast: (id) ->
        return id in app.map.mcoasts

    CanConvoy: (id) ->
        res = false
        if app.IsFleet(id) and app.IsSea(id)
            nears = app.map.moves.fleets[id]
            for i in nears
                if app.IsArmy(i)
                    res = true
                    break
        return res

    ActionPresent: (id) ->
        movement = app.play.moves[id]
        if movement
            return movement.type
        return false

    TheresOrders: ->
        return !jQuery.isEmptyObject(app.play.moves)

    GetCountryTroops: (country) ->
        troops = []
        for ttype, tlist of app.map.troops[app.play.country]
            for troop in tlist
                troops.push(troop)
        return troops

    LoadPhase: (id, drawl=true) ->
        console.log("LoadPhase called")
        console.log(drawl)
        reset_map = true
        old_tcolors = {}
        old_c_terrs = []
        app.OrdersMenuPhase(id)
        if id is "next" and app.map.phase.id is app.phase.id
            reset_map = false
        else
            for key, value of app.map.colors_now
                old_tcolors[key] = value
            for key, terr_list of app.map.countries_terr
                for terr in terr_list
                    old_c_terrs.push(terr)
            time_start = new Date().getTime()
            if id is "next"
                app.GetPhaseVars(app.phase.id)
            else
                app.GetPhaseVars(id)
            time_end = new Date().getTime()
            time_ex = time_end - time_start
            console.log("GetPhaseVars time "+time_ex)
        app.TopButtons("enable", false)
        if id is 0
            app.TopButtons("disable", "r")
        else if id is app.phase.id
            if not app.TheresOrders()
                app.TopButtons("disable", "f")
        else if id is "next"
            app.TopButtons("disable", "f")
        #else
        #   app.TopButtons("enable", false)
        app.TopPhase(id)
        app.map.phase.id = id
        if reset_map
            time_start = new Date().getTime()
            #app.SetMap()
            app.ChangeMap(old_c_terrs, old_tcolors)
            time_end = new Date().getTime()
            time_ex = time_end - time_start
            console.log("ChangeMap time "+time_ex)
        else
            if drawl
                time_start = new Date().getTime()
                app.DrawLines()
                time_end = new Date().getTime()
                time_ex = time_end - time_start
                console.log("DrawLines time "+time_ex)
                app.UpdateMap()
        return


    TerrOn: (id) ->
        #var r,g,b,rr,gg,bb;
        #ccolor = r: 250, g: 0, b: 0
        ocolor = app.map.colors_now[id]
        ncolor = r: ocolor.r-50, g: ocolor.g-50, b: ocolor.b-50
        app.ColorTerr(id, ncolor)
        return

    TerrOff: (id) ->
        ccolor = r: app.map.colors_now[id].r, g: app.map.colors_now[id].g, b: app.map.colors_now[id].b
        app.ColorTerr(id, ccolor)
        return

    Terr_Track_Off: ->
        for i in app.play.track_terrs
            ccolor = r: app.map.colors_now[i].r, g: app.map.colors_now[i].g, b: app.map.colors_now[i].b
            app.ColorTerr(i, ccolor)
        app.play.track_terrs = []
        app.play.track_convoy = {}
        app.play.track_cterrs = []
        return

    Terr_MoveTo_On: (id) ->
        nears = app.AvailMoveList("move", id)
        nears_c = app.AvailMoveList("move_convoy", id)
        for i in nears
            app.play.track_terrs.push(i)
            #ocolor = app.map.colors_now[i]
            #ncolor = r: ocolor.r+30, g: ocolor.g+30, b: ocolor.b+30
            ncolor = r: 235, g: 0, b: 0
            app.ColorTerr(i, ncolor)
        for i in nears_c
            if i not in app.play.track_terrs
                app.play.track_terrs.push(i)
                ncolor = r: 0, g: 0, b: 235
                app.ColorTerr(i, ncolor)
        #app.play.track_convoy = nears_c
        return

    Terr_SupHold_On: (id) ->
        app.play.track_terrs = app.AvailMoveList("sup_hold", id)
        for i in app.play.track_terrs
            #ocolor = app.map.colors_now[i]
            #ncolor = r: ocolor.r+30, g: ocolor.g+30, b: ocolor.b+30
            ncolor = r: 0, g: 235, b: 0
            app.ColorTerr(i, ncolor)
        return

    Terr_SupMove_To_On: (id) ->
        ## deactivate past colored terrs
        for i in app.play.track_terrs
            if i isnt id
                ccolor = r: app.map.colors_now[i].r, g: app.map.colors_now[i].g, b: app.map.colors_now[i].b
                app.ColorTerr(i, ccolor)
        app.play.track_terrs = [id]
        ## activate new terrs
        nears = app.AvailMoveList("sup_move_to", id)
        for i in nears
            app.play.track_terrs.push(i)
        console.log(app.play.track_terrs)
        for i in app.play.track_terrs
            if i isnt id
                #ocolor = app.map.colors_now[i]
                ncolor = r: 235, g: 0, b: 0
                app.ColorTerr(i, ncolor)
        return

    Terr_SupMove_From_On: (id) ->
        app.play.track_terrs = app.AvailMoveList("sup_move_from", id)
        console.log(app.play.track_terrs)
        for i in app.play.track_terrs
            #ocolor = app.map.colors_now[i]
            #ncolor = r: ocolor.r+30, g: ocolor.g+30, b: ocolor.b+30
            ncolor = r: 235, g: 235, b: 0
            app.ColorTerr(i, ncolor)
        return

    Terr_Convoy_From_On: (id) ->
        app.play.track_terrs = app.AvailMoveList("convoy_from", id)
        for i in app.play.track_terrs
            ncolor = r: 0, g: 0, b: 235
            app.ColorTerr(i, ncolor)
        return

    Terr_Convoy_To_On: (id) ->
        nears_s = app.AvailMoveList("convoy_to_fleet", id)
        nears_t = app.AvailMoveList("convoy_to_terr", id)
        id_f = app.play.track_terrs[0]
        #moves_f = app.map.moves.armies[id_f]
        for i in nears_s
            app.play.track_terrs.push(i)
            ncolor = r: 0, g: 0, b: 235
            app.ColorTerr(i, ncolor)
        for i in nears_t
            if i isnt id_f
                #if i not in moves_f
                app.play.track_terrs.push(i)
                ncolor = r: 235, g: 0, b: 0
                app.ColorTerr(i, ncolor)
        console.log(app.play.track_terrs)
        return


    AvailMoveList: (act, id_f) ->
        nears_res = []
        switch act
            when "move"
                if app.IsArmy(id_f)
                    nears_res = app.map.moves.armies[id_f]
                else
                    ## check multicoasts
                    if app.IsMCoast(id_f)
                        mc_pos = app.map.mc_pos[id_f]
                        nears_res = app.map.moves.mc[id_f][mc_pos]
                    else
                        nears_res = app.map.moves.fleets[id_f]
            when "move_convoy"
                if app.IsFleet(id_f)
                    nears_res = []
                else
                    nears_o = app.map.moves.armies[id_f]
                    nears = app.map.moves.fleets[id_f]
                    nears_s = {}
                    if nears
                        for i in nears
                            if app.IsFleet(i) and app.IsSea(i)
                                nears_s[i] = 1
                    console.log(nears_s)
                    console.log(jQuery.isEmptyObject(nears_s))
                    if jQuery.isEmptyObject(nears_s)
                        done = true
                    else
                        done = false
                    console.log(done)
                    while not done
                        found = false
                        for key, value of nears_s
                            nears_t = app.map.moves.fleets[key]
                            #found = false
                            for j in nears_t
                                if j not in (key for key of nears_s)
                                    if app.IsFleet(j) and app.IsSea(j)
                                        nears_s[j] = value + 1
                                        console.log(nears_s)
                                        found = true
                                        break
                            if found
                                break
                        if not found
                            done = true
                    console.log(nears_s)
                    for key of nears_s
                        nears_t = app.map.moves.fleets[key]
                        for j in nears_t
                            if j isnt id_f
                                if j not in nears_o
                                    #if j not in app.map.seas
                                    if not app.IsSea(j)
                                        if j not in nears_res
                                            nears_res.push(j)
                    app.play.track_convoy = nears_s
                    app.play.track_cterrs = nears_res
            when "sup_hold"
                if app.IsArmy(id_f)
                    nears = app.map.moves.armies[id_f]
                else
                    nears = app.map.moves.fleets[id_f]
                for i in nears
                    if i in app.map.troops_lst or i in app.map.fleets_lst
                        nears_res.push(i)
            when "sup_move_to"
                nears_o = []
                nears_f = []
                id_o = app.play.active_terr
                if app.IsArmy(id_o)
                    nears_o = app.map.moves.armies[id_o]
                else
                    nears_o = app.map.moves.fleets[id_o]
                console.log(id_f)
                if app.IsArmy(id_f)
                    nears_f = app.map.moves.armies[id_f]
                else
                    nears_f = app.map.moves.fleets[id_f]
                console.log(nears_f)
                nears = []
                for i in nears_o
                    if i not in nears
                        nears.push(i)
                for i in nears_f
                    if i isnt id_o
                        if i not in nears
                            nears.push(i)
                for i in nears
                    if i isnt id_f
                        if i in nears_o and i in nears_f
                            nears_res.push(i)
                ## get convoyable to terrs if is army
                nears_s = {}
                if app.IsArmy(id_f)
                    if app.map.moves.fleets[id_f]
                        for i in app.map.moves.fleets[id_f]
                            if app.IsFleet(i) and app.IsSea(i)
                                nears_s[i] = 1
                console.log(nears_s)
                console.log(jQuery.isEmptyObject(nears_s))
                done = jQuery.isEmptyObject(nears_s)
                console.log(done)
                while not done
                    found = false
                    for key, value of nears_s
                        nears_t = app.map.moves.fleets[key]
                        #found = false
                        for j in nears_t
                            if j not in (key for key of nears_s)
                                if app.IsFleet(j) and app.IsSea(j)
                                    nears_s[j] = value + 1
                                    console.log(nears_s)
                                    found = true
                                    break
                        if found
                            break
                    if not found
                        done = true
                console.log(nears_s)
                nears_c = []
                for key of nears_s
                    nears_t = app.map.moves.fleets[key]
                    for j in nears_t
                        if j isnt id_f
                            if not app.IsSea(j)
                                if j not in nears_c
                                    nears_c.push(j)
                for i in nears_c
                    if i in nears_o
                        nears_res.push(i)
            when "sup_move_from"
                if app.IsArmy(id_f)
                    nears = app.map.moves.armies[id_f]
                else
                    if app.IsMCoast(id_f)
                        mc_pos = app.map.mc_pos[id_f]
                        nears = app.map.moves.mc[id_f][mc_pos]
                    else
                        nears = app.map.moves.fleets[id_f]
                console.log(nears)
                for i in nears
                    f_nears = []
                    if app.map.moves.fleets[i]
                        for j in app.map.moves.fleets[i]
                            if j isnt id_f and app.IsFleet(j)
                                f_nears.push(j)
                    if app.map.moves.armies[i]
                        for j in app.map.moves.armies[i]
                            if j isnt id_f and app.IsArmy(j)
                                f_nears.push(j)
                    #console.log(f_nears)
                    for j in f_nears
                        if j not in nears_res
                            #if j in app.map.troops_lst or j in app.map.fleets_lst
                            nears_res.push(j)
                ## via Convoy
                ## HOW TO?
                #c_nears = []
                #for key, j in app.play.orders
                #   if j.type is "move" and j.viaConvoy isnt null and j.to in nears
                #       c_nears.push(key)
                #console.log(c_nears)
                #for j in c_nears
                #   if j not in nears_res
                #       nears_res.push(j)
                nears_s = {}
                for i in nears
                    if app.map.moves.fleets[i]
                        for j in app.map.moves.fleets[i]
                            if app.IsFleet(j) and app.IsSea(j)
                                nears_s[j] = 1
                console.log(nears_s)
                console.log(jQuery.isEmptyObject(nears_s))
                done = jQuery.isEmptyObject(nears_s)
                console.log(done)
                while not done
                    found = false
                    for key, value of nears_s
                        nears_t = app.map.moves.fleets[key]
                        for j in nears_t
                            if j not in (key for key of nears_s)
                                if app.IsFleet(j) and app.IsSea(j)
                                    nears_s[j] = value + 1
                                    console.log(nears_s)
                                    found = true
                                    break
                        if found
                            break
                    if not found
                        done = true
                console.log(nears_s)
                for key of nears_s
                    nears_t = app.map.moves.fleets[key]
                    for j in nears_t
                        if j isnt id_f
                            #if j not in app.map.seas
                            if not app.IsSea(j)
                                if app.IsArmy(j)
                                    if j not in nears_res
                                        nears_res.push(j)
            when "convoy_from"
                nears = app.map.moves.fleets[id_f]
                for i in nears
                    if app.IsCoast(i) and app.IsArmy(i)
                        nears_res.push(i)
            when "convoy_to_fleet"
                nears = app.map.moves.fleets[id_f]
                for i in nears
                    if i not in app.play.track_cterrs
                        if app.IsSea(i) and app.IsFleet(i)
                            nears_res.push(i)
            when "convoy_to_terr"
                nears = app.map.moves.fleets[id_f]
                for i in nears
                    if app.IsCoast(i)
                        nears_res.push(i)
        return nears_res


    ConvoysFromMove: (id_f, id_t) ->
        conv_lst = []
        country = app.FindCountry(id_f)
        #id_t = app.play.moves[id_f].to
        nears_t = app.map.moves.fleets[id_t]
        console.log(nears_t)
        val = 0
        for i, v of app.play.track_convoy
            if v > val
                val = v
        console.log(val)
        #val = 10
        for i in nears_t
            conv_val = app.play.track_convoy[i]
            if conv_val
                console.log(conv_val)
                if conv_val < val
                    val = conv_val
                    console.log(val)
        ## multi ROUTE?? how TO?
        routes = []
        for key, value of app.play.track_convoy
            if value <= val
                if not routes[value-1]
                    routes[value-1] = []
                #conv_lst.push(key)
                routes[value-1].push(key)
        console.log(routes)
        ##for route in routes
        country_troops = app.GetCountryTroops(app.play.country)
        for i in [0..routes.length-1]
            route = routes[i]
            console.log(route)
            if route.length > 1
                #arm_dict = app.map.troops[country]
                #console.log(arm_dict)
                for i in route
                    console.log(i)
                    #if i in (key for key of (tlist for ttype, tlist of arm_dict))
                    if i in country_troops
                        conv_lst.push(i)
                        console.log(conv_lst)
                        break
            if conv_lst.length<i+1
                conv_lst.push(route[0])
        console.log(conv_lst)
        return conv_lst


    ###
    -- EVENTS and ACTIONS functions --
    ###
    ClickCheck: (act, color) ->
        res = false
        Id = app.GetTerrId(color)
        ## same check and correction
        if app.IsSame(Id)
            Id = app.map.same[Id]
        switch act
            when "select"
                ## TODO: add build support
                if (app.phase.id is app.map.phase.id) or (app.map.phase.id is "next")
                    #arm_dict = app.map.troops[app.play.country]
                    #if Id in (key for key of arm_dict)
                    if Id in app.GetCountryTroops(app.play.country)
                        res = true
            when "move"
                if Id in app.play.track_terrs
                    res = true
            when "sup_hold"
                if Id in app.play.track_terrs
                    res = true
            when "sup_move_from"
                if Id in app.play.track_terrs
                    res = true
            when "sup_move_to"
                lst = app.play.track_terrs[1..]
                console.log(lst)
                if Id in lst
                    #if Id isnt app.GetTerrId(app.play.active_terr)
                    res = true
            when "convoy_from"
                if Id in app.play.track_terrs
                    res = true
            when "convoy_to"
                clen = app.play.track_cterrs.length+1
                lst = app.play.track_terrs[clen..]
                console.log(lst)
                if Id in lst
                    #if Id isnt app.GetTerrId(app.play.active_terr)
                    res = true
        console.log(res)
        return res

    ClickEvent: (eve) ->
        app.play.action = eve
        m_id = app.play.active_terr
        act = app.ActionPresent(m_id)
        re_act = false
        ## check if deactivating action
        if act is eve
            re_act = true
            app.play.action = "menu"
        console.log(re_act)
        console.log(act)
        console.log(eve)
        ## check if action present
        if act
            if eve isnt "close"
                console.log("deleting move")
                ## need to check moves break on "move"
                ##
                #if act is "move"
                #   to_delete = []
                #   for key, value of app.play.moves
                #       if value.from is m_id
                #           to_delete.push(key)
                #   for i in to_delete
                #       #delete app.play.moves[i]
                #       app.DelMove(i)
                #delete app.play.moves[m_id]
                app.DelMove(m_id)
                app.DrawLines()
            app.MenuButtons("reset", app.play.active_terr)
        switch eve
            when "move"
                if not re_act
                    app.Terr_MoveTo_On(app.play.active_terr)
                    app.CloseMenu()
            when "sup_move"
                if not re_act
                    app.Terr_SupMove_From_On(app.play.active_terr)
                    app.CloseMenu()
            when "sup_hold"
                if not re_act
                    app.Terr_SupHold_On(app.play.active_terr)
                    app.CloseMenu()
            when "convoy"
                if not re_act
                    app.Terr_Convoy_From_On(app.play.active_terr)
                    #app.MenuButtons("reset", app.play.active_terr)
                    app.CloseMenu()
            when "close"
                app.TerrOff(app.play.active_terr)
                app.CloseMenu()
                app.play.action = "none"
        app.UpdateMap()
        return

    MCClick: (act) ->
        pos = x: 0, y: 0
        switch act
            ## north click
            when "mc_n"
                app.ActionEvent("mcoast_n", pos)
            ## south click
            when "mc_s"
                app.ActionEvent("mcoast_s", pos)
        app.CloseMCMenu()
        app.DrawLines()
        app.UpdateMap()

    Action: (mpos, pos, img) ->
        ## TODO: add retreats and builds support
        console.log("called action")
        refcolor = app.GetColor(pos)
        if app.ValidColor(refcolor)
            do_map_upd = true
            switch app.play.action
                when "none"
                    id = app.GetTerrId(refcolor)
                    ## same check and correction
                    if app.IsSame(id)
                        id = app.map.same[id]
                    if app.ClickCheck("select", refcolor)
                        app.MenuButtons("open", id)
                        app.LoadMenu(mpos)
                        app.play.action = "menu"
                    #else
                    #   app.LoadTerrName(id)
                    #   app.play.action = "name"
                        app.TerrOn(id)
                        app.play.active_terr = id
                        console.log(app.play.active_terr)
                    else
                        do_map_upd = false
                #when "name"
                #   app.HideTerrName()
                #   app.TerrOff(app.play.active_terr)
                #   app.play.action = "none"
                when "menu"
                    app.MenuButtons("reset", app.play.active_terr)
                    app.CloseMenu()
                    app.TerrOff(app.play.active_terr)
                    app.play.action = "none"
                when "move"
                    if app.ClickCheck("move", refcolor)
                        app.ActionEvent("move", pos)
                        app.DrawLines()
                    else
                        app.Terr_Track_Off()
                        app.TerrOff(app.play.active_terr)
                        app.play.action = "none"
                when "sup_move"
                    if app.ClickCheck("sup_move_from", refcolor)
                        app.ActionEvent("sup_move_from", pos)
                        #app.Terr_SupMove_To_On(refcolor)
                        #app.play.action = "sup_move_to"
                    else
                        app.Terr_Track_Off()
                        app.TerrOff(app.play.active_terr)
                        app.play.action = "none"
                when "sup_move_to"
                    if app.ClickCheck("sup_move_to", refcolor)
                        app.ActionEvent("sup_move_to", pos)
                        app.DrawLines()
                        if app.play.action is "none"
                            app.Terr_Track_Off()
                            app.TerrOff(app.play.active_terr)
                    else
                        app.Terr_Track_Off()
                        app.TerrOff(app.play.active_terr)
                        app.play.action = "none"
                when "sup_hold"
                    if app.ClickCheck("sup_hold", refcolor)
                        app.ActionEvent("sup_hold", pos)
                        app.DrawLines()
                    app.Terr_Track_Off()
                    app.TerrOff(app.play.active_terr)
                    app.play.action = "none"
                when "convoy"
                    if app.ClickCheck("convoy_from", refcolor)
                        app.ActionEvent("convoy_from", pos)
                    else
                        app.Terr_Track_Off()
                        app.TerrOff(app.play.active_terr)
                        app.play.action = "none"
                when "convoy_to"
                    if app.ClickCheck("convoy_to", refcolor)
                        app.ActionEvent("convoy_to", pos)
                        if app.play.action is "none"
                            app.DrawLines()
                    else
                        app.Terr_Track_Off()
                        app.play.action = "none"
                    #app.Terr_Track_Off()
                    #app.TerrOff(app.play.active_terr)
                    #app.play.action = "none"
                when "mcoast_move"
                    ## this is called only on invalid click, so we delete the movement
                    app.DelMove(app.play.active_terr)
                    app.DrawLines()
                    app.Terr_Track_Off()
                    app.TerrOff(app.play.active_terr)
                    app.play.action = "none"
                    app.CloseMCMenu()
            if do_map_upd
                app.UpdateMap()
        return

    AddMove: (id, type, from, to, viaConvoy, croute) ->
        data = type: type, from: from, to: to, viaConvoy: viaConvoy, croute: croute
        app.play.moves[id] = data
        #if id in (key for key of app.map.troops[app.play.country])
        if id in app.GetCountryTroops(app.play.country)
            app.AddOrder(id, data)
        return

    DelMove: (id) ->
        to_delete = []
        to_delete.push(id)
        if app.play.moves[id].type is "move"
            for key, value of app.play.moves
                if value.from is id
                    to_delete.push(key)
        else if app.play.moves[id].type is "sup_move"
            ## remove move order if no other sup_move
            del_move = true
            for key, value of app.play.moves
                if value.from is app.play.moves[id].from and value.type in ["sup_move", "convoy"]
                    if key isnt id
                        del_move = false
                        break
            if del_move
                to_delete.push(app.play.moves[id].from)
        else if app.play.moves[id].type is "convoy"
            to_delete.push(app.play.moves[id].from)
            for key, value of app.play.moves
                if value.from is app.play.moves[id].from and value.type is "convoy"
                    if key not in to_delete
                        to_delete.push(key)
        for i in to_delete
            delete app.play.moves[i]
            #if i in (key for key of app.map.troops[app.play.country])
            if i in app.GetCountryTroops(app.play.country)
                app.DelOrder(i)
        return

    AddOrder: (id, data) ->
        app.play.orders[id]["type"] = data.type
        app.play.orders[id]["to"] = data.to
        #app.play.orders[id] = type: data.type, to: data.to
        if data.type is "move"
            if data.viaConvoy
                app.play.orders[id]["viaConvoy"] = data.viaConvoy
                app.play.orders[id]["convoy_route"] = data.croute
            if app.IsMCoast(data.to)
                app.play.orders[id]["mc"] = app.play.moves_mc[id]
        else if data.type in ["sup_move", "convoy"]
            app.play.orders[id]["from"] = data.from
        #country = app.GetCountryByTerr(id)
        #try
        #   app.play.orders_country[country].push(id)
        #catch
        #   app.play.orders_country[country] = []
        #   app.play.orders_country[country].push(id)
        app.AddOrderM(id, app.play.orders[id])
        return

    DelOrder: (id) ->
        app.play.orders[id] = type: "hold"
        app.DelOrderM(id)
        return

    BuildOrderStr: (id, data) ->
        order_str = app.map.names[id]+' '+data.type
        if data.type isnt "hold"
            if data.type is "move"
                order_str += ' to '+app.map.names[data.to]
                if data.viaConvoy
                    order_str += ' via convoy'
                if data.mc isnt undefined
                    if data.mc is 0
                        order_str += ' north coast'
                    else
                        order_str += ' south coast'
            else
                order_str += ' from '+app.map.names[data.from]+' to '+app.map.names[data.to]
        return order_str

    AddOrderM: (id, data) ->
        #order_str = app.map.names[id]+' '+data["type"]+' from '+app.map.names[data["from"]]+' to '+app.map.names[data["to"]]+'.'
        #$('#ord_wrapper').append '<div class="order" id="ord_'+id+'">'+order_str+'</div>'
        order_str = app.BuildOrderStr(id, data)
        $('#ord_next_'+id).html order_str
        return

    DelOrderM: (id) ->
        $('#ord_'+id).remove()
        return

    ActionEvent: (act, pos) ->
        switch act
            when "move"
                console.log("moving")
                id = app.play.active_terr
                color = app.GetColor(pos)
                t_id = app.GetTerrId(color)
                ## multi-coasts check
                if app.IsMCoast(t_id) and app.IsFleet(id)
                    mv_mc_lst = app.map.moves.mc[t_id]
                    l0 = id in mv_mc_lst[0]
                    l1 = id in mv_mc_lst[1]
                    if l0 and l1
                        console.log("sei stronzo")
                        app.play.action = "mcoast_move"
                        ## store the t_id in track_terrs
                        app.Terr_Track_Off()
                        app.play.track_terrs.push(t_id)
                        ccolor = r: 235, g: 0, b: 0
                        app.ColorTerr(t_id, ccolor)
                        #app.UpdateMap()
                        app.LoadMCMenu(app.GetPagePos(pos))
                    else
                        if l0
                            app.play.moves_mc[id] = 0
                        else
                            app.play.moves_mc[id] = 1
                        #app.play.moves[id] = type: "move", from: id, to: t_id
                        app.Terr_Track_Off()
                        app.TerrOff(app.play.active_terr)
                        app.play.action = "none"
                        app.AddMove(id, "move", id, t_id)
                else
                    #app.play.moves[id] = type: "move", from: id, to: t_id
                    ## convoys check
                    if t_id in app.play.track_cterrs
                        convoys = app.ConvoysFromMove(id, t_id)
                        console.log(convoys)
                        for i in convoys
                            #app.play.moves[i] = type: "convoy", from: id, to: t_id
                            app.AddMove(i, "convoy", id, t_id)
                        #app.play.moves[id]["viaConvoy"] = true
                        #app.play.moves[id]["convoy_route"] = convoys
                        app.AddMove(id, "move", id, t_id, true, convoys)
                    else
                        app.AddMove(id, "move", id, t_id)
                    app.Terr_Track_Off()
                    app.TerrOff(app.play.active_terr)
                    app.play.action = "none"
            when "sup_hold"
                console.log("supping hold")
                id = app.play.active_terr
                color = app.GetColor(pos)
                t_id = app.GetTerrId(color)
                #app.play.moves[id] = type: "sup_hold", from: id, to: t_id
                app.AddMove(id, "sup_hold", id, t_id)
            when "sup_move_from"
                console.log("supping move from")
                color = app.GetColor(pos)
                id_f = app.GetTerrId(color)
                if app.ActionPresent(id_f) is "move"
                    console.log("move present")
                    ## check move is valid..
                    nears_c = app.AvailMoveList("sup_move_to", id_f)
                    if app.play.moves[id_f].to in nears_c
                        console.log("valid sup_move movement")
                        id = app.play.active_terr
                        id_t = app.play.moves[id_f].to
                        app.Terr_Track_Off()
                        app.TerrOff(app.play.active_terr)
                        app.play.action = "none"
                        #app.play.moves[id] = type: "sup_move", from: id_f, to: id_t
                        app.AddMove(id, "sup_move", id_f, id_t)
                        app.DrawLines()
                    else
                        #delete app.play.moves[id_f]
                        #app.DelOrder(id_f)
                        app.DelMove(id_f)
                        app.Terr_SupMove_To_On(id_f)
                        app.play.action = "sup_move_to"
                else
                    app.Terr_SupMove_To_On(id_f)
                    app.play.action = "sup_move_to"
                #id = app.GetTerrId(app.play.active_terr)
                #color = app.GetColor(pos)
                #t_id = app.GetTerrId(color)
            when "sup_move_to"
                console.log("supping move to")
                id = app.play.active_terr
                color = app.GetColor(pos)
                f_id = app.play.track_terrs[0]
                t_id = app.GetTerrId(color)
                continue_mc = false
                #if f_id in (key for key of app.map.troops[app.play.country])
                if f_id in app.GetCountryTroops(app.play.country)
                    if app.IsMCoast(t_id) and app.IsFleet(f_id)
                        mv_mc_lst = app.map.moves.mc[t_id]
                        l0 = id in mv_mc_lst[0]
                        l1 = id in mv_mc_lst[1]
                        if l0 and l1
                            console.log("sei stronzo")
                            continue_mc = true
                            app.play.action = "mcoast_move"
                            ## store the t_id in track_terrs
                            app.TerrOff(app.play.active_terr)
                            app.Terr_Track_Off()
                            app.play.track_terrs.push(t_id)
                            app.play.active_terr = f_id
                            ccolor = r: 235, g: 0, b: 0
                            app.ColorTerr(t_id, ccolor)
                            app.UpdateMap()
                            app.LoadMCMenu(app.GetPagePos(pos))
                        else
                            if l0
                                app.play.moves_mc[id] = 0
                            else
                                app.play.moves_mc[id] = 1
                            #app.play.moves[id] = type: "move", from: id, to: t_id
                            #app.AddMove(id, "move", id, t_id)
                            #app.Terr_Track_Off()
                            #app.TerrOff(app.play.active_terr)
                            #app.play.action = "none"
                app.AddMove(id, "sup_move", f_id, t_id)
                app.AddMove(f_id, "move", f_id, t_id)
                if not continue_mc
                    #app.play.moves[id] = type: "sup_move", from: f_id, to: t_id
                    #app.play.moves[f_id] = type: "move", from: f_id, to: t_id
                    app.play.action = "none"
            when "convoy_from"
                console.log("convoying from")
                id = app.play.active_terr
                app.play.track_cterrs.push(id)
                color = app.GetColor(pos)
                f_id = app.GetTerrId(color)
                for i in app.play.track_terrs
                    if i isnt f_id
                        ccolor = r: app.map.colors_now[i].r, g: app.map.colors_now[i].g, b: app.map.colors_now[i].b
                        app.ColorTerr(i, ccolor)
                app.play.track_terrs = [f_id, id]
                ## color the moving army
                ccolor = r: 235, g: 235, b: 0
                app.ColorTerr(f_id, ccolor)
                ## color the convoy fleet
                ccolor = r: 0, g: 235, b: 0
                app.ColorTerr(id, ccolor)
                app.Terr_Convoy_To_On(app.play.active_terr)
                app.play.action = "convoy_to"
            when "convoy_to"
                console.log("convoying to")
                color = app.GetColor(pos)
                id = app.GetTerrId(color)
                f_id = app.play.track_terrs[0]
                if app.IsCoast(id)
                    #app.play.moves[f_id] = type: "move", from: f_id, to: id, viaConvoy: true, convoy_route: app.play.track_cterrs
                    app.AddMove(f_id, "move", f_id, id, true, app.play.track_cterrs)
                    for i in app.play.track_cterrs
                        #app.play.moves[i] = type: "convoy", from: f_id, to: id
                        app.AddMove(i, "convoy", f_id, id)
                    app.Terr_Track_Off()
                    app.play.action = "none"
                    #app.DrawLines()
                else
                    app.play.track_cterrs.push(id)
                    for i in app.play.track_terrs
                        if i isnt f_id
                            if i not in app.play.track_cterrs
                                ccolor = r: app.map.colors_now[i].r, g: app.map.colors_now[i].g, b: app.map.colors_now[i].b
                                app.ColorTerr(i, ccolor)
                    app.play.track_terrs = [f_id]
                    for i in app.play.track_cterrs
                        app.play.track_terrs.push(i)
                    ## color the new convoy fleet
                    ccolor = r: 0, g: 235, b: 0
                    app.ColorTerr(id, ccolor)
                    app.Terr_Convoy_To_On(id)
            when "mcoast_n"
                id = app.play.active_terr
                t_id = app.play.track_terrs[0]
                mv_mc_lst = app.map.mcoasts_oxy[t_id]
                if mv_mc_lst[0].y < mv_mc_lst[1].y
                    mc_n = 0
                    mc_s = 1
                else
                    mc_n = 1
                    mc_s = 0
                app.play.moves_mc[id] = mc_n
                #app.play.moves[id] = type: "move", from: id, to: t_id
                app.AddMove(id, "move", id, t_id)
                app.Terr_Track_Off()
                app.TerrOff(app.play.active_terr)
                app.play.action = "none"
            when "mcoast_s"
                id = app.play.active_terr
                t_id = app.play.track_terrs[0]
                mv_mc_lst = app.map.mcoasts_oxy[t_id]
                if mv_mc_lst[0].y < mv_mc_lst[1].y
                    mc_n = 0
                    mc_s = 1
                else
                    mc_n = 1
                    mc_s = 0
                app.play.moves_mc[id] = mc_s
                #app.play.moves[id] = type: "move", from: id, to: t_id
                app.AddMove(id, "move", id, t_id)
                app.Terr_Track_Off()
                app.TerrOff(app.play.active_terr)
                app.play.action = "none"
        ## next phase auto swithing
        if app.map.phase.id isnt "next" and app.TheresOrders()
            app.LoadPhase("next", false)
        return


    LoadTerrName: (mpos, pos) ->
        refcolor = app.GetColor(pos)
        id = app.GetTerrId(refcolor)
        if app.map.names[id]
            name = app.map.names[id]
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

    HideTerrName: ->
        if $('#terr_name').length != 0
            $('#terr_name').animate
                opacity:'0'
                300
                'linear'
                ->
                    $('#terr_name').remove()
        return

    ###
    -- MENUs and BARS functions --
    ###
    MenuButtons: (act, id) ->
        if act is "open"
            console.log(id)
            console.log(app.CanConvoy(id))
            if app.CanConvoy(id)
                $('#btn_c').removeClass 'ninja'
            #move = app.play.moves[id]
            #console.log(move)
            #if move
            move = app.ActionPresent(id)
            if move
                console.log('MenuButtons activated')
                switch move
                    when "move"
                        $('#btn_m').addClass 'btn-primary'
                    when "sup_hold"
                        $('#btn_sh').addClass 'btn-primary'
                    when "sup_move"
                        $('#btn_sm').addClass 'btn-primary'
                    when "convoy"
                        $('#btn_c').addClass 'btn-primary'
        else if act is "close"
            $('#btn_c').addClass 'ninja'
        else if act is "reset"
            $('#btn_m').removeClass 'btn-primary'
            $('#btn_sh').removeClass 'btn-primary'
            $('#btn_sm').removeClass 'btn-primary'
            $('#btn_c').removeClass 'btn-primary'
        return

    LoadMenu: (mpos) ->
        console.log("called loadmenu")
        console.log(mpos)
        ## load buttons state
        m_x = mpos.x - 40
        m_y = mpos.y - 60
        $('#terr_menu').css
            top: m_y+'px'
            left: m_x+'px'
            visibility: 'visible'
        $('#terr_menu').animate
            opacity:'1'
            500
            'linear'
        return

    CloseMenu: ->
        app.MenuButtons("close", false)
        $('#terr_menu').animate
            opacity:'0'
            500
            'linear'
        $('#terr_menu').css visibility: 'hidden'
        return

    LoadMCMenu: (mpos) ->
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

    CloseMCMenu: ->
        $('#mcoast_menu').animate
            opacity:'0'
            500
            'linear'
        $('#mcoast_menu').css visibility: 'hidden'
        return

    OpenBar: (side) ->
        app.page.bars_open += 1
        val = 1 - 0.18*app.page.bars_open
        newzoom = app.page.w*val/app.canv.img.width
        app.page.zoom = newzoom
        switch side
            when "left"
                $('#left_wrapper').animate
                    #left: '0px'
                    left: '-20%'
                    300
                    'linear'
                $('#cont_wrapper').animate
                    #width: '83%'
                    width: (100-17*app.page.bars_open)+'%'
                    #height: app.canv.img.height*newzoom
                    left: '17%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.canv.img.height*app.page.zoom
                    300
                    'linear'
            when "right"
                $('#right_wrapper').animate
                    right: '0px'
                    300
                    'linear'
                $('#cont_wrapper').animate
                    #width: '83%'
                    width: (100-17*app.page.bars_open)+'%'
                    #height: app.canv.img.height*newzoom
                    right: '17%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.canv.img.height*app.page.zoom
                    300
                    'linear'
        $('.menu_butt').each(
            ->
                c_off = $(this).offset().top
                c_top = c_off+$('#cont_wrapper').scrollTop()
                console.log(c_top)
                console.log(app.canv.img.height*app.page.zoom)
                if c_top >= (app.canv.img.height*app.page.zoom-40)
                    $(this).offset
                        top: c_off*app.page.zoom
                c_off = $(this).offset().left
                c_left = c_off+$('#cont_wrapper').scrollLeft()
                if c_left >= (app.canv.img.width*app.page.zoom-40)
                    $(this).offset
                        left: c_off*app.page.zoom
                return
        )
        return

    ExtendBar: (side) ->
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

    CompressBar: (side) ->
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

    CloseBar: (side) ->
        app.page.bars_open -= 1
        val = 1 - 0.18*app.page.bars_open
        newzoom = app.page.w*val/app.canv.img.width
        app.page.zoom = newzoom
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
                    width: (100-17*app.page.bars_open)+'%'
                    #height: app.canv.img.height*app.page.zoom
                    left: '0%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.canv.img.height*app.page.zoom
                    300
                    'linear'
            when "right"
                $('#right_wrapper').animate
                    right: '-18%'
                    300
                    'linear'
                $('#cont_wrapper').animate
                    #width: '100%'
                    width: (100-17*app.page.bars_open)+'%'
                    #height: app.canv.img.height*app.page.zoom
                    right: '0%'
                    300
                    'linear'
                $('#map_img').animate
                    height: app.canv.img.height*app.page.zoom
                    300
                    'linear'
        return

    OpenTopMenu: ->
        if app.page.stats_bar is "closed"
            $('#top_wrapper').stop()
            $('#top_wrapper').animate
                top: '0px'
                300
                'linear'
        return

    CloseTopMenu: ->
        if app.page.stats_bar is "closed"
            $('#top_wrapper').stop()
            $('#top_wrapper').animate
                top: '-40px'
                300
                'linear'
        return

    OpenStats: ->
        #$('#stats_wrapper').stop()
        $('#stats_wrapper').css
            top: '-50%'
        $('#stats_wrapper').animate
            top: '0px'
            500
            'linear'
        $('#top_wrapper').animate
            top: '50%'
            500
            'linear'
        return

    CloseStats: ->
        #$('#stats_wrapper').stop()
        $('#stats_wrapper').animate
            top: '-50%'
            500
            'linear'
            ->
                $('#stats_wrapper').css
                    top: '-52%'
        $('#top_wrapper').animate
            top: '0px'
            500
            'linear'
        return

    TopButtons: (act, dis) ->
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

    TopPhase: (id) ->
        $('#phase_ind').empty()
        if id isnt "next"
            #$('#phase_ind').append '<span>'+id+'/'+app.phase.id+'</span>'
            if app.phase.season[id]
                $('#phase_ind').append '<span>'+app.phase.season[id]+' '+app.phase.year[id]+'</span>'
            else
                $('#phase_ind').append '<span>'+app.phase.type[id]+' '+app.phase.year[id]+'</span>'
        else
            $('#phase_ind').append '<span><em>Next</em></span>'
        return

    OrdersMenuPhase: (phase) ->
        last = app.map.phase.id
        console.log(phase)
        console.log(last)
        if last isnt "next"
            last--
        if phase isnt "next"
            phase--
        console.log(phase)
        console.log(last)
        ###
        $('#orders_'+last+' .ord_pin').each(
            ->
                console.log(this.id)
                app.OrdersPinClose('#'+this.id)
                return
        )
        ###
        $('#orders_'+last).css
            visibility: 'hidden'
        $('#orders_'+phase).css
            visibility: 'visible'
        ###
        $('#orders_'+phase+' .ord_pin').each(
            ->
                console.log(this.id)
                app.OrdersPinOpen('#'+this.id)
                return
        )
        ###

    OrdersPinClick: (id) ->
        ## id finish with _head
        sid = id.split("_")
        sid.pop()
        pid = '#'+sid.join("_")
        closed = $(pid+"_text").hasClass 'ord_pin_text_off'
        if closed
            app.OrdersPinOpen(pid)
        else
            app.OrdersPinClose(pid)

    OrdersPinOpen: (id) ->
        $(id+'_text').removeClass 'ord_pin_text_off'
        $(id+'_text').addClass 'ord_pin_text_on'
        $(id+'_icon').removeClass 'ord_pin_icon_off'
        $(id+'_icon').addClass 'ord_pin_icon_on'
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

    OrdersPinClose: (id) ->
        $(id+'_data').animate
            #visibility: 'hidden'
            opacity: 0
            200
        $(id).animate
            height: 20
            200
        $(id+'_text').removeClass('ord_pin_text_on')
        $(id+'_text').addClass('ord_pin_text_off')
        $(id+'_icon').removeClass('ord_pin_icon_on')
        $(id+'_icon').addClass('ord_pin_icon_off')

    ChatLoad: (id) ->
        sid = id.split("_")
        cid = sid.pop()
        $('#msg_conv_'+cid).removeClass('ninja')
        $('.msg_select').animate
            opacity: 0
            200
        $('#msg_conv_'+cid).animate
            opacity: 1
            200
        $('.msg_select').addClass('ninja')
        return

    ChatBack: (id) ->
        $('.msg_select').removeClass('ninja')
        $('#'+id).animate
            opacity: 0
            200
        $('.msg_select').animate
            opacity: 1
            200
        $('#'+id).addClass('ninja')

    componentToHex: (c) ->
        hex = c.toString(16)
        if hex.length == 1
            return "0"+hex
        return hex

    rgbToHex: (r, g, b) ->
        "#"+app.componentToHex(r) + app.componentToHex(g) + app.componentToHex(b)
