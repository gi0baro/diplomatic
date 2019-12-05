<template>
  <div class="h-screen">
    <header class="h-12 flex">
      <div class="flex-1 flex items-center justify-between px-6 bg-gray-800">
        <logo></logo>
        <div class="flex-1 flex items-center justify-end">
          <time-controls
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
          :dismiss_after="alertData.autoDismiss"
        ></alert>
      </div>
      <div class="w-64 xl:w-1/5 bg-gray-800 border-l border-gray-700">
        <transition name="fade" mode="out-in">
          <orders v-if="activeSection == 'orders'"></orders>
          <chat-fragment v-if="activeSection == 'chat'"></chat-fragment>
          <stats v-if="activeSection == 'stats'"></stats>
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
    player: String,
    game_active: Boolean,
    game_pre: Boolean,
    game_over: Boolean,
    player_active: Boolean,
    player_ready: Boolean
  },
  data() {
    return {
      game: null,
      mapData: null,
      gameData: null,
      framesLoaded: false,
      mapLoading: true,
      isPlayerReady: false,
      isSaving: false,
      needSave: false,
      activeSection: 'chat',
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
    launchFeasible() {
      return (!!this.mapData && !!this.gameData && this.framesLoaded)
    }
  },
  mounted() {
    this.isPlayerReady = !!this.player_ready
    this.game = window.gapp
    this.getData()
  },
  methods: {
    getData() {
      axios.all([
        this.$http.get(this.game.net.routes.map),
        this.$http.get(this.game.net.routes.game)
      ]).then(axios.spread((mapResponse, gameResponse) => {
        if ((mapResponse.status == 200) && (gameResponse.status == 200)) {
          this.mapData = mapResponse.data
          this.gameData = gameResponse.data
          if (this.launchFeasible) {
            this.launch()
          }
        }
      })).catch(() => {})
    },
    launch() {
      this.game.launch(
        this.mapData,
        this.gameData,
        this.player,
        this.game_active,
        this.game_pre,
        this.game_over,
        () => {
          this.mapDisplay()
        }
      )
    },
    controlSection(section) {
      this.activeSection = section
    },
    controlTime(action) {
      console.log(action)
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
