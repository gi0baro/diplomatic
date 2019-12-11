<template>
  <div class="menu-wrapper">
    <transition name="fade" mode="out-in">
      <div v-if="display" class="action-menu" ref="menu" :style="style">
        <button :class="`btn-ico ${disbandCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="disband">
            <path d="M4.15,21.46L5.47,19.58C3.35,17.74 2,15.03 2,12A10,10 0 0,1 12,2C13.78,2 15.44,2.46 16.89,3.27L18.21,1.39L19.85,2.54L18.53,4.42C20.65,6.26 22,8.97 22,12A10,10 0 0,1 12,22C10.22,22 8.56,21.54 7.11,20.73L5.79,22.61L4.15,21.46M12,4A8,8 0 0,0 4,12C4,14.35 5,16.46 6.63,17.93L15.73,4.92C14.62,4.33 13.35,4 12,4M12,20A8,8 0 0,0 20,12C20,9.65 19,7.54 17.37,6.07L8.27,19.08C9.38,19.67 10.65,20 12,20Z"/>
          </svg>
        </button>
        <button :class="`btn-ico ${retreatCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="retreat">
            <path d="M5,13L9,17L7.6,18.42L1.18,12L7.6,5.58L9,7L5,11H21V13H5M21,6V8H11V6H21M21,16V18H11V16H21Z"/>
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
  name: 'RetreatMenu',
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
      return {
        5: 'retreat',
        7: 'disband'
      }[this.order.type]
    },
    isRetreat() {
      return this.action == 'retreat'
    },
    isDisband() {
      return this.action == 'disband'
    },
    retreatCssColorCls() {
      return this.isRetreat ? 'text-gray-200' : 'text-gray-500'
    },
    disbandCssColorCls() {
      return this.isDisband ? 'text-gray-200' : 'text-gray-500'
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
    retreat() {
      this.$emit('action', 'retreat')
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
