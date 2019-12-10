<template>
  <div id="app">
    <Board
      image_src_map="http://localhost:8000/download/maps.image.b1eb206f03a87d22.6d61702e706e67.png"
      image_src_army="http://localhost:8000/static/images/tank.png"
      image_src_fleet="http://localhost:8000/static/images/ship.png"
      player="Austria"
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
      init(map_src, army_src, fleet_src, map_update_callback, screen_init_callback, menu_territory_method, alert_method) {
        this.act.menuTerritoryMethod = menu_territory_method
        screen_init_callback()
      },
      launch(mapData, gameData, player, isGameActive, isPregame, isGameOver, isPlayerReady, callback) {
        callback()
      },
      net: {
        routes: {
          map: 'http://localhost:8000/api/map/1',
          game: 'http://localhost:8000/api/game/3',
          phase: 'http://localhost:8000/api/phases/:ID:',
          phase_next: 'http://localhost:8000/api/game/3/phases/next',
          phase_prev: 'http://localhost:8000/api/game/3/phases/prev'
        }
      },
      act: {
        click(mousePosition, relativePosition, mapPosition) {
          console.log(relativePosition)
          this.menuTerritoryMethod(relativePosition, false)
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
