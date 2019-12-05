<template>
  <div id="app">
    <Board
      image_src_map="http://localhost:8000/download/maps.image.b1eb206f03a87d22.6d61702e706e67.png"
      image_src_army="http://localhost:8000/static/images/tank.png"
      image_src_fleet="http://localhost:8000/static/images/ship.png"
      player="Russia"
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
      init(map_src, army_src, fleet_src, map_update_callback, screen_init_callback, alert_method) {
        screen_init_callback()
      },
      launch(mapData, gameData, player, isGameActive, isPregame, isGameOver, callback) {
        callback()
      },
      net: {
        routes: {
          map: 'http://localhost:8000/api/map/1',
          game: 'http://localhost:8000/api/game/1'
        }
      },
      act: {
        click(mousePosition, mapPosition) {

        }
      },
      utils: {
        getTerritoryNameByPosition(mapPosition) {
          return 'Debug East'
        }
      }
    }
  }
}
</script>
