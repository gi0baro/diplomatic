<template>
  <div class="menu-wrapper">
    <transition name="fade" mode="out-in">
      <div v-if="display" class="action-menu" ref="menu" :style="style">
        <button v-if="canBuild" :class="`btn-ico ${buildArmyCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="army">
            <path d="M20,12H4V11H6L7,6H12L13,11H20V12M13.22,7L13.62,9H22V7H13.22M22,16A3,3 0 0,1 19,19H5A3,3 0 0,1 2,16A3,3 0 0,1 5,13H19A3,3 0 0,1 22,16M6,16A1,1 0 0,0 5,15A1,1 0 0,0 4,16A1,1 0 0,0 5,17A1,1 0 0,0 6,16M13,16A1,1 0 0,0 12,15A1,1 0 0,0 11,16A1,1 0 0,0 12,17A1,1 0 0,0 13,16M20,16A1,1 0 0,0 19,15A1,1 0 0,0 18,16A1,1 0 0,0 19,17A1,1 0 0,0 20,16Z"/>
          </svg>
        </button>
        <button v-if="canBuild && canBuildFleet" :class="`btn-ico ${buildFleetCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="fleet">
            <path d="M6,6H18V9.96L12,8L6,9.96M3.94,19H4C5.6,19 7,18.12 8,17C9,18.12 10.4,19 12,19C13.6,19 15,18.12 16,17C17,18.12 18.4,19 20,19H20.05L21.95,12.31C22.03,12.06 22,11.78 21.89,11.54C21.76,11.3 21.55,11.12 21.29,11.04L20,10.62V6C20,4.89 19.1,4 18,4H15V1H9V4H6A2,2 0 0,0 4,6V10.62L2.71,11.04C2.45,11.12 2.24,11.3 2.11,11.54C2,11.78 1.97,12.06 2.05,12.31M20,21C18.61,21 17.22,20.53 16,19.67C13.56,21.38 10.44,21.38 8,19.67C6.78,20.53 5.39,21 4,21H2V23H4C5.37,23 6.74,22.65 8,22C10.5,23.3 13.5,23.3 16,22C17.26,22.65 18.62,23 20,23H22V21H20Z"/>
          </svg>
        </button>
        <button v-if="canDisband" :class="`btn-ico ${disbandCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="disband">
            <path d="M4.15,21.46L5.47,19.58C3.35,17.74 2,15.03 2,12A10,10 0 0,1 12,2C13.78,2 15.44,2.46 16.89,3.27L18.21,1.39L19.85,2.54L18.53,4.42C20.65,6.26 22,8.97 22,12A10,10 0 0,1 12,22C10.22,22 8.56,21.54 7.11,20.73L5.79,22.61L4.15,21.46M12,4A8,8 0 0,0 4,12C4,14.35 5,16.46 6.63,17.93L15.73,4.92C14.62,4.33 13.35,4 12,4M12,20A8,8 0 0,0 20,12C20,9.65 19,7.54 17.37,6.07L8.27,19.08C9.38,19.67 10.65,20 12,20Z"/>
          </svg>
        </button>
        <button class="btn-ico">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="close">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
          </svg>
        </button>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'BuildMenu',
  props: {
    display: {
      type: Boolean,
      default: true
    },
    screenw: {
      type: Number,
      default: 0
    },
    origin: {
      type: Object,
      default: null
    },
    canBuild: {
      type: Boolean,
      default: true
    },
    canBuildFleet: {
      type: Boolean,
      default: false
    },
    canDisband: {
      type: Boolean,
      default: false
    },
    order: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      position: {x: 0, y: 0}
    }
  },
  computed: {
    style() {
      return {top: `${this.position.y}px`, left: `${this.position.x}px`}
    },
    action() {
      if (this.order === null) {
        return null
      }
      if (this.order.type === 7) {
        return 'disband'
      }
      if (this.order.type === 6 && this.order.data.troop !== undefined) {
        if (this.order.data.troop === 0) {
          return 'build_army'
        }
        if (this.order.data.troop === 1) {
          return 'build_fleet'
        }
      }
      return null
    },
    isDisband() {
      return this.action == 'disband'
    },
    isBuildArmy() {
      return this.action == 'build_army'
    },
    isBuildFleet() {
      return this.action == 'build_fleet'
    },
    disbandCssColorCls() {
      return this.isDisband ? 'text-gray-200' : 'text-gray-500'
    },
    buildArmyCssColorCls() {
      return this.isBuildArmy ? 'text-gray-200' : 'text-gray-500'
    },
    buildFleetCssColorCls() {
      return this.isBuildFleet ? 'text-gray-200' : 'text-gray-500'
    }
  },
  watch: {
    origin(value) {
      if (value === null) {
        return
      }
      this.$nextTick(() => {
        let element = this.$refs.menu
        let multiplier = (value.x > (this.screenw / 2)) ? 1 : 0
        let mx = Math.round((element.clientWidth * multiplier) + (element.clientWidth * 0.1 * (multiplier || -1)))
        let my = Math.round(element.clientHeight)
        this.position.x = value.x - mx
        this.position.y = value.y - my
      })
    }
  },
  methods: {
    army() {
      this.$emit('action', 'build_army')
    },
    fleet() {
      this.$emit('action', 'build_fleet')
    },
    disband() {
      this.$emit('action', 'disband')
    },
    close() {
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.menu-wrapper {
  @apply absolute block top-0;
}
.action-menu {
  @apply absolute z-20 w-32 flex items-center justify-center bg-gray-800 text-gray-500 text-xs rounded px-2 py-2;
}
.btn-ico {
  @apply mx-2;
}
.btn-ico:hover {
  @apply text-gray-200;
}
.btn-ico:focus {
  outline: none;
}
.btn-ico-svg {
  @apply h-6 w-6 fill-current;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
