class Interactions
    constructor: (@app) ->
        @current = "none"
        @active = null
        @tracked = []
        #@trackedConvoys = {}
        @trackedConvoyRoutes = {}
        @_trackedConvoyRST = []
        @trackedConvoyTerrs = []
        return

    getMousePosition: (e) ->
        if not e.hasOwnProperty('offsetX')
            e.offsetX = e.layerX
        if not e.hasOwnProperty('offsetY')
            e.offsetY = e.layerY
        pos = x: e.offsetX, y: e.offsetY

    _isColorValid: (color) ->
        #: check that the color is not black
        res = false
        if color.r > 20 or color.g > 20 or color.b > 20
            res = true
        return res

    _clickCheck: (act, color) ->
        res = false
        Id = @app.env.getTerritoryByColor(color)
        #: same check and correction
        if @app.env.isSame(Id)
            Id = @app.env.same[Id]
        #: check depending on action
        switch act
            when "select"
                if (@app.game.isLastPhase()) or (@app.game.phase().id is "next")
                    if @app.game.phase().type is PHASE_TYPES.diplomacy
                        if Id in @app.game.phase().getCountryTroops()
                            res = true
                    if @app.game.phase().type is PHASE_TYPES.builds
                        bn = @app.game.canBuild()
                        if bn > 0
                            if @app.game.phase().getCountryByTerritory(Id) is @app.game.country
                                if @app.env.isSupply(Id)
                                    if not @app.game.phase().isFleet(Id) and not @app.game.phase().isArmy(Id)
                                        res = true
                        else if bn < 0
                            if Id in @app.game.phase().getCountryTroops()
                                res = true
                        else
                            # allow undo orders
                            bd = (key for key of @app.game.phase('next').builds)
                            if Id in bd
                                res = true
                    if @app.game.phase().type is PHASE_TYPES.retreats
                        #if Id in @app.game.phase().previous().getCountryTroops()
                        dlist = @app.game.phase().dislodged[@app.game.country]
                        if not dlist
                            dlist = []
                        if Id in dlist
                            res = true
            when "move"
                if Id in @tracked
                    res = true
            when "sup_hold"
                if Id in @tracked
                    res = true
            when "sup_move_from"
                if Id in @tracked
                    res = true
            when "sup_move_to"
                lst = @tracked[1..]
                console.log(lst)
                if Id in lst
                    #if Id isnt @app.env.getTerritoryByColor(@active)
                    res = true
            when "convoy_from"
                if Id in @tracked
                    res = true
            when "convoy_to"
                clen = @trackedConvoyTerrs.length + 1
                lst = @tracked[clen..]
                console.log(lst)
                if Id in lst
                    #if Id isnt @app.env.getTerritoryByColor(@active)
                    res = true
        console.log(res)
        return res

    stop: () ->
        @_offTracked()
        @app.screen.offTerritory(@active)
        @current = "none"

    click: (mpos, rpos, pos) ->
        ## TODO: add retreats and builds support
        # mpos = @getMousePosition(e)
        # pos = @app.ui._translatePosition(mpos)
        console.log("called action")
        refcolor = @app.screen.getColor(pos)
        if not @_isColorValid(refcolor)
            console.log('exiting')
            return
        do_map_upd = true
        switch @current
            when "none"
                id = @app.env.getTerritoryByColor(refcolor)
                console.log('none', 'terr', id)
                ## same check and correction
                if @app.env.isSame(id)
                    id = @app.env.same[id]
                if @_clickCheck("select", refcolor)
                    # @app.ui.setMenuButtons("open", id)
                    # @app.ui.openMenu(mpos)
                    @app.ux.relevantActionMenuOpen(rpos, id)
                    @current = "menu"
                #else
                #   @app.LoadTerrName(id)
                #   @current = "name"
                    @app.screen.onTerritory(id)
                    @active = id
                    console.log(@active, @current)
                else
                    do_map_upd = false
            #when "name"
            #   @app.HideTerrName()
            #   @app.screen.offTerritory(@active)
            #   @current = "none"
            when "menu"
                # @app.ui.setMenuButtons("reset", @active)
                # @app.ui.closeMenu()
                @app.ux.relevantActionMenuClose()
                @app.screen.offTerritory(@active)
                @current = "none"
            when "move"
                if @_clickCheck("move", refcolor)
                    @intent("move", pos)
                    @app.screen.drawLines()
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_move"
                if @_clickCheck("sup_move_from", refcolor)
                    @intent("sup_move_from", pos)
                    #@app.Terr_SupMove_To_On(refcolor)
                    #@current = "sup_move_to"
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_move_to"
                if @_clickCheck("sup_move_to", refcolor)
                    @intent("sup_move_to", pos)
                    @app.screen.drawLines()
                    if @current is "none"
                        @_offTracked()
                        @app.screen.offTerritory(@active)
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_hold"
                if @_clickCheck("sup_hold", refcolor)
                    @intent("sup_hold", pos)
                    @app.screen.drawLines()
                @_offTracked()
                @app.screen.offTerritory(@active)
                @current = "none"
            when "convoy"
                if @_clickCheck("convoy_from", refcolor)
                    @intent("convoy_from", pos)
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "convoy_to"
                if @_clickCheck("convoy_to", refcolor)
                    @intent("convoy_to", pos)
                    if @current is "none"
                        @app.screen.drawLines()
                else
                    @_offTracked()
                    @current = "none"
                #@_offTracked()
                #@app.screen.offTerritory(@active)
                #@current = "none"
            when "mcoast_move"
                ## this is called only on invalid click, so we delete the movement
                @app.game.delMove(@active)
                @app.game.moves_queue = []
                @app.screen.drawLines()
                @_offTracked()
                @app.screen.offTerritory(@active)
                @current = "none"
                @app.ui.closeMCMenu()
            when "retreat"
                if @_clickCheck("move", refcolor)
                    @intent("retreat", pos)
                    @app.screen.drawLines()
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "mcoast_retreat"
                #: this is called only on invalid click
                #@app.game.delMove(@active)
                #@app.game.moves_queue = []
                @app.screen.drawLines()
                @_offTracked()
                @app.screen.offTerritory(@active)
                @current = "none"
                @app.ui.closeMCMenu()
        if do_map_upd
            @app.screen.update()
        return

    _remapUxEvents: (action) ->
        return {
            hold: "hold",
            move: "move",
            support_hold: "sup_hold",
            support_move: "sup_move",
            convoy: "convoy",
            army: "build_army",
            fleet: "build_fleet",
            disband: "disband",
            retreat: "retreat",
            close: "close"
        }[action]

    uxEvent: (action) ->
        eve = @_remapUxEvents(action)
        @uiClick(eve)
        return

    uiClick: (eve) ->
        @current = eve
        m_id = @active
        if @app.game.phase().type is PHASE_TYPES.diplomacy
            act = @app.game.hasMove(m_id)
        if @app.game.phase().type is PHASE_TYPES.builds
            act = @app.game.hasBuild(m_id)
        if @app.game.phase().type is PHASE_TYPES.retreats
            if @app.game.hasMove(m_id)
                act = @app.game.hasMove(m_id)
            else
                act = @app.game.hasBuild(m_id)
        re_act = false
        ## check if deactivating action
        if act is eve
            re_act = true
            @current = "menu"
        console.log(re_act)
        console.log(act)
        console.log(eve)
        ## check if action present
        if act
            if eve isnt "close"
                if @app.game.phase().type is PHASE_TYPES.diplomacy
                    #console.log("deleting move")
                    ## need to check moves break on "move"
                    ##
                    #if act is "move"
                    #   to_delete = []
                    #   for key, value of @app.play.moves
                    #       if value.from is m_id
                    #           to_delete.push(key)
                    #   for i in to_delete
                    #       #delete @app.play.moves[i]
                    #       @app.DelMove(i)
                    #delete @app.play.moves[m_id]
                    @app.game.delMove(m_id)
                    @app.screen.drawLines()
                if @app.game.phase().type is PHASE_TYPES.builds
                    todel = @app.game._nphases isnt 2 or (@app.game._nphases is 2 and not re_act)
                    if todel
                        @app.game.delBuild(@active)
                        @app.screen.drawTroops()
                if @app.game.phase().type is PHASE_TYPES.retreats
                    # if was retreat -> disband
                    if act is "retreat"
                        @app.game.delMove(m_id)
                        @app.screen.drawLines()
                        #@app.game.addBuild(m_id, "disband")
                        if re_act
                            @app.game.addBuild(m_id, "disband")
            # if @app.game.phase().type is PHASE_TYPES.diplomacy
            #     @app.ux.relevantActionMenuClose()
            # if @app.game.phase().type is PHASE_TYPES.builds
            #     todel = @app.game._nphases isnt 2 or (@app.game._nphases is 2 and not re_act)
            #     if todel
            #         @app.ux.relevantActionMenuClose()
            # if @app.game.phase().type is PHASE_TYPES.retreats
            #     # @app.ui.setMenuButtons("reset", @active)
            #     if not (eve isnt "close" and @app.game.hasBuild(m_id))
            #         # @app.ui.setMenuButtons("open", @active)
            #         @app.ux.relevantActionMenuClose()
        switch eve
            when "move"
                if not re_act
                    @_onMoveTo(@active)
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
            when "sup_move"
                if not re_act
                    @_onSupportMoveFrom(@active)
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
            when "sup_hold"
                if not re_act
                    @_onSupportHold(@active)
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
            when "convoy"
                if not re_act
                    @_onConvoyFrom(@active)
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
            when "build_army"
                if not re_act
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
                    @intent("build_a", null)
            when "build_fleet"
                if not re_act
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
                    if @app.env.isMCoast(@active)
                        #position?
                        pos = @app.env.oxy[@active]
                        @app.ui.openMCMenu(pos)
                    else
                        @intent("build_f", null)
            when "retreat"
                if not re_act
                    @_onRetreatTo(@active)
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
            when "disband"
                if @app.game.phase('last').type is PHASE_TYPES.builds
                    if not re_act
                        @intent("disband", null)
                        # @app.ui.closeMenu()
                        @app.ux.relevantActionMenuClose()
                else
                    @intent("disband", null)
                    # @app.ui.closeMenu()
                    @app.ux.relevantActionMenuClose()
            when "close"
                @app.screen.offTerritory(@active)
                # @app.ui.closeMenu()
                @app.ux.relevantActionMenuClose()
                @current = "none"
        if eve isnt "close" and @app.game.ready
            @app.ui.setReady()
        @app.screen.update()
        return

    mcClick: (act) ->
        pos = x: 0, y: 0
        switch act
            ## north click
            when "mc_n"
                @intent("mcoast_n", pos)
            ## south click
            when "mc_s"
                @intent("mcoast_s", pos)
        @app.ui.closeMCMenu()
        @app.screen.drawLines()
        @app.screen.update()

    intent: (act, pos) ->
        switch act
            when "move"
                console.log("moving")
                id = @active
                color = @app.screen.getColor(pos)
                t_id = @app.env.getTerritoryByColor(color)
                ## multi-coasts check
                if @app.env.isMCoast(t_id) and @app.game.phase().isFleet(id)
                    mv_mc_lst = @app.env.moves.mc[t_id]
                    l0 = id in mv_mc_lst[0]
                    l1 = id in mv_mc_lst[1]
                    if l0 and l1
                        console.log("sei stronzo")
                        @current = "mcoast_move"
                        ## store the t_id in track_terrs
                        @_offTracked()
                        @tracked.push(t_id)
                        ccolor = r: 235, g: 0, b: 0
                        @app.screen.colorTerritory(t_id, ccolor)
                        #@app.UpdateMap()
                        @app.ui.openMCMenu(pos)
                    else
                        #if l0
                        #    @app.game.moves_mc[id] = 0
                        #else
                        #    @app.game.moves_mc[id] = 1
                        mc = if l0 then 0 else 1
                        #@app.game.moves[id] = type: "move", from: id, to: t_id
                        @_offTracked()
                        @app.screen.offTerritory(@active)
                        @current = "none"
                        @app.game.addMoveMC(id, "move", id, t_id, mc)
                else
                    #@app.game.moves[id] = type: "move", from: id, to: t_id
                    ## convoys check
                    if t_id in @trackedConvoyTerrs
                        convoys = @_getConvoysFromMove(id, t_id)
                        console.log(convoys)
                        for i in convoys
                            #@app.game.moves[i] = type: "convoy", from: id, to: t_id
                            @app.game.addMove(i, "convoy", id, t_id)
                        #@app.game.moves[id]["viaConvoy"] = true
                        #@app.game.moves[id]["convoy_route"] = convoys
                        @app.game.addMoveConvoy(id, "move", id, t_id, convoys)
                    else
                        @app.game.addMove(id, "move", id, t_id)
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_hold"
                console.log("supping hold")
                id = @active
                color = @app.screen.getColor(pos)
                t_id = @app.env.getTerritoryByColor(color)
                #@app.game.moves[id] = type: "support_hold", from: id, to: t_id
                @app.game.addMove(id, "support_hold", id, t_id)
            when "sup_move_from"
                console.log("supping move from")
                color = @app.screen.getColor(pos)
                id_f = @app.env.getTerritoryByColor(color)
                if @app.game.hasMove(id_f) is "move"
                    console.log("move present")
                    ## check move is valid..
                    nears_c = @_availableMoves("sup_move_to", id_f)
                    if @app.game.moves[id_f].dst in nears_c
                        console.log("valid sup_move movement")
                        id = @active
                        id_t = @app.game.moves[id_f].dst
                        @_offTracked()
                        @app.screen.offTerritory(@active)
                        @current = "none"
                        #@app.game.moves[id] = type: "support_move", from: id_f, to: id_t
                        if @app.game.moves[id_f].mc isnt undefined
                            @app.game.addMoveMC(id, "support_move", id_f, id_t, @app.game.moves[id_f].mc)
                        else
                            @app.game.addMove(id, "support_move", id_f, id_t)
                        @app.screen.drawLines()
                    else
                        #delete @app.game.moves[id_f]
                        #@app.DelOrder(id_f)
                        @app.game.delMove(id_f)
                        @_onSupportMoveTo(id_f)
                        @current = "sup_move_to"
                else
                    @_onSupportMoveTo(id_f)
                    @current = "sup_move_to"
                #id = @app.env.getTerritoryByColor(@active)
                #color = @app.screen.getColor(pos)
                #t_id = @app.env.getTerritoryByColor(color)
            when "sup_move_to"
                console.log("supping move to")
                id = @active
                color = @app.screen.getColor(pos)
                f_id = @tracked[0]
                t_id = @app.env.getTerritoryByColor(color)
                need_mc = false
                continue_mc = false
                #if f_id in (key for key of @app.map.troops[@app.play.country])
                if f_id in @app.game.phase().getCountryTroops()
                    if @app.env.isMCoast(t_id) and @app.game.phase().isFleet(f_id)
                        need_mc = true
                        mv_mc_lst = @app.env.moves.mc[t_id]
                        l0 = id in mv_mc_lst[0]
                        l1 = id in mv_mc_lst[1]
                        if l0 and l1
                            continue_mc = true
                            @current = "mcoast_move"
                            ## store the t_id in track_terrs
                            @app.screen.offTerritory(@active)
                            @_offTracked()
                            @tracked.push(t_id)
                            @active = f_id
                            ccolor = r: 235, g: 0, b: 0
                            @app.screen.colorTerritory(t_id, ccolor)
                            @app.screen.update()
                            # open mc selection menu
                            @app.ui.openMCMenu(pos)
                        else
                            #if l0
                            #    @app.game.moves_mc[id] = 0
                            #else
                            #    @app.game.moves_mc[id] = 1
                            # ---
                            mc = if l0 then 0 else 1
                            #@app.game.moves[id] = type: "move", from: id, to: t_id
                            #@app.game.addMove(id, "move", id, t_id)
                            #@_offTracked()
                            #@app.screen.offTerritory(@active)
                            #@current = "none"
                if not need_mc
                    @app.game.addMove(id, "support_move", f_id, t_id)
                    @app.game.addMove(f_id, "move", f_id, t_id)
                else
                    if not continue_mc
                        @app.game.addMove(id, "support_move", f_id, t_id, mc)
                        @app.game.addMoveMC(f_id, "move", f_id, t_id, mc)
                    else
                        @app.game.enqueueMove(id, "support_move", f_id, t_id)
                if not continue_mc
                    @current = "none"
            when "convoy_from"
                console.log("convoying from")
                id = @active
                @trackedConvoyTerrs.push(id)
                color = @app.screen.getColor(pos)
                f_id = @app.env.getTerritoryByColor(color)
                for i in @tracked
                    if i isnt f_id
                        ccolor = r: @app.game.colors[i].r, g: @app.game.colors[i].g, b: @app.game.colors[i].b
                        @app.screen.colorTerritory(i, ccolor)
                @tracked = [f_id, id]
                ## color the moving army
                ccolor = r: 235, g: 235, b: 0
                @app.screen.colorTerritory(f_id, ccolor)
                ## color the convoy fleet
                ccolor = r: 0, g: 235, b: 0
                @app.screen.colorTerritory(id, ccolor)
                @_onConvoyTo(@active)
                @current = "convoy_to"
            when "convoy_to"
                console.log("convoying to")
                color = @app.screen.getColor(pos)
                id = @app.env.getTerritoryByColor(color)
                f_id = @tracked[0]
                if @app.env.isCoast(id)
                    #@app.game.moves[f_id] = type: "move", from: f_id, to: id, viaConvoy: true, convoy_route: @trackedConvoyTerrs
                    @app.game.addMoveConvoy(f_id, "move", f_id, id, @trackedConvoyTerrs)
                    for i in @trackedConvoyTerrs
                        #@app.game.moves[i] = type: "convoy", from: f_id, to: id
                        @app.game.addMove(i, "convoy", f_id, id)
                    @_offTracked()
                    @current = "none"
                    #@app.screen.drawLines()
                else
                    @trackedConvoyTerrs.push(id)
                    for i in @tracked
                        if i isnt f_id
                            if i not in @trackedConvoyTerrs
                                ccolor = r: @app.game.colors[i].r, g: @app.game.colors[i].g, b: @app.game.colors[i].b
                                @app.screen.colorTerritory(i, ccolor)
                    @tracked = [f_id]
                    for i in @trackedConvoyTerrs
                        @tracked.push(i)
                    ## color the new convoy fleet
                    ccolor = r: 0, g: 235, b: 0
                    @app.screen.colorTerritory(id, ccolor)
                    @_onConvoyTo(id)
            when "mcoast_n"
                id = @active
                t_id = if @app.game.phase().type isnt PHASE_TYPES.builds then @tracked[0] else @active
                mv_mc_lst = @app.env.mcoasts_oxy[t_id]
                if mv_mc_lst[0].y < mv_mc_lst[1].y
                    mc_n = 0
                    mc_s = 1
                else
                    mc_n = 1
                    mc_s = 0
                console.log(mc_n)
                #@app.game.moves_mc[id] = mc_n
                #@app.game.moves[id] = type: "move", from: id, to: t_id
                #if @app.game.phase().type isnt "builds"
                if @app.game.phase().type is PHASE_TYPES.builds
                    @app.game.addBuild(t_id, "build_fleet", mc_n)
                    @app.screen.drawTroops()
                else if @app.game.phase().type is PHASE_TYPES.retreats
                    @app.game.delBuild(id)
                    @app.game.addMoveMC(id, "retreat", id, t_id, mc_n)
                    @_offTracked()
                else
                    if @app.game.moves_queue.length
                        qm = @app.game.dequeueMove()
                        @app.game.addMoveMC(qm.id, qm.type, qm.from, qm.dst, mc_n)
                    console.log("adding mcmove with diplomacy phase")
                    @app.game.addMoveMC(id, "move", id, t_id, mc_n)
                    @_offTracked()
                @app.screen.offTerritory(@active)
                @current = "none"
            when "mcoast_s"
                id = @active
                t_id = if @app.game.phase().type isnt PHASE_TYPES.builds then @tracked[0] else @active
                mv_mc_lst = @app.env.mcoasts_oxy[t_id]
                if mv_mc_lst[0].y < mv_mc_lst[1].y
                    mc_n = 0
                    mc_s = 1
                else
                    mc_n = 1
                    mc_s = 0
                console.log(mc_s)
                #@app.game.moves_mc[id] = mc_s
                #@app.game.moves[id] = type: "move", from: id, to: t_id
                if @app.game.phase().type is PHASE_TYPES.builds
                    @app.game.addBuild(t_id, "build_fleet", mc_s)
                    @app.screen.drawTroops()
                else if @app.game.phase().type is PHASE_TYPES.retreats
                    @app.game.delBuild(id)
                    @app.game.addMoveMC(id, "retreat", id, t_id, mc_s)
                    @_offTracked()
                else
                    if @app.game.moves_queue.length
                        qm = @app.game.dequeueMove()
                        @app.game.addMoveMC(qm.id, qm.type, qm.from, qm.dst, mc_s)
                    console.log("adding mcmove with diplomacy phase")
                    @app.game.addMoveMC(id, "move", id, t_id, mc_s)
                    @_offTracked()
                @app.screen.offTerritory(@active)
                @current = "none"
            when "build_a"
                @app.game.addBuild(@active, "build_army")
                @app.screen.offTerritory(@active)
                @current = "none"
                @app.screen.drawTroops()
            when "build_f"
                @app.game.addBuild(@active, "build_fleet")
                @app.screen.offTerritory(@active)
                @current = "none"
                @app.screen.drawTroops()
            when "retreat"
                id = @active
                color = @app.screen.getColor(pos)
                t_id = @app.env.getTerritoryByColor(color)
                ## multi-coasts check
                if @app.env.isMCoast(t_id) and @app.game.phase('last').previous().isFleet(id)
                    mv_mc_lst = @app.env.moves.mc[t_id]
                    l0 = id in mv_mc_lst[0]
                    l1 = id in mv_mc_lst[1]
                    if l0 and l1
                        @current = "mcoast_retreat"
                        ## store the t_id in track_terrs
                        @_offTracked()
                        @tracked.push(t_id)
                        ccolor = r: 235, g: 0, b: 0
                        @app.screen.colorTerritory(t_id, ccolor)
                        #@app.UpdateMap()
                        @app.ui.openMCMenu(pos)
                    else
                        mc = if l0 then 0 else 1
                        @_offTracked()
                        @app.screen.offTerritory(@active)
                        @current = "none"
                        @app.game.delBuild(id)
                        @app.game.addMoveMC(id, "retreat", id, t_id, mc)
                else
                    @app.game.delBuild(id)
                    @app.game.addMove(id, "retreat", id, t_id)
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "disband"
                if @app.game.phase('last').type is PHASE_TYPES.builds
                    @app.game.addBuild(@active, "disband")
                    @app.screen.offTerritory(@active)
                    @current = "none"
                    @app.screen.drawTroops()
                else

        ## next phase auto swithing
        if @app.game.phase().id isnt "next" and @app.game.gotOrders()
            # @app.game.loadPhase("next", false)
            @app.game.movePhaseToNext()
        return

    _offTracked: ->
        for i in @tracked
            @app.screen.offTerritory(i)
        @tracked = []
        #@trackedConvoys = {}
        @trackedConvoyRoutes = {}
        @_trackedConvoyRST = []
        @trackedConvoyTerrs = []

    _onMoveTo: (id) ->
        nears = @_availableMoves("move", id)
        nears_c = @_availableMoves("move_convoy", id)
        for i in nears
            @tracked.push(i)
            #ocolor = @app.game.colors[i]
            #ncolor = r: ocolor.r+30, g: ocolor.g+30, b: ocolor.b+30
            ncolor = r: 235, g: 0, b: 0
            @app.screen.colorTerritory(i, ncolor)
        for i in nears_c
            if i not in @tracked
                @tracked.push(i)
                ncolor = r: 0, g: 0, b: 235
                @app.screen.colorTerritory(i, ncolor)
        #@app.play.track_convoy = nears_c
        return

    _onSupportHold: (id) ->
        @tracked = @_availableMoves("sup_hold", id)
        for i in @tracked
            #ocolor = @app.game.colors[i]
            #ncolor = r: ocolor.r+30, g: ocolor.g+30, b: ocolor.b+30
            ncolor = r: 0, g: 235, b: 0
            @app.screen.colorTerritory(i, ncolor)
        return

    _onSupportMoveTo: (id) ->
        ## deactivate past colored terrs
        for i in @tracked
            if i isnt id
                ccolor = r: @app.game.colors[i].r, g: @app.game.colors[i].g, b: @app.game.colors[i].b
                @app.screen.colorTerritory(i, ccolor)
        @tracked = [id]
        ## activate new terrs
        nears = @_availableMoves("sup_move_to", id)
        for i in nears
            @tracked.push(i)
        console.log(@tracked)
        for i in @tracked
            if i isnt id
                #ocolor = @app.game.colors[i]
                ncolor = r: 235, g: 0, b: 0
                @app.screen.colorTerritory(i, ncolor)
        return

    _onSupportMoveFrom: (id) ->
        @tracked = @_availableMoves("sup_move_from", id)
        console.log(@tracked)
        for i in @tracked
            #ocolor = @app.game.colors[i]
            #ncolor = r: ocolor.r+30, g: ocolor.g+30, b: ocolor.b+30
            ncolor = r: 235, g: 235, b: 0
            @app.screen.colorTerritory(i, ncolor)
        return

    _onConvoyFrom: (id) ->
        @tracked = @_availableMoves("convoy_from", id)
        for i in @tracked
            ncolor = r: 0, g: 0, b: 235
            @app.screen.colorTerritory(i, ncolor)
        return

    _onConvoyTo: (id) ->
        nears_s = @_availableMoves("convoy_to_fleet", id)
        nears_t = @_availableMoves("convoy_to_terr", id)
        id_f = @tracked[0]
        #moves_f = @app.map.moves.armies[id_f]
        for i in nears_s
            @tracked.push(i)
            ncolor = r: 0, g: 0, b: 235
            @app.screen.colorTerritory(i, ncolor)
        for i in nears_t
            if i isnt id_f
                #if i not in moves_f
                @tracked.push(i)
                ncolor = r: 235, g: 0, b: 0
                @app.screen.colorTerritory(i, ncolor)
        console.log(@tracked)
        return

    _onRetreatTo: (id) ->
        @tracked = @_availableMoves("retreat", id)
        for i in @tracked
            ncolor = r: 235, g: 0, b: 0
            @app.screen.colorTerritory(i, ncolor)
        return

    _availableMoves: (act, id_f) ->
        nears_res = []
        switch act
            when "move"
                if @app.game.phase().isArmy(id_f)
                    nears_res = @app.env.moves.armies[id_f]
                else
                    ## check multicoasts
                    if @app.env.isMCoast(id_f)
                        mc_pos = @app.game.phase().mcpos[id_f]
                        nears_res = @app.env.moves.mc[id_f][mc_pos]
                    else
                        nears_res = @app.env.moves.fleets[id_f]
            when "move_convoy"
                nears_res = []
                if not @app.game.phase().isFleet(id_f)
                    army_links = @app.env.moves.armies[id_f]
                    fleet_links = @app.env.moves.fleets[id_f]
                    if not fleet_links
                        fleet_links = []
                    examine = []
                    for terr in fleet_links
                        if @app.game.phase().isFleet(terr) and @app.env.isSea(terr)
                            examine.push([terr, 1])
                    _routes = [[]]
                    step = 1
                    index = 0
                    while examine.length > 0
                        data = examine.shift()
                        element = data[0]
                        elstep = data[1]
                        etype = "fleet"
                        if not (@app.game.phase().isFleet(element) and @app.env.isSea(element))
                            if @app.env.isCoast(element)
                                etype = "coast"
                            else
                                if examine.length isnt 0
                                    index++
                                    _routes.push(_routes.last()[0..examine[0][1]-2])
                                continue
                        if element in _routes[index]
                            if examine.length isnt 0
                                index++
                                _routes.push(_routes.last()[0..examine[0][1]-2])
                            continue
                        if elstep > step
                            step++
                        if elstep < step
                            index++
                            if elstep > 1
                                _routes.push(_routes.last()[0..elstep-2])
                            else
                                _routes.push([])
                            step = elstep
                        if etype is "fleet"
                            #: add node to processing list
                            _routes[index].push(element)
                            node_links = @app.env.moves.fleets[element]
                            for node in node_links
                                if node not in [element, id_f]
                                    examine.insert(0, [node, step+1])
                        else
                            #: close the route
                            if @trackedConvoyRoutes[id_f+"_"+element] is undefined
                                @trackedConvoyRoutes[id_f+"_"+element] = []
                            @trackedConvoyRoutes[id_f+"_"+element].push(_routes[index])
                            if element not in nears_res and element not in army_links and element isnt id_f
                                nears_res.push(element)
                            if examine.length isnt 0
                                if examine[0][1] is step
                                    index++
                                    _routes.push(_routes.last()[0..step-2])
                    #@trackedConvoys = nears_s
                    @trackedConvoyTerrs = nears_res
            when "sup_hold"
                if @app.game.phase().isArmy(id_f)
                    nears = @app.env.moves.armies[id_f]
                else
                    nears = @app.env.moves.fleets[id_f]
                for i in nears
                    #if i in @app.map.troops_lst or i in @app.map.fleets_lst
                    if i in @app.game.phase().listArmies or i in @app.game.phase().listFleets
                        nears_res.push(i)
            when "sup_move_to"
                nears_o = []
                nears_f = []
                id_o = @active
                if @app.game.phase().isArmy(id_o)
                    nears_o = @app.env.moves.armies[id_o]
                else
                    nears_o = @app.env.moves.fleets[id_o]
                console.log(id_f)
                if @app.game.phase().isArmy(id_f)
                    nears_f = @app.env.moves.armies[id_f]
                else
                    nears_f = @app.env.moves.fleets[id_f]
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
                if @app.game.phase().isArmy(id_f)
                    if @app.env.moves.fleets[id_f]
                        for i in @app.env.moves.fleets[id_f]
                            if @app.game.phase().isFleet(i) and @app.env.isSea(i)
                                nears_s[i] = 1
                console.log(nears_s)
                console.log(isObjectEmpty(nears_s))
                done = isObjectEmpty(nears_s)
                console.log(done)
                while not done
                    found = false
                    for key, value of nears_s
                        nears_t = @app.env.moves.fleets[key]
                        #found = false
                        for j in nears_t
                            if j not in (key for key of nears_s)
                                if @app.game.phase().isFleet(j) and @app.env.isSea(j)
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
                    nears_t = @app.env.moves.fleets[key]
                    for j in nears_t
                        if j isnt id_f
                            if not @app.env.isSea(j)
                                if j not in nears_c
                                    nears_c.push(j)
                for i in nears_c
                    if i in nears_o
                        nears_res.push(i)
            when "sup_move_from"
                if @app.game.phase().isArmy(id_f)
                    nears = @app.env.moves.armies[id_f]
                else
                    if @app.env.isMCoast(id_f)
                        mc_pos = @app.game.phase().mcpos[id_f]
                        nears = @app.env.moves.mc[id_f][mc_pos]
                    else
                        nears = @app.env.moves.fleets[id_f]
                console.log(nears)
                for i in nears
                    f_nears = []
                    if @app.env.moves.fleets[i]
                        for j in @app.env.moves.fleets[i]
                            if j isnt id_f and @app.game.phase().isFleet(j)
                                f_nears.push(j)
                    if @app.env.moves.armies[i]
                        for j in @app.env.moves.armies[i]
                            if j isnt id_f and @app.game.phase().isArmy(j)
                                f_nears.push(j)
                    #console.log(f_nears)
                    for j in f_nears
                        if j not in nears_res
                            #if j in @app.map.troops_lst or j in @app.map.fleets_lst
                            nears_res.push(j)
                ## via Convoy
                ## HOW TO?
                #c_nears = []
                #for key, j in @app.play.orders
                #   if j.type is "move" and j.viaConvoy isnt null and j.dst in nears
                #       c_nears.push(key)
                #console.log(c_nears)
                #for j in c_nears
                #   if j not in nears_res
                #       nears_res.push(j)
                nears_s = {}
                for i in nears
                    if @app.env.moves.fleets[i]
                        for j in @app.env.moves.fleets[i]
                            if @app.game.phase().isFleet(j) and @app.env.isSea(j)
                                nears_s[j] = 1
                console.log(nears_s)
                console.log(isObjectEmpty(nears_s))
                done = isObjectEmpty(nears_s)
                console.log(done)
                while not done
                    found = false
                    for key, value of nears_s
                        nears_t = @app.env.moves.fleets[key]
                        for j in nears_t
                            if j not in (key for key of nears_s)
                                if @app.game.phase().isFleet(j) and @app.env.isSea(j)
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
                    nears_t = @app.env.moves.fleets[key]
                    for j in nears_t
                        if j isnt id_f
                            #if j not in @app.map.seas
                            if not @app.env.isSea(j)
                                if @app.game.phase().isArmy(j)
                                    if j not in nears_res
                                        nears_res.push(j)
            when "convoy_from"
                nears = @app.env.moves.fleets[id_f]
                for i in nears
                    if @app.env.isCoast(i) and @app.game.phase().isArmy(i)
                        nears_res.push(i)
            when "convoy_to_fleet"
                nears = @app.env.moves.fleets[id_f]
                for i in nears
                    if i not in @trackedConvoyTerrs
                        if @app.env.isSea(i) and @app.game.phase().isFleet(i)
                            nears_res.push(i)
            when "convoy_to_terr"
                nears = @app.env.moves.fleets[id_f]
                for i in nears
                    if @app.env.isCoast(i)
                        nears_res.push(i)
            when "retreat"
                if @app.game.phase('last').previous().isArmy(id_f)
                    nears = @app.env.moves.armies[id_f]
                else
                    #: check multicoasts
                    if @app.env.isMCoast(id_f)
                        mc_pos = @app.game.phase('last').previous().mcpos[id_f]
                        nears = @app.env.moves.mc[id_f][mc_pos]
                    else
                        nears = @app.env.moves.fleets[id_f]
                for i in nears
                    #: don't track occupied territories
                    if @app.game.phase().isArmy(i) or @app.game.phase().isFleet(i)
                        continue
                    #: don't track prior moves to terr
                    skip = false
                    for country, orders of @app.game.phase('last').previous().orders
                        for oid, odata of orders
                            if odata.type is "move" and odata.dst is i
                                skip = true
                                break
                            if oid is i and odata.type is "move" and odata.dst is @active
                                skip = true
                                break
                    if skip
                        continue
                    nears_res.push(i)
        return nears_res

    _OLDgetConvoysFromMove: (id_f, id_t) ->
        conv_lst = []
        #country = @app.FindCountry(id_f)
        #id_t = @app.play.moves[id_f].dst
        nears_t = @app.env.moves.fleets[id_t]
        console.log(nears_t)
        val = 0
        for i, v of @trackedConvoys
            if v > val
                val = v
        console.log(val)
        #val = 10
        for i in nears_t
            conv_val = @trackedConvoys[i]
            if conv_val
                console.log(conv_val)
                if conv_val < val
                    val = conv_val
                    console.log(val)
        ## multi ROUTE?? how TO?
        routes = []
        for key, value of @trackedConvoys
            if value <= val
                if not routes[value-1]
                    routes[value-1] = []
                #conv_lst.push(key)
                routes[value-1].push(key)
        console.log(routes)
        ##for route in routes
        #country_troops = @app.GetCountryTroops(@app.play.country)
        country_troops = @app.game.phase().getCountryTroops()
        for i in [0..routes.length-1]
            route = routes[i]
            console.log(route)
            if route.length > 1
                #arm_dict = @app.map.troops[country]
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

    _getConvoysFromMove: (id_f, id_t) ->
        #console.log(@trackedConvoys)
        console.log(@trackedConvoyRoutes)
        console.log(@_trackedConvoyRST)
        choosen = false
        choice = null
        choices = []
        routes = @trackedConvoyRoutes[id_f+"_"+id_t]
        for route in routes
            allmine = true
            for t in route
                if t not in @app.game.phase().getCountryTroops()
                    allmine = false
                    break
            chdata =
                data: route
                mine: allmine
            choices.push(chdata)
        for ch in choices
            if ch.mine
                choice = ch.data
                choosen = true
                break
        console.log(routes)
        console.log(choices)
        console.log(choosen)
        if not choosen
            choice = choices[0].data
        return choice

window.Interactions = Interactions
