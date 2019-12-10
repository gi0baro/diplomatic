<template>
  <div class="h-screen">
    <header class="h-12 flex">
      <div class="flex-1 flex items-center justify-between px-6 bg-gray-800">
        <logo></logo>
        <div class="flex-1 flex items-center justify-end">
          <time-controls
            :active="timeControlsEnabled"
            :step="gameStep"
            :rewindEnabled="canTimeRewind"
            :forwardEnabled="canTimeForward"
            @begin="controlTime('begin')"
            @rewind="controlTime('rewind')"
            @forward="controlTime('forward')"
            @end="controlTime('end')"
          ></time-controls>
          <controls
            :isPlayer="hasPlayerControls"
            :isReady="isPlayerReady"
            :isSaving="isSaving"
            :pendingSave="needSave"
            :activeSection="activeSection"
            @section="controlSection"
            @ready="setPlayerReady"
            @save="saveOrders"
          ></controls>
        </div>
      </div>
      <header-side></header-side>
    </header>
    <div class="flex content">
      <div class="flex-1 relative">
        <variant-map
          :src="image_src_map"
          :loading="mapLoading"
          :territoryLabel="mapTerritoryLabel"
          @imgLoaded="mapImageLoaded"
          @clicked="mapClicked"
          @holdOver="mapHoldOver"
          @left="mapLeft"
          ref="map"
        ></variant-map>
        <territory-menu
          :screenw="screenWidth"
          :display="actionMenus.territory.display"
          :origin="actionMenus.territory.position"
          :canConvoy="actionMenus.territory.canConvoy"
          :order="actionMenus.territory.order"
          @action="controlTerritoryAction"
          @close="menuTerritoryClose(true)"
        ></territory-menu>
        <alert
          :message="alertData.message"
          :dismissable="alertData.dismissable"
          :dismissAfter="alertData.autoDismiss"
          @clear="alertClear"
        ></alert>
      </div>
      <div class="w-64 xl:w-1/5 bg-gray-800 border-l border-gray-700">
        <transition name="fade" mode="out-in">
          <orders v-if="activeSection == 'orders'"></orders>
          <chat-fragment v-if="activeSection == 'chat'"></chat-fragment>
          <stats
            v-if="activeSection == 'stats'"
            :player="player"
            :mapData="mapData"
            :gameData="gameData"
            :targetCenters="targetSupplyCenters"
            :step="gameStep"
            :loading="isLoadingStep"
          ></stats>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'
import axios from 'axios'

import Logo from './Logo'
import HeaderSide from './HeaderSide'
import Controls from './Controls'
import TimeControls from './TimeControls'
import VariantMap from './Map'
import Orders from './Orders'
import ChatFragment from './ChatFragment'
import Stats from './Stats'
import TerritoryMenu from './TerritoryMenu'
import Alert from './Alert'

import {
  ListMapper,
  buildGameStep,
  buildPreGameStep,
  buildNextGameStep
} from '../utils'

Vue.prototype.$http = axios.create({
  validateStatus (status) {
    return (status >= 200 && status < 300) || (status >= 400 && status < 500)
  }
})

export default {
  name: 'Board',
  components: {
    Logo,
    HeaderSide,
    Controls,
    TimeControls,
    VariantMap,
    Orders,
    ChatFragment,
    Stats,
    TerritoryMenu,
    Alert
  },
  props: {
    image_src_map: String,
    image_src_army: String,
    image_src_fleet: String,
    player: {
      type: String,
      default: null
    },
    game_active: {
      type: Boolean,
      default: false
    },
    game_pre: {
      type: Boolean,
      default: false
    },
    game_over: {
      type: Boolean,
      default: false
    },
    player_active: {
      type: Boolean,
      default: false
    },
    player_ready: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      game: null,
      mapData: null,
      gameData: null,
      gameStep: null,
      gameSteps: ListMapper(),
      framesLoaded: false,
      mapLoading: true,
      isLoadingStep: true,
      isPlayerReady: false,
      isSaving: false,
      isChangingReady: false,
      needSave: false,
      // playerOrders: null,
      activeSection: 'stats',
      screenWidth: 0,
      timeouts: {
        save: null,
      },
      mapTerritoryLabel: {
        name: null,
        position: null
      },
      actionMenus: {
        territory: {
          display: false,
          position: null,
          canConvoy: false,
          order: {type: 0}
        }
      },
      alertData: {
        message: null,
        dismissable: true,
        autoDismiss: null
      }
    }
  },
  computed: {
    hasPlayerControls() {
      return this.player != null
    },
    hasPlayerFullControls() {
      return this.game_active && this.hasPlayerControls && this.player_active
    },
    timeControlsEnabled() {
      return !this.game_pre && this.launchFeasible
    },
    launchFeasible() {
      return !!this.mapData && !!this.gameData && this.framesLoaded && this.gameStep !== null
    },
    lastGameStep() {
      let sub = this.hasPlayerFullControls ? -2 : -1
      return this.gameSteps.get(sub)
    },
    nextGameStep() {
      if (this.hasPlayerFullControls) {
        return this.gameSteps.get(-1)
      }
      return null
    },
    canTimeRewind() {
      if (this.gameStep === null) {
        return false
      }
      return this.gameStep.idx > 0
    },
    canTimeForward() {
      if (this.gameStep === null) {
        return false
      }
      return this.gameStep.idx < (this.gameSteps.len() - 1)
    },
    targetSupplyCenters() {
      return (!!this.mapData && !!this.gameData) ? (this.gameData.target_sc || this.mapData.scs_to_win) : 0
    },
    playerOrders() {
      let step = this.nextGameStep
      if (step !== null && step.orders !== null) {
        return step.orders[this.player]
      }
      return []
    },
    playerOrdersMap() {
      let rv = {}
      this.playerOrders.forEach((element) => {
        rv[element.territory] = element
      })
      return rv
    },
    canSave() {
      return !this.isLoadingStep && !this.isSaving
    }
  },
  watch: {
    gameStep(value) {
      this.game.ux.stepChange(value)
    },
    playerOrders: {
      deep: true,
      handler() {
        clearTimeout(this.timeouts.save)
        if (!this.canSave) {
          return
        }
        this.needSave = (this.playerOrders.filter((element) => {
          return element._changed === true
        }).length > 0)
        if (!this.needSave) {
          return
        }
        this.timeouts.save = setTimeout(() => {
          this.saveOrders()
        }, 3000)
      }
    }
  },
  mounted() {
    this.game = window.gapp
    this.isPlayerReady = !!this.player_ready
    this.getGameData()
  },
  methods: {
    getGameData() {
      axios.all([
        this.$http.get(this.game.net.routes.map),
        this.$http.get(this.game.net.routes.game),
        this.$http.get(this.game.net.routes.phase_next)
      ]).then(axios.spread((mapResponse, gameResponse, stepResponse) => {
        if ((mapResponse.status == 200) && (gameResponse.status == 200)) {
          this.mapData = mapResponse.data
          this.gameData = gameResponse.data
          this.gameSteps.append(buildPreGameStep(this.mapData, this.gameData))
          if (stepResponse.status == 200) {
            if (stepResponse.data.parent === null) {
              this.gameSteps.append(
                buildGameStep(this.mapData, this.gameData, stepResponse.data, {}, true)
              )
              this.afterGameData()
            } else {
              this.gameSteps.append(
                buildGameStep(this.mapData, this.gameData, stepResponse.data, null, true)
              )
              this.storeStepOrders(this.gameSteps.last()).then(() => {
                this.afterGameData()
              })
            }
          } else {
            this.afterGameData()
          }
        }
      })).catch(() => {})
    },
    async getPlayerOrders() {
      try {
        let {status, data} = await this.$http.get(
          this.game.net.routes.orders
        )
        if (status == 200 && !!data.data) {
          return data.data
        } else {
          return []
        }
      } catch (err) {
        throw err
      }
    },
    afterGameData() {
      if (this.hasPlayerFullControls) {
        this.gameSteps.append(buildNextGameStep(this.player, this.gameSteps.last()))
        let virtualStep = this.nextGameStep
        this.getPlayerOrders().then((orders) => {
          orders.forEach((element) => {
            virtualStep.orders[this.player].push({
              ...element,
              _changed: false
            })
          })
          this.dataLoaded()
        })
      } else {
        this.dataLoaded()
      }
    },
    dataLoaded() {
      this.gameStep = this.lastGameStep
      if (this.launchFeasible) {
        this.launch()
      }
    },
    async storeStepOrders(step, storeStep=true) {
      if (step.parent === null) {
        step.orders = {}
        return
      }
      let {idx} = step
      try {
        let {status, data} = await this.$http.get(
          this.game.net.routes.phase.replace(':ID:', step.parent)
        )
        if (status == 200) {
          step.orders = data.orders
          if (storeStep === true) {
            this.gameSteps.insert(idx, buildGameStep(this.mapData, this.gameData, data))
          }
        } else {
          throw 'bad step response'
        }
      } catch (err) {
        throw err
      }
    },
    async getStepBack() {
      // TODO: loading
      if (this.gameStep.parent === null) {
        // previous step is fake initial
        return this.gameStep.prev()
      }
      let prevStep = this.gameStep.prev()
      if (this.gameStep.parent !== null && prevStep.orders === null) {
        // we have previous step but is missing orders
        try {
          await this.storeStepOrders(prevStep)
        } catch (err) {
          throw err
        }
      }
      return prevStep
    },
    async getStepForward() {
      // TODO: loading
      let nextStep = this.gameStep.next()
      if (this.gameStep.id === null) {
        // current step is fake initial
        if (nextStep.parent === null) {
          // next step is the first real
          return nextStep
        }
        // fetch the first real step
        try {
          let {status, data} = await this.$http.get(
            this.game.net.routes.phase_prev
          )
          if (status == 200) {
            this.gameSteps.insert(1, buildGameStep(this.mapData, this.gameData, data, data.orders))
            nextStep = this.gameStep.next()
          } else {
            throw 'bad step response'
          }
        } catch (err) {
          throw err
        }
      } else if (nextStep.parent !== this.gameStep.id) {
        // we need the step(s) in the middle
        let {id, idx} = this.gameStep
        try {
          let {status, data} = await this.$http.get(
            this.game.net.routes.phase_next, {
              params: {last_id: id}
            }
          )
          if (status == 200) {
            this.gameSteps.insert(idx + 1, buildGameStep(this.mapData, this.gameData, data, data.orders))
            nextStep = this.gameStep.next()
          } else {
            throw 'bad step response'
          }
        } catch (err) {
          throw err
        }
      } else if (nextStep.orders === null) {
        // we have next step but is missing orders
        try {
          await this.storeStepOrders(nextStep, false)
        } catch (err) {
          throw err
        }
      }
      return nextStep
    },
    launch() {
      this.game.launch(
        this.mapData,
        this.gameData,
        this.player,
        this.game_active,
        this.game_pre,
        this.game_over,
        this.playerReady,
        this.playerOrders,
        () => {
          this.mapDisplay()
          this.isLoadingStep = false
        }
      )
    },
    controlSection(section) {
      this.activeSection = section
    },
    async controlTime(action) {
      if (action == 'begin') {
        this.gameStep = this.gameSteps.get(0)
      } else if (action == 'rewind') {
        this.gameStep = await this.getStepBack()
        // this.gameStep = this.gameSteps.get(this.gameStep.idx - 1)
      } else if (action == 'forward') {
        // this.gameStep = this.gameSteps.get(this.gameStep.idx + 1)
        this.gameStep = await this.getStepForward()
      } else if (action == 'end') {
        this.gameStep = this.lastGameStep
      }
    },
    controlTerritoryAction(action) {
      this.game.act.uxEvent(action)
      // this.actionMenus.territory.display = false
    },
    mapImageLoaded(canvasWidth) {
      this.screenWidth = canvasWidth
      this.game.init(
        this.image_src_map,
        this.image_src_army,
        this.image_src_fleet,
        (value) => {
          this.mapUpdate(value)
        },
        () => {
          this.framesLoaded = true
          if (this.launchFeasible) {
            this.launch()
          }
        }
      )
      this.game.bindings(
        (data) => {
          this.menuTerritoryShow(data.position, data.territory, !!data.canConvoy)
        },
        () => {
          this.menuTerritoryClose()
        },
        () => {
          this.switchStepToVirtual()
        },
        (message, dismissable=true, autoDismiss=null) => {
          this.alert(message, dismissable, autoDismiss)
        }
      )
    },
    mapClicked(mousePosition, relativePosition, mapPosition) {
      if (this.isPlayerReady) {
        this.alert("You can't add new orders since you set yourself as ready", true, 5)
        return
      }
      this.game.act.click(mousePosition, relativePosition, mapPosition)
    },
    mapHoldOver(mousePosition, relativePosition, mapPosition) {
      let name = this.game.utils.getTerritoryNameByPosition(mapPosition)
      this.mapTerritoryLabel.name = name
      this.mapTerritoryLabel.position = relativePosition
    },
    mapLeft() {
      this.mapTerritoryLabel.name = null
      this.mapTerritoryLabel.position = null
    },
    mapDisplay() {
      this.mapLoading = false
    },
    mapUpdate(value) {
      this.$refs.map.updateFrame(value)
    },
    menuTerritoryShow(position, territory, canConvoy) {
      let order = this.playerOrdersMap[territory]
      this.actionMenus.territory.position = position
      this.actionMenus.territory.canConvoy = canConvoy
      this.actionMenus.territory.order = order
      this.actionMenus.territory.display = true
    },
    menuTerritoryClose(action=false) {
      this.actionMenus.territory.display = false
      this.actionMenus.territory.position = null
      this.actionMenus.territory.canConvoy = false
      this.actionMenus.territory.order = {type: 0}
      if (action === true) {
        this.game.act.uxEvent('close')
      }
    },
    alert(message, dismissable, autoDismiss) {
      this.alertData.message = message
      this.alertData.dismissable = dismissable
      this.alertData.autoDismiss = autoDismiss
    },
    alertClear() {
      this.alertData.message = null
      this.alertData.dismissable = true
      this.alertData.autoDismiss = null
    },
    switchStepToVirtual() {
      this.gameStep = this.nextGameStep
    },
    saveOrders() {
      if (!this.needSave) {
        return
      }
      this.isSaving = true
      this.needSave = false
      let reqs = []
      this.playerOrders.filter((element) => {
        return element._changed === true
      }).forEach((element) => {
        reqs.push(
          this.$http.put(
            this.game.net.routes.order_save.replace(':ID:', element.id),
            {type: element.type, data: element.data}
          )
        )
      })
      axios.all(reqs).then(axios.spread((...args) => {
        args.forEach((arg) => {
          let {status, data} = arg
          if (status == 200) {
            let order = this.playerOrdersMap[data.territory]
            order._changed = false
          }
        })
        this.isSaving = false
      })).catch(() => {})
    },
    async setPlayerReady(value) {
      if (this.isChangingReady) {
        return
      }
      this.isChangingReady = true
      try {
        let {status, data} = await this.$http.put(
          this.game.net.routes.ready,
          {ready: value}
        )
        if (status == 200) {
          this.isPlayerReady = data.data
        }
        this.isChangingReady = false
      } catch (err) {
        throw err
      }
    }
  }
}
</script>

<style scoped>
.content {
  height: calc(100% - 3rem);
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
