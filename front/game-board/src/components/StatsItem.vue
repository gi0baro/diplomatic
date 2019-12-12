<template>
  <div
    class="w-full mx-auto flex flex-row flex-wrap bg-gray-700 stats-element border-t first:border-t-0 border-gray-600"
  >
    <div :class="`w-full flex items-center px-4 py-4 ml-1 ${country.self ? 'country-self' : ''}`">
      <div class="w-full flex flex-1">
        <div class="block h-12 w-12 rounded-full bg-gray-200">
        </div>
        <div class="ml-3 flex-1 flex-row flex-wrap items-center justify-start text-left">
          <p class="text-lg leading-tight text-gray-100">{{ country.label }}</p>
          <p class="text-sm text-gray-400">:player name:</p>
          <div class="w-full px-1 pr-3 pt-2">
            <div class="w-full bg-gray-800">
              <div class="h-1" :style="style"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="h-full">
        <div class="w-full flex items-center justify-around text-gray-400">
          <svg class="h-5 w-5 fill-current" viewBox="0 0 24 24">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
          </svg>
          <p class="ml-2 text-sm text-gray-400">{{ country.supply_centers }}</p>
        </div>
        <div class="w-full flex items-center justify-around text-gray-400">
          <svg class="h-5 w-5 fill-current" viewBox="0 0 24 24">
            <path d="M20,12H4V11H6L7,6H12L13,11H20V12M13.22,7L13.62,9H22V7H13.22M22,16A3,3 0 0,1 19,19H5A3,3 0 0,1 2,16A3,3 0 0,1 5,13H19A3,3 0 0,1 22,16M6,16A1,1 0 0,0 5,15A1,1 0 0,0 4,16A1,1 0 0,0 5,17A1,1 0 0,0 6,16M13,16A1,1 0 0,0 12,15A1,1 0 0,0 11,16A1,1 0 0,0 12,17A1,1 0 0,0 13,16M20,16A1,1 0 0,0 19,15A1,1 0 0,0 18,16A1,1 0 0,0 19,17A1,1 0 0,0 20,16Z"/>
          </svg>
          <p class="ml-2 text-sm text-gray-400">{{ country.troops.armies }}</p>
        </div>
        <div class="w-full flex items-center justify-around text-gray-400">
          <svg class="h-5 w-5 fill-current" viewBox="0 0 24 24">
            <path d="M6,6H18V9.96L12,8L6,9.96M3.94,19H4C5.6,19 7,18.12 8,17C9,18.12 10.4,19 12,19C13.6,19 15,18.12 16,17C17,18.12 18.4,19 20,19H20.05L21.95,12.31C22.03,12.06 22,11.78 21.89,11.54C21.76,11.3 21.55,11.12 21.29,11.04L20,10.62V6C20,4.89 19.1,4 18,4H15V1H9V4H6A2,2 0 0,0 4,6V10.62L2.71,11.04C2.45,11.12 2.24,11.3 2.11,11.54C2,11.78 1.97,12.06 2.05,12.31M20,21C18.61,21 17.22,20.53 16,19.67C13.56,21.38 10.44,21.38 8,19.67C6.78,20.53 5.39,21 4,21H2V23H4C5.37,23 6.74,22.65 8,22C10.5,23.3 13.5,23.3 16,22C17.26,22.65 18.62,23 20,23H22V21H20Z"/>
          </svg>
          <p class="ml-2 text-sm text-gray-400">{{ country.troops.fleets }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {rgbToHex} from '../utils'

export default {
  name: 'StatsItem',
  props: {
    country: {
      type: Object,
      default: null
    },
    targetCenters: {
      type: Number,
      default: 0
    }
  },
  computed: {
    centersPercentage() {
      return Math.round(this.country.supply_centers / this.targetCenters * 100)
    },
    hexColor() {
      return rgbToHex(this.country.color.r, this.country.color.g, this.country.color.b)
    },
    style() {
      return {
        width: `${this.centersPercentage}%`,
        "background-color": this.hexColor
      }
    }
  }
}
</script>

<style scoped>
.country-self {
  @apply ml-0 border-l-1r;
}
</style>
