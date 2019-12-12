<template>
  <div id="app">
    <Board
      image_src_map="http://localhost:8000/download/maps.image.b1eb206f03a87d22.6d61702e706e67.png"
      image_src_army="http://localhost:8000/static/images/tank.png"
      image_src_fleet="http://localhost:8000/static/images/ship.png"
      player="France"
      :player_id="7"
      :user_id="1"
      user_name="gi0baro"
      :game_active="true"
      :game_pre="false"
      player_active
    ></Board>
  </div>
</template>

<script>
import '@/assets/css/tailwind.css'

import Board from './components/Board.vue'

export default {
  name: 'app',
  components: {
    Board
  },
  created() {
    window.gapp = window.gapp || {
      init(map_src, army_src, fleet_src, map_update_callback, screen_init_callback) {
        screen_init_callback()
      },
      bindings(menu_territory_open, menu_territory_close, menu_build_open, menu_build_close, menu_retreat_open, menu_retreat_close, menu_coast_open, menu_coast_close, step_next_method, alert_method) {
        this.act.menuTerritoryOpen = menu_territory_open
        this.act.menuTerritoryClose = menu_territory_close
      },
      launch(mapData, gameData, player, isGameActive, isPregame, isGameOver, isPlayerReady, orders, callback) {
        callback()
      },
      net: {
        routes: {
          map: 'http://localhost:8000/api/map/1',
          game: 'http://localhost:8000/api/game/4',
          phase: 'http://localhost:8000/api/phases/:ID:',
          phase_next: 'http://localhost:8000/api/game/4/phases/next',
          phase_prev: 'http://localhost:8000/api/game/4/phases/prev',
          orders: 'http://localhost:8000/api/game/4/orders',
          order_save: 'http://localhost:8000/api/orders/:ID:',
          chat_rooms: 'http://localhost:8000/api/game/4/rooms'
        }
      },
      act: {
        click(mousePosition, relativePosition, mapPosition) {
          console.log(relativePosition)
          this.menuTerritoryOpen({position: relativePosition, canConvoy: false})
        },
        uxEvent(action) {
          console.log(action)
        }
      },
      utils: {
        getTerritoryNameByPosition(mapPosition) {
          return 'Debug East'
        }
      },
      ux: {
        stepChange(val) {}
      }
    }
  }
}
</script>
