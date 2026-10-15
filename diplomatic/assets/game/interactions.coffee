class Interactions
    constructor: (@app) ->
        @current = "none"
        @active = null
        @tracked = []
        #@trackedConvoys = {}
        @trackedConvoyRoutes = {}
        @_trackedConvoyRST = []
        @trackedConvoyTerrs = []
        @_lastRpos =
            x: 0
            y: 0
        return

    getMousePosition: (e) ->
        if not e.hasOwnProperty('offsetX')
            e.offsetX = e.layerX
        if not e.hasOwnProperty('offsetY')
            e.offsetY = e.layerY
        pos = x: e.offsetX, y: e.offsetY

    #: can the player start an order on this province in the viewed step? (board marks those as actionable)
    canSelect: (id) ->
        return false if @app.game.ready or not @app.game.canOrder
        return @_clickCheck("select", id)

    _clickCheck: (act, Id) ->
        res = false
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
                            bd = (key for key of @app.game.builds)
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
                if Id in lst
                    #if Id isnt @app.env.getTerritoryByColor(@active)
                    res = true
            when "convoy_from"
                if Id in @tracked
                    res = true
            when "convoy_to"
                clen = @trackedConvoyTerrs.length + 1
                lst = @tracked[clen..]
                if Id in lst
                    #if Id isnt @app.env.getTerritoryByColor(@active)
                    res = true
        return res

    stop: () ->
        @_offTracked()
        @app.screen.offTerritory(@active)
        @current = "none"

    #: drop whatever is being built: highlights off, menus closed, queued moves forgotten, state none
    #: (Esc, the popover's close, an invalid click while choosing a coast)
    cancel: ->
        @_offTracked()
        @app.screen.offTerritory(@active) if @active?
        @app.game.moves_queue = []
        @app.ux.relevantActionMenuClose()
        @current = "none"
        @app.screen.drawLines()
        return

    click: (id, rpos) ->
        #: id: the clicked province (row id, from the SVG); rpos: the click position, for menus
        @_lastRpos = rpos
        if @app.game.ready
            @app.ux.alert("You can't add new orders since you set yourself as ready", true, 5)
            return
        if not id?
            return
        do_map_upd = true
        auto_switch_step = false
        switch @current
            when "none"
                if @_clickCheck("select", id)
                    @app.ux.relevantActionMenuOpen(rpos, id)
                    @current = "menu"
                #else
                #   @app.LoadTerrName(id)
                #   @current = "name"
                    @app.screen.onTerritory(id)
                    @active = id
                    auto_switch_step = true
                else
                    do_map_upd = false
            #when "name"
            #   @app.HideTerrName()
            #   @app.screen.offTerritory(@active)
            #   @current = "none"
            when "menu"
                @app.ux.relevantActionMenuClose()
                @app.screen.offTerritory(@active)
                @current = "none"
            when "move"
                if @_clickCheck("move", id)
                    @intent("move", id)
                    @app.screen.drawLines()
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_move"
                if @_clickCheck("sup_move_from", id)
                    @intent("sup_move_from", id)
                    #@app.Terr_SupMove_To_On(id)
                    #@current = "sup_move_to"
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_move_to"
                if @_clickCheck("sup_move_to", id)
                    @intent("sup_move_to", id)
                    @app.screen.drawLines()
                    if @current is "none"
                        @_offTracked()
                        @app.screen.offTerritory(@active)
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "sup_hold"
                if @_clickCheck("sup_hold", id)
                    @intent("sup_hold", id)
                    @app.screen.drawLines()
                @_offTracked()
                @app.screen.offTerritory(@active)
                @current = "none"
            when "convoy"
                if @_clickCheck("convoy_from", id)
                    @intent("convoy_from", id)
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
            when "convoy_to"
                if @_clickCheck("convoy_to", id)
                    @intent("convoy_to", id)
                    if @current is "none"
                        @app.screen.drawLines()
                else
                    @_offTracked()
                    @current = "none"
                #@_offTracked()
                #@app.screen.offTerritory(@active)
                #@current = "none"
            when "mcoast_move", "mcoast_retreat", "build_fleet"
                ## a map click while the coast menu waits cancels the order being built
                ## (build_fleet: the coast menu of a fleet build on a multi-coast centre)
                if @app.game.moves[@active]
                    @app.game.delMove(@active)
                @cancel()
            when "retreat"
                if @_clickCheck("move", id)
                    @intent("retreat", id)
                    @app.screen.drawLines()
                else
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
        if do_map_upd
            @app.screen.update()
        if auto_switch_step and @app.game.phase().id isnt "next"
            @app.game.movePhaseToNext()
        return

    _remapUxEvents: (action) ->
        return {
            hold: "hold",
            move: "move",
            support_hold: "sup_hold",
            support_move: "sup_move",
            convoy: "convoy",
            build_army: "build_army",
            build_fleet: "build_fleet",
            disband: "disband",
            retreat: "retreat",
            close: "close"
        }[action]

    #: the popover's actions; `coast:<Name>` picks a coast by its name (env.coastNames); unknown
    #: actions are ignored
    uxEvent: (action) ->
        return unless typeof action is "string"
        if action.indexOf("coast:") is 0
            @mcClick(action.slice(6))
            return
        eve = @_remapUxEvents(action)
        return unless eve?
        @uiClick(eve)
        return

    #: the stored order type for a menu event (moves keep support_hold/support_move)
    _storedType: (eve) ->
        return {sup_hold: "support_hold", sup_move: "support_move"}[eve] or eve

    uiClick: (eve) ->
        if eve is "close"
            @cancel()
            return
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
        ## re-picking the order's own action deactivates it only for actions without a target (hold,
        ## builds, disband); for targeted ones (move, supports, convoy, retreat) it clears the order
        ## below and goes straight into picking the new target
        if eve in ["hold", "build_army", "build_fleet", "disband"]
            if act is @_storedType(eve) or (act is false and eve is "hold")
                re_act = true
                @current = "menu"
        ## check if action present
        if (act and eve isnt "close")
            if @app.game.phase().type is PHASE_TYPES.diplomacy
                @app.game.delMove(m_id)
                @app.screen.drawLines()
            if @app.game.phase().type is PHASE_TYPES.builds
                @app.game.delBuild(@active)
                @app.screen.drawTroops()
            if @app.game.phase().type is PHASE_TYPES.retreats
                # a cleared retreat falls back to the phase's default, disband (re-targeting replaces it)
                if act is "retreat"
                    @app.game.delMove(m_id)
                    @app.screen.drawLines()
                    @app.game.addBuild(m_id, "disband")
                    @app.screen.drawTroops()
        switch eve
            when "hold"
                if not re_act
                    @app.ux.relevantActionMenuClose()
                    @stop()
            when "move"
                if not re_act
                    @_onMoveTo(@active)
                    @app.ux.relevantActionMenuClose()
            when "sup_move"
                if not re_act
                    @_onSupportMoveFrom(@active)
                    @app.ux.relevantActionMenuClose()
            when "sup_hold"
                if not re_act
                    @_onSupportHold(@active)
                    @app.ux.relevantActionMenuClose()
            when "convoy"
                if not re_act
                    @_onConvoyFrom(@active)
                    @app.ux.relevantActionMenuClose()
            when "build_army"
                if not re_act
                    @app.ux.relevantActionMenuClose()
                    @intent("build_a", null)
            when "build_fleet"
                if not re_act
                    @app.ux.relevantActionMenuClose()
                    if @app.env.isMCoast(@active)
                        @app.ux.menuOpen("coast", {position: @_lastRpos, territory: @active})
                    else
                        @intent("build_f", null)
            when "retreat"
                if not re_act
                    @_onRetreatTo(@active)
                    @app.ux.relevantActionMenuClose()
            when "disband"
                if @app.game.phase().type is PHASE_TYPES.builds
                    if not re_act
                        @intent("disband", null)
                        @app.ux.relevantActionMenuClose()
                else
                    @intent("disband", null)
                    @app.ux.relevantActionMenuClose()
        # if eve isnt "close" and @app.game.ready
        #     @app.ui.setReady()
        @app.screen.update()
        return

    #: the multi-coast territory the coast menu is about: the target of a move/retreat (tracked), the
    #: selected centre of a fleet build
    _coastTerritory: ->
        return if @app.game.phase().type isnt PHASE_TYPES.builds then @tracked[0] else @active

    #: a coast chosen by name in the coast menu; the engine and the wire speak the coast's index
    mcClick: (name) ->
        t_id = @_coastTerritory()
        index = (@app.env.coastNames[t_id] or []).indexOf(name)
        if t_id? and index >= 0
            @intent("mcoast", null, index)
        @app.ux.menuClose("coast")
        @app.screen.drawLines()
        @app.screen.update()
        return

    intent: (act, tid, coast=null) ->
        #: tid: the province the intent targets (row id), null for menu-driven intents;
        #: coast: the coast index, for "mcoast"
        switch act
            when "move"
                id = @active
                t_id = tid
                ## multi-coasts check
                if @app.env.isMCoast(t_id) and @app.game.phase().isFleet(id)
                    mv_mc_lst = @app.env.moves.mc[t_id]
                    l0 = id in mv_mc_lst[0]
                    l1 = id in mv_mc_lst[1]
                    if l0 and l1
                        @current = "mcoast_move"
                        ## store the t_id in track_terrs
                        @_offTracked()
                        @tracked.push(t_id)
                        @app.screen.markTerritory(t_id, "dest")
                        #@app.UpdateMap()
                        @app.ux.menuOpen("coast", {position: @_lastRpos, territory: t_id})
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
                id = @active
                t_id = tid
                #@app.game.moves[id] = type: "support_hold", from: id, to: t_id
                @app.game.addMove(id, "support_hold", id, t_id)
            when "sup_move_from"
                id_f = tid
                if @app.game.hasMove(id_f) is "move"
                    ## check move is valid..
                    nears_c = @_availableMoves("sup_move_to", id_f)
                    if @app.game.moves[id_f].dst in nears_c
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
                        #: the supported unit's own order is left alone: a support's src/dst are independent of
                        #: what that unit actually ordered; offer the destinations supportable from here
                        @_onSupportMoveTo(id_f)
                        @current = "sup_move_to"
                else
                    @_onSupportMoveTo(id_f)
                    @current = "sup_move_to"
                #id = @app.env.getTerritoryByColor(@active)
                #color = @app.screen.getColor(pos)
                #t_id = @app.env.getTerritoryByColor(color)
            when "sup_move_to"
                id = @active
                f_id = @tracked[0]
                t_id = tid
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
                            @app.screen.markTerritory(t_id, "dest")
                            @app.screen.update()
                            # open mc selection menu
                            @app.ux.menuOpen("coast", {position: @_lastRpos, territory: t_id})
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
                id = @active
                @trackedConvoyTerrs.push(id)
                f_id = tid
                for i in @tracked
                    if i isnt f_id
                        @app.screen.offTerritory(i)
                @tracked = [f_id, id]
                ## color the moving army
                @app.screen.markTerritory(f_id, "source")
                ## color the convoy fleet
                @app.screen.markTerritory(id, "support")
                @_onConvoyTo(@active)
                @current = "convoy_to"
            when "convoy_to"
                id = tid
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
                                @app.screen.offTerritory(i)
                    @tracked = [f_id]
                    for i in @trackedConvoyTerrs
                        @tracked.push(i)
                    ## color the new convoy fleet
                    @app.screen.markTerritory(id, "support")
                    @_onConvoyTo(id)
            when "mcoast"
                #: the coast menu answered (coast: index in env.coastNames[t_id])
                id = @active
                t_id = @_coastTerritory()
                if @app.game.phase().type is PHASE_TYPES.builds
                    @app.game.addBuild(t_id, "build_fleet", coast)
                    @app.screen.drawTroops()
                else if @app.game.phase().type is PHASE_TYPES.retreats
                    @app.game.delBuild(id)
                    @app.game.addMoveMC(id, "retreat", id, t_id, coast)
                    @_offTracked()
                else
                    if @app.game.moves_queue.length
                        qm = @app.game.dequeueMove()
                        @app.game.addMoveMC(qm.id, qm.type, qm.src, qm.dst, coast)
                    @app.game.addMoveMC(id, "move", id, t_id, coast)
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
                t_id = tid
                ## multi-coasts check
                if @app.env.isMCoast(t_id) and @app.game.phase().prev.isFleet(id)
                    mv_mc_lst = @app.env.moves.mc[t_id]
                    l0 = id in mv_mc_lst[0]
                    l1 = id in mv_mc_lst[1]
                    if l0 and l1
                        @current = "mcoast_retreat"
                        ## store the t_id in track_terrs
                        @_offTracked()
                        @tracked.push(t_id)
                        @app.screen.markTerritory(t_id, "dest")
                        #@app.UpdateMap()
                        @app.ux.menuOpen("coast", {position: @_lastRpos, territory: t_id})
                    else
                        mc = if l0 then 0 else 1
                        @_offTracked()
                        @app.screen.offTerritory(@active)
                        @current = "none"
                        @app.game.delBuild(id)
                        @app.game.addMoveMC(id, "retreat", id, t_id, mc)
                        @app.screen.drawTroops()
                else
                    @app.game.delBuild(id)
                    @app.game.addMove(id, "retreat", id, t_id)
                    @_offTracked()
                    @app.screen.offTerritory(@active)
                    @current = "none"
                    @app.screen.drawTroops()
            when "disband"
                if @app.game.phase().type is PHASE_TYPES.builds
                    @app.game.addBuild(@active, "disband")
                    @app.screen.offTerritory(@active)
                    @current = "none"
                    @app.screen.drawTroops()
                else
                    if @app.game.hasMove(@active)
                        @app.game.delMove(@active)
                        @app.screen.drawLines()
                    @app.game.addBuild(@active, "disband")
                    @app.screen.offTerritory(@active)
                    @current = "none"
                    @app.screen.drawTroops()
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
            @app.screen.markTerritory(i, "dest")
        for i in nears_c
            if i not in @tracked
                @tracked.push(i)
                @app.screen.markTerritory(i, "convoy")
        #@app.play.track_convoy = nears_c
        return

    _onSupportHold: (id) ->
        @tracked = @_availableMoves("sup_hold", id)
        for i in @tracked
            @app.screen.markTerritory(i, "support")
        return

    _onSupportMoveTo: (id) ->
        ## deactivate past colored terrs
        for i in @tracked
            if i isnt id
                @app.screen.offTerritory(i)
        @tracked = [id]
        ## activate new terrs
        nears = @_availableMoves("sup_move_to", id)
        for i in nears
            @tracked.push(i)
        for i in @tracked
            if i isnt id
                @app.screen.markTerritory(i, "dest")
        return

    _onSupportMoveFrom: (id) ->
        @tracked = @_availableMoves("sup_move_from", id)
        for i in @tracked
            @app.screen.markTerritory(i, "source")
        return

    _onConvoyFrom: (id) ->
        @tracked = @_availableMoves("convoy_from", id)
        for i in @tracked
            @app.screen.markTerritory(i, "convoy")
        return

    _onConvoyTo: (id) ->
        nears_s = @_availableMoves("convoy_to_fleet", id)
        nears_t = @_availableMoves("convoy_to_terr", id)
        id_f = @tracked[0]
        #moves_f = @app.map.moves.armies[id_f]
        for i in nears_s
            @tracked.push(i)
            @app.screen.markTerritory(i, "convoy")
        for i in nears_t
            if i isnt id_f
                #if i not in moves_f
                @tracked.push(i)
                @app.screen.markTerritory(i, "dest")
        return

    _onRetreatTo: (id) ->
        @tracked = @_availableMoves("retreat", id)
        for i in @tracked
            @app.screen.markTerritory(i, "dest")
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
                    army_links = @app.env.moves.armies[id_f] or []
                    convoys = (id) => @app.game.phase().isFleet(id) and @app.env.isSea(id)
                    routes = {}
                    walk = (node, chain) =>
                        for link in @app.env.moves.fleets[node] or []
                            if @app.env.isCoast(link) and link isnt id_f
                                (routes[link] ?= []).push(chain)
                            else if convoys(link) and link not in chain
                                walk(link, chain.concat([link]))
                        return
                    for sea in @app.env.moves.fleets[id_f] or []
                        walk(sea, [sea]) if convoys(sea)
                    for dst, chains of routes
                        @trackedConvoyRoutes[id_f + "_" + dst] = chains
                        nears_res.push(dst) if dst not in army_links
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
                if @app.game.phase().isArmy(id_f)
                    nears_f = @app.env.moves.armies[id_f]
                else
                    nears_f = @app.env.moves.fleets[id_f]
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
                done = isObjectEmpty(nears_s)
                while not done
                    found = false
                    for key, value of nears_s
                        nears_t = @app.env.moves.fleets[key]
                        #found = false
                        for j in nears_t
                            if j not in (key for key of nears_s)
                                if @app.game.phase().isFleet(j) and @app.env.isSea(j)
                                    nears_s[j] = value + 1
                                    found = true
                                    break
                        if found
                            break
                    if not found
                        done = true
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
                #for j in c_nears
                #   if j not in nears_res
                #       nears_res.push(j)
                nears_s = {}
                for i in nears
                    if @app.env.moves.fleets[i]
                        for j in @app.env.moves.fleets[i]
                            if @app.game.phase().isFleet(j) and @app.env.isSea(j)
                                nears_s[j] = 1
                done = isObjectEmpty(nears_s)
                while not done
                    found = false
                    for key, value of nears_s
                        nears_t = @app.env.moves.fleets[key]
                        for j in nears_t
                            if j not in (key for key of nears_s)
                                if @app.game.phase().isFleet(j) and @app.env.isSea(j)
                                    nears_s[j] = value + 1
                                    found = true
                                    break
                        if found
                            break
                    if not found
                        done = true
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
                if @app.game.phase().prev.isArmy(id_f)
                    nears = @app.env.moves.armies[id_f]
                else
                    #: check multicoasts
                    if @app.env.isMCoast(id_f)
                        mc_pos = @app.game.phase().prev.mcpos[id_f]
                        nears = @app.env.moves.mc[id_f][mc_pos]
                    else
                        nears = @app.env.moves.fleets[id_f]
                for i in nears
                    #: don't track occupied territories
                    if @app.game.phase().isArmy(i) or @app.game.phase().isFleet(i)
                        continue
                    #: don't track prior moves to terr
                    skip = false
                    for country, orders of @app.game.phase().prev.orders
                        for odata in orders
                            if odata.type is undefined
                                continue
                            if odata.type is ORDER_TYPES.move and odata.data.dst is i
                                skip = true
                                break
                            if odata.territory is i and odata.type is ORDER_TYPES.move and odata.data.dst is @active
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
        val = 0
        for i, v of @trackedConvoys
            if v > val
                val = v
        #val = 10
        for i in nears_t
            conv_val = @trackedConvoys[i]
            if conv_val
                if conv_val < val
                    val = conv_val
        ## multi ROUTE?? how TO?
        routes = []
        for key, value of @trackedConvoys
            if value <= val
                if not routes[value-1]
                    routes[value-1] = []
                #conv_lst.push(key)
                routes[value-1].push(key)
        ##for route in routes
        #country_troops = @app.GetCountryTroops(@app.play.country)
        country_troops = @app.game.phase().getCountryTroops()
        for i in [0..routes.length-1]
            route = routes[i]
            if route.length > 1
                #arm_dict = @app.map.troops[country]
                for i in route
                    #if i in (key for key of (tlist for ttype, tlist of arm_dict))
                    if i in country_troops
                        conv_lst.push(i)
                        break
            if conv_lst.length<i+1
                conv_lst.push(route[0])
        return conv_lst

    _getConvoysFromMove: (id_f, id_t) ->
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
        if not choosen
            choice = choices[0].data
        return choice

window.Interactions = Interactions
