
class Screen
    constructor: ->
        @img = ''
        @imgArmy = ''
        @imgFleet = ''
        @ref =
            layer: ''
            ctx: ''
            pix: ''
            pixdata: ''
        @base =
            layer: ''
            ctx: ''
            pix: ''
            pixdata: ''
        @ov =
            layer: ''
            ctx: ''
        @arms =
            layer: ''
            ctx: ''
        @arws =
            layer: ''
            ctx: ''
        @res =
            layer: ''
            ctx: ''
        return

    createElements: ->
        #: create canvas
        @ref.layer = document.createElement("canvas")
        @base.layer = document.createElement("canvas")
        @ov.layer = document.createElement("canvas")
        @arms.layer = document.createElement("canvas")
        @arws.layer = document.createElement("canvas")
        @res.layer = document.createElement("canvas")
        #: create a ref img
        @img = document.createElement("img")
        ## TODO: update next line
        #@img.src = "map.png"
        @img.src = document.getElementById("map_img").src
        ##
        @img_army = document.getElementById("army_img")
        @img_fleet = document.getElementById("ship_img")
        return

    init: ->
        #: set width and height on canvas
        @ref.layer.width = @img.width
        @ref.layer.height = @img.height
        @base.layer.width = @img.width
        @base.layer.height = @img.height
        @ov.layer.width = @img.width
        @ov.layer.height = @img.height
        @arms.layer.width = @img.width
        @arms.layer.height = @img.height
        @arws.layer.width = @img.width
        @arws.layer.height = @img.height
        @res.layer.width = @img.width
        @res.layer.height = @img.height
        #: set contexts
        @ref.ctx = @ref.layer.getContext('2d')
        @base.ctx = @base.layer.getContext('2d')
        @ov.ctx = @ov.layer.getContext('2d')
        @arms.ctx = @arms.layer.getContext('2d')
        @arws.ctx = @arws.layer.getContext('2d')
        @res.ctx = @res.layer.getContext('2d')
        #: draw ref image in base and ref canvas
        @base.ctx.drawImage(@img, 0, 0)
        @ref.ctx.drawImage(@img, 0, 0)
        #: load and rebuild img data
        @_loadData()
        @_buildPixArray()
        @_initLayers()
        return

    _loadData: ->
        #: initialize canvas pixel data
        @base.pix = @base.ctx.getImageData(0,0,@base.layer.width,@base.layer.height)
        @ref.pix = @ref.ctx.getImageData(0,0,@base.layer.width,@base.layer.height)
        @base.pixdata = @base.pix.data
        @ref.pixdata = @ref.pix.data
        return

    _buildPixArray: ->
        filter = (list, color) ->
            #x for x in [0..list.length-1] when (list[x].r is color[0] and list[x].g is color[1] and list[x].b is color[2])
            l = []
            for x in [0..list.length-1]
                if list[x].r is color[0]
                    if list[x].g is color[1]
                        if list[x].b is color[2]
                            l.push(x)
            return l
        #: build an array of objects for pixs
        pixa = []
        j = 0
        #time_start = new Date().getTime()
        for i in [0..@ref.pixdata.length-1] by 4
            pixa[j] = r: @ref.pixdata[i], g: @ref.pixdata[i+1], b: @ref.pixdata[i+2]
            j += 1
        #time_end = new Date().getTime()
        #time_ex = time_end - time_start
        #console.log("1time "+time_ex)
        #time_start = new Date().getTime()
        for key, color of app.env.colors
            app.env.pix[key] = filter(pixa, color)
        #time_end = new Date().getTime()
        #time_ex = time_end - time_start
        #console.log("2time "+time_ex)
        return

    ## NOTE: this seems slower
    _OLDbuildPixArray: ->
        filter = (obj, color) ->
            #x for x, val of obj when (val[0] is color.r and val[1] is color.g and val[2] is color.b)
            for x, val of obj
                if val[0] is color.r and val[1] is color.g and val[2] is color.b
                    return x
            return null
        pixa = []
        j = 0
        for i in [0..@ref.pixdata.length-1] by 4
            pixa[j] = r: @ref.pixdata[i], g: @ref.pixdata[i+1], b: @ref.pixdata[i+2]
            j += 1
        for key of app.env.colors
            #console.log(key)
            app.env.pix[key] = []
        j = 0
        for pix in pixa
            #color = key for key, val of app.env.colors when (val[0] is pix.r and val[1] is pix.g and val[2] is pix.b)
            color = filter(app.env.colors, pix)
            if color isnt null
                app.env.pix[color].push(j)
            j += 1
        return

    _initLayers: ->
        #: re-color the map based on the reference object for colors
        for key, color of app.game.colors
            @colorTerritory(key, color)
        @drawSupply()
        @drawTroops()
        @drawLines()
        @update()
        return

    getColor: (pos) ->
        #: get the real image color from the given position
        s_map = @ref.ctx.getImageData(pos.x,pos.y,1,1)
        color = s_map.data
        res_color = r: color[0], g: color[1], b: color[2]

    update: ->
        #: update the rendered image in page
        @base.ctx.putImageData(@base.pix,0,0)
        @res.ctx.drawImage(@base.layer,0,0)
        @res.ctx.drawImage(@ov.layer,0,0)
        @res.ctx.drawImage(@arws.layer,0,0)
        @res.ctx.drawImage(@arms.layer,0,0)
        app.ui.img.src = @res.layer.toDataURL()

    _diffColor: (color1, color2) ->
        return !(color1.r is color2.r and color1.g is color2.g and color1.b is color2.b)

    _getTerritories: ->
        if app.game.phase().id is 0
            rv = {}
            for key of app.env.countries
                rv[key] = []
                for terr in app.env.countries_init[key]
                    rv[key].push(terr)
            return rv
            #return app.env.countries_init
        return app.game.phase().territories

    _updateColors: (grounds) ->
        ## draw all terrs to ground color
        color = r: 226, g: 198, b: 158
        for i in grounds
            app.game.colors[i] = color
        ## draw countries terrs
        territories = @_getTerritories()
        for key, color of app.env.countries
            #for i in app.game.phase().territories[key]
            for i in territories[key]
                app.game.colors[i] = color
        return

    change: (old_c_terrs, old_tcolors) ->
        #: re-color the map based on the reference object for colors
        #time_start = new Date().getTime()
        c_terrs = []
        #for key, terr_list of app.map.countries_terr
        territories = @_getTerritories()
        #for key, terr_list of app.game.phase().territories
        console.log(old_c_terrs)
        console.log(territories)
        for key, terr_list of territories
            for terr in terr_list
                c_terrs.push(terr)
        c_diff_list = old_c_terrs.filter (x) -> x not in c_terrs
        console.log(c_diff_list)
        @_updateColors(c_diff_list)
        #time_end = new Date().getTime()
        #time_ex = time_end - time_start
        #console.log("LoadMapColors time "+time_ex)
        #time_start = new Date().getTime()
        #: color diff country terrs only
        c_diff_list = []
        for key, color of app.game.colors
            if @_diffColor(old_tcolors[key], color)
                c_diff_list.push(key)
        for terr in c_diff_list
            @colorTerritory(terr, app.game.colors[terr])
        #time_end = new Date().getTime()
        #time_ex = time_end - time_start
        #console.log("ColorTerr for time "+time_ex)
        @drawSupply()
        @drawTroops()
        @drawLines()
        @update()
        return

    colorTerritory: (id, color) ->
        #: color the terr in the base canvas
        get_pix = app.env.pix[id]
        for p in [0..get_pix.length]
            @base.pixdata[get_pix[p]*4] = color.r
            @base.pixdata[get_pix[p]*4+1] = color.g
            @base.pixdata[get_pix[p]*4+2] = color.b
        return

    clearOVMap: ->
        @ov.ctx.clearRect(0,0,@ov.layer.width,@ov.layer.height)
        return

    _clearTroops: ->
        @arms.ctx.clearRect(0,0,@arms.layer.width,@arms.layer.height)
        return

    _clearLines: ->
        @arws.ctx.clearRect(0,0,@ov.layer.width,@ov.layer.height)
        return

    drawSupply: ->
        #: draw the supply centers dots
        for key, value of app.env.supply
            x = value.x
            y = value.y
            radius = 5
            startangle = 0
            endangle = Math.PI*2
            @ov.ctx.beginPath()
            @ov.ctx.arc(x,y,radius,startangle,endangle,true)
            #@ov.ctx.closePath()
            @ov.ctx.fillStyle= "#000000"
            @ov.ctx.fill()
            radius = 4
            @ov.ctx.beginPath()
            @ov.ctx.arc(x,y,radius,startangle,endangle,true)
            #@ov.ctx.closePath()
            @ov.ctx.fillStyle= "#FFFFFF"
            @ov.ctx.fill()
            radius = 2.5
            @ov.ctx.beginPath()
            @ov.ctx.arc(x,y,radius,startangle,endangle,true)
            #@ov.ctx.closePath()
            @ov.ctx.fillStyle= "#000000"
            @ov.ctx.fill()
        return

    drawTroops: ->
        @_clearTroops()
        for country, troops of app.game.phase().troops
            dislodged = app.game.phase().dislodged[country]
            if not dislodged
                dislodged = []
            for type, tlist of troops
                for id in tlist
                    if type is "fleets" and app.env.isMCoast(id)
                        if id in dislodged
                            #? sure about that?
                            mc_pos = app.game.phase('last').previous().mcpos[id]
                        else
                            mc_pos = app.game.phase().mcpos[id]
                        x = app.env.mcoasts_oxy[id][mc_pos].x
                        y = app.env.mcoasts_oxy[id][mc_pos].y
                    else
                        x = app.env.oxy[id].x
                        y = app.env.oxy[id].y
                    ## check if country color is different from the army country
                    console.log(country)
                    if country isnt app.game.phase().getCountryByTerritory(id)
                        ## draw color square under the army
                        ccolor = app.env.countries[country]
                        @arms.ctx.beginPath()
                        @arms.ctx.rect(x-8, y-16, 16, 16)
                        @arms.ctx.lineWidth = 1
                        @arms.ctx.fillStyle = 'rgb('+ccolor.r+','+ccolor.g+','+ccolor.b+')'
                        @arms.ctx.fill()
                        @arms.ctx.strokeStyle = 'black'
                        @arms.ctx.stroke()
                    if type is "armies"
                        @arms.ctx.drawImage(@img_army, x-15, y-9, 29, 17)
                    else
                        @arms.ctx.drawImage(@img_fleet, x-13, y-11, 25, 22)
                    ## dislodgement circle
                    if app.game.phase().dislodged[country]
                        #console.log(app.env.dislodged[country])
                        if id in app.game.phase().dislodged[country]
                            console.log("dislodge circle draw..")
                            @arms.ctx.beginPath()
                            @arms.ctx.arc(x, y, 22, 0, Math.PI*2, true)
                            #@arms.ctx.closePath()
                            @arms.ctx.lineWidth = 2
                            @arms.ctx.strokeStyle = 'rgb(255,127,0)'
                            @arms.ctx.stroke()
        console.log(app.game.phase().builds)
        for tid, tdata of app.game.phase().builds
            if tdata.type in ["build_fleet", "disband"] and app.env.isMCoast(tid)
                mc_pos = tdata.mc
                x = app.env.mcoasts_oxy[tid][mc_pos].x
                y = app.env.mcoasts_oxy[tid][mc_pos].y
            else
                x = app.env.oxy[tid].x
                y = app.env.oxy[tid].y
            if tdata.type is "disband"
                ccolor = r: 255, g: 0, b: 0
                @arms.ctx.beginPath()
                @arms.ctx.arc(x+12, y-16, 4, 0, Math.PI*2, true)
                @arms.ctx.fillStyle = 'rgb('+ccolor.r+','+ccolor.g+','+ccolor.b+')'
                @arms.ctx.fill()
            else
                if tdata.type is "build_army"
                    @arms.ctx.drawImage(@img_army, x-15, y-9, 29, 17)
                else if tdata.type is "build_fleet"
                    @arms.ctx.drawImage(@img_fleet, x-13, y-11, 25, 22)
                ccolor = r: 0, g: 255, b: 0
                @arms.ctx.beginPath()
                @arms.ctx.arc(x+12, y-16, 4, 0, Math.PI*2, true)
                @arms.ctx.fillStyle = 'rgb('+ccolor.r+','+ccolor.g+','+ccolor.b+')'
                @arms.ctx.fill()
        return

    drawLines: ->
        @_clearLines()
        for id, obj of app.game.phase().pastMoves
            @newLine("past", obj.type, id, obj.from, obj.to, obj.mc, obj.success or false)
        if app.game.phase().id is "next"
            for id, obj of app.game.moves
                @newLine("future", obj.type, id, obj.from, obj.to, obj.mc)
        return

    newLine: (time, act, id, f_id, t_id, mc, success=true) ->
        country_troops = app.game.phase().getCountryTroops()
        console.log(country_troops)
        console.log(time)
        if time is "past"
            mc_pos_data = app.game.phase().previous().mcpos
            console.log(mc_pos_data)
            #mc_move_data = app.game.phase().previous().mcmoves
            #console.log(mc_move_data)
            #mc_pos_data = app.phase.mc_pos[app.phase.id-1]
            #console.log(mc_pos_data)
            #mc_move_data = app.env.moves_last_mc
            isFleet = (id) ->
                #app.WasFleet(id)
                app.game.phase().previous().isFleet(id)
        else
            #mc_pos_data = app.env.mc_pos
            #mc_move_data = app.play.moves_mc
            mc_pos_data = app.game.phase().mcpos
            #mc_move_data = app.game.phase().mcmoves
            console.log(mc_pos_data)
            #console.log(mc_move_data)
            isFleet = (id) ->
                app.game.phase().isFleet(id)
            #if id not in (key for key of app.env.troops[app.play.country])
            if id not in country_troops
                success = false

        switch act
            when "move"
                if isFleet(f_id) and app.env.isMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.env.mcoasts_oxy[f_id][mc_pos].x, app.env.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.env.oxy[f_id].x, app.env.oxy[f_id].y)
                if isFleet(f_id) and app.env.isMCoast(t_id)
                    #if f_id in (key for key of app.env.troops[app.play.country])
                    ##if f_id in country_troops
                    #mc_pos = mc_move_data[f_id]
                    p2 = new Point2D(app.env.mcoasts_oxy[t_id][mc].x, app.env.mcoasts_oxy[t_id][mc].y)
                    ##else
                    ##  p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                else
                    p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                #p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                intersect = Intersection.intersectCircleLine(p2, 18, p1, p2)
                #intersect1 = Intersection.intersectCircleLine(app.env.oxy[f_id], 10, p1, p2)
                x = p1.x
                y = p1.y
                x_t = intersect.points[0].x
                y_t = intersect.points[0].y
                if time is "past" and app.game.phase().id is "next"
                    color = "#7F7F7F"
                else
                    color = "#FF0000"
                @_drawLine(x, y, x_t, y_t, color, success)
                angle = Math.atan2(y_t-y,x_t-x)
                @_drawTriangle(angle, 10, x_t, y_t, color)
            when "sup_hold"
                if isFleet(f_id) and app.env.isMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.env.mcoasts_oxy[f_id][mc_pos].x, app.env.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.env.oxy[f_id].x, app.env.oxy[f_id].y)
                p1 = new Point2D(app.env.oxy[f_id].x, app.env.oxy[f_id].y)
                if isFleet(t_id) and app.env.isMCoast(t_id)
                    mc_pos = mc_pos_data[t_id]
                    p2 = new Point2D(app.env.mcoasts_oxy[t_id][mc_pos].x, app.env.mcoasts_oxy[t_id][mc_pos].y)
                else
                    p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                #p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                intersect = Intersection.intersectCircleLine(p2, 18, p1, p2)
                x = p1.x
                y = p1.y
                x_t = intersect.points[0].x
                y_t = intersect.points[0].y
                angle = Math.atan2(y_t-y,x_t-x)
                if time is "past" and app.game.phase().id is "next"
                    color = "#7F7F7F"
                else
                    color = "#00FF00"
                @_drawLine(x, y, x_t, y_t, color, success)
                @_drawTriangle(angle, 10, x_t, y_t, color)
                #x_t = app.env.oxy[t_id].x
                #y_t = app.env.oxy[t_id].y
                x_t = p2.x
                y_t = p2.y
                @_drawCircle(x_t, y_t, 18, color)
            when "sup_move"
                if isFleet(id) and app.env.isMCoast(id)
                    mc_pos = mc_pos_data[id]
                    p0 = new Point2D(app.env.mcoasts_oxy[id][mc_pos].x, app.env.mcoasts_oxy[id][mc_pos].y)
                else
                    p0 = new Point2D(app.env.oxy[id].x, app.env.oxy[id].y)
                if isFleet(f_id) and app.env.isMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.env.mcoasts_oxy[f_id][mc_pos].x, app.env.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.env.oxy[f_id].x, app.env.oxy[f_id].y)
                if isFleet(f_id) and app.env.isMCoast(t_id)
                    #if f_id in (key for key of app.env.troops[app.play.country])
                    if f_id in country_troops
                        #mc_pos = mc_move_data[f_id]
                        p2 = new Point2D(app.env.mcoasts_oxy[t_id][mc].x, app.env.mcoasts_oxy[t_id][mc].y)
                    else
                        p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                else
                    p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                res = @_evalSupMoveEPoint(p0, p1, p2)
                p3 = res.p0
                p4 = res.p1
                angle = res.angle
                if time is "past" and app.game.phase().id is "next"
                    color = "#7F7F7F"
                else
                    color = "#FFFF00"
                @_drawLine(p0.x, p0.y, p3.x, p3.y, color, success)
                @_drawLine(p3.x, p3.y, p4.x, p4.y, color, success)
                @_drawTriangle(angle, 10, p4.x, p4.y, color)
            when "convoy"
                p0 = new Point2D(app.env.oxy[id].x, app.env.oxy[id].y)
                p1 = new Point2D(app.env.oxy[f_id].x, app.env.oxy[f_id].y)
                p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                res = @_evalSupMoveEPoint(p0, p1, p2)
                p3 = res.p0
                p4 = res.p1
                angle = res.angle
                if time is "past" and app.game.phase().id is "next"
                    color = "#7F7F7F"
                else
                    color = "#0000FF"
                @_drawLine(p0.x, p0.y, p3.x, p3.y, color, success)
                @_drawLine(p3.x, p3.y, p4.x, p4.y, color, success)
                @_drawTriangle(angle, 10, p4.x, p4.y, color)
            when "retreat"
                if isFleet(f_id) and app.env.isMCoast(f_id)
                    mc_pos = mc_pos_data[f_id]
                    p1 = new Point2D(app.env.mcoasts_oxy[f_id][mc_pos].x, app.env.mcoasts_oxy[f_id][mc_pos].y)
                else
                    p1 = new Point2D(app.env.oxy[f_id].x, app.env.oxy[f_id].y)
                if isFleet(f_id) and app.env.isMCoast(t_id)
                    #mc_pos = mc_move_data[f_id]
                    p2 = new Point2D(app.env.mcoasts_oxy[t_id][mc].x, app.env.mcoasts_oxy[t_id][mc].y)
                else
                    p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                #p2 = new Point2D(app.env.oxy[t_id].x, app.env.oxy[t_id].y)
                intersect = Intersection.intersectCircleLine(p2, 22, p1, p2)
                #intersect1 = Intersection.intersectCircleLine(app.env.oxy[f_id], 10, p1, p2)
                x = p1.x
                y = p1.y
                x_t = intersect.points[0].x
                y_t = intersect.points[0].y
                if time is "past" and app.game.phase().id is "next"
                    color = "#7F7F7F"
                else
                    color = "#FF7F00"
                @_drawLine(x, y, x_t, y_t, color, success)
                angle = Math.atan2(y_t-y,x_t-x)
                @_drawTriangle(angle, 10, x_t, y_t, color)
        return

    _drawLine: (x, y, x_t, y_t, color, success) ->
        @arws.ctx.beginPath()
        if not success
            @arws.ctx.setLineDash([5])
        else
            @arws.ctx.setLineDash([0])
        @arws.ctx.moveTo(x, y)
        @arws.ctx.lineTo(x_t, y_t)
        #@arws.ctx.closePath()
        @arws.ctx.strokeStyle = color
        @arws.ctx.stroke()
        return

    _drawCircle: (x, y, r, color) ->
        @arws.ctx.beginPath()
        @arws.ctx.arc(x, y, r, 0, Math.PI*2, true)
        #@arws.ctx.closePath()
        @arws.ctx.strokeStyle = color
        @arws.ctx.stroke()
        return

    _drawTriangle: (angle, headlen, x, y, color) ->
        @arws.ctx.beginPath()
        @arws.ctx.moveTo(x,y)
        @arws.ctx.lineTo(x-headlen*Math.cos(angle-Math.PI/6),y-headlen*Math.sin(angle-Math.PI/6))
        @arws.ctx.lineTo(x-headlen*Math.cos(angle+Math.PI/6),y-headlen*Math.sin(angle+Math.PI/6))
        @arws.ctx.closePath()
        @arws.ctx.fillStyle = color
        @arws.ctx.fill()
        return

    _evalSupMoveEPoint: (p0, p1, p2) ->
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

    onTerritory: (id) ->
        #var r,g,b,rr,gg,bb;
        #ccolor = r: 250, g: 0, b: 0
        ocolor = app.game.colors[id]
        ncolor = r: ocolor.r-50, g: ocolor.g-50, b: ocolor.b-50
        @colorTerritory(id, ncolor)
        return

    offTerritory: (id) ->
        ccolor = r: app.game.colors[id].r, g: app.game.colors[id].g, b: app.game.colors[id].b
        @colorTerritory(id, ccolor)
        return

window.Screen = Screen
