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
        <alert
          :message="alertData.message"
          :dismissable="alertData.dismissable"
          :dismissAfter="alertData.autoDismiss"
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
      needSave: false,
      activeSection: 'stats',
      mapTerritoryLabel: {
        name: null,
        position: null
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
    }
  },
  watch: {
    gameStep(value) {
      this.game.ux.stepChange(value)
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
    afterGameData() {
      if (this.hasPlayerFullControls) {
        this.gameSteps.append(buildNextGameStep(this.player, this.gameSteps.last()))
        // TODO: player orders
      }
      this.gameStep = this.lastGameStep
      if (this.launchFeasible) {
        this.launch()
      }
    },
    async storeStepOrders(step, storeStep=true) {
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
        () => {
          console.log('launch callback')
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
    mapImageLoaded() {
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
        },
        (message, dismissable=true, autoDismiss=null) => {
          this.alert(message, dismissable, autoDismiss)
        }
      )
    },
    mapClicked(mousePosition, mapPosition) {
      this.game.act.click(mousePosition, mapPosition)
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
    alert(message, dismissable, autoDismiss) {
      this.alertData.message = message
      this.alertData.dismissable = dismissable
      this.alertData.autoDismiss = autoDismiss
    },
    saveOrders() {
      this.isSaving = true
      this.needSave = false
    },
    setPlayerReady(value) {
      this.isPlayerReady = value
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
