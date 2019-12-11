<template>
  <div v-if="!loading" class="h-full flex flex-col">
    <div class="flex px-4 py-1 items-center border-b border-gray-600">
      <span class="w-full text-lg text-white">Stats</span>
    </div>
    <div class="flex flex-row flex-wrap overflow-y-auto stats-list">
      <stats-item
        v-for="country in countries"
        :key="country.label"
        :country="country"
        :targetCenters="targetCenters"
      ></stats-item>
    </div>
  </div>
  <div v-else class="h-full flex items-center justify-center">
    <dot-spinner></dot-spinner>
  </div>
</template>

<script>
import DotSpinner from './DotSpinner'
import StatsItem from './StatsItem'

export default {
  name: 'Stats',
  components: {
    DotSpinner,
    StatsItem
  },
  props: {
    player: {
      type: String,
      default: null
    },
    mapData: {
      type: Object,
      default: null
    },
    gameData: {
      type: Object,
      default: null
    },
    targetCenters: {
      type: Number,
      default: 0
    },
    step: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    countries() {
      if (this.step === null) {
        return []
      }
      let rv = this.gameData.players.map((country) => {
        return {
          label: country,
          color: this.mapData.countries[country],
          supply_centers: this.step.supply_centers[country] || 0,
          troops: this.step.troops[country] || {armies: 0, fleets: 0},
          self: (country === this.player)
        }
      })
      return rv.sort((a, b) => {
        return (a.supply_centers > b.supply_centers) ? -1 : 1
      })
    }
  }
}
</script>

<style scoped>
.country-self {
  @apply ml-0 border-l-1r;
}
</style>
