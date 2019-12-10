<template>
  <div class="menu-wrapper">
    <transition name="fade" mode="out-in">
      <div v-if="display" class="action-menu" ref="menu" :style="style">
        <button :class="`btn-ico ${holdCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="hold">
            <path d="M21,11C21,16.55 17.16,21.74 12,23C6.84,21.74 3,16.55 3,11V5L12,1L21,5V11M12,21C15.75,20 19,15.54 19,11.22V6.3L12,3.18L5,6.3V11.22C5,15.54 8.25,20 12,21Z"/>
          </svg>
        </button>
        <button :class="`btn-ico ${moveCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="move">
            <path d="M11,2V4.07C7.38,4.53 4.53,7.38 4.07,11H2V13H4.07C4.53,16.62 7.38,19.47 11,19.93V22H13V19.93C16.62,19.47 19.47,16.62 19.93,13H22V11H19.93C19.47,7.38 16.62,4.53 13,4.07V2M11,6.08V8H13V6.09C15.5,6.5 17.5,8.5 17.92,11H16V13H17.91C17.5,15.5 15.5,17.5 13,17.92V16H11V17.91C8.5,17.5 6.5,15.5 6.08,13H8V11H6.09C6.5,8.5 8.5,6.5 11,6.08M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11Z"/>
          </svg>
        </button>
        <button :class="`btn-ico ${supportHoldCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="supportHold">
            <path d="M21 11C21 16.55 17.16 21.74 12 23C6.84 21.74 3 16.55 3 11V5L12 1L21 5V11M12 21C15.75 20 19 15.54 19 11.22V6.3L12 3.18L5 6.3V11.22C5 15.54 8.25 20 12 21M15.05 16L11.97 14.15L8.9 16L9.71 12.5L7 10.16L10.58 9.85L11.97 6.55L13.37 9.84L16.95 10.15L14.23 12.5L15.05 16"/>
          </svg>
        </button>
        <button :class="`btn-ico ${supportMoveCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="supportMove">
            <path d="M12,2L16,6H13V13.82L22.39,19.25L21.39,21L12,15.56L2.61,21L1.61,19.25L11,13.82V6H8L12,2Z"/>
          </svg>
        </button>
        <button v-if="canConvoy" :class="`btn-ico ${convoyCssColorCls}`">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="convoy">
            <path d="M2.2,9.76H4.44V11.94H2.2V9.76H2.2M4.95,9.76H7.2V11.94H4.95V9.76H4.95M4.95,6.96H7.2V9.14H4.95V6.96M7.71,9.76H9.95V11.94H7.71V9.76H7.71M7.71,6.96H9.95V9.14H7.71V6.96M10.46,9.76H12.71V11.94H10.46V9.76H10.46M10.46,6.96H12.71V9.14H10.46V6.96M13.22,9.76H15.46V11.94H13.22V9.76H13.22M10.46,4.16H12.71V6.34H10.46V4.16M5.33,15.09C5.68,15.09 5.96,15.36 5.96,15.7C5.96,16.03 5.68,16.31 5.33,16.31C5,16.31 4.71,16.03 4.71,15.7C4.71,15.36 5,15.09 5.33,15.09M22.69,10.89V10.89L23,11.06L22.84,11.37C22.2,12.58 20.87,12.95 19.57,12.89C17.62,17.6 13.37,19.84 8.23,19.84C5.57,19.84 3.13,18.87 1.74,16.58L1.72,16.54L1.5,16.14C1.05,15.13 0.89,14.03 1,12.92L1.03,12.59H15.8C16.33,12.59 16.87,12.5 17.36,12.34L18.12,12C17.81,11.6 17.64,11.09 17.6,10.59C17.53,9.91 17.67,9 18.15,8.5L18.39,8.22L18.67,8.44C19.38,9 19.97,9.77 20.08,10.65C20.93,10.41 21.94,10.46 22.69,10.89M5.34,16.85V16.85C6,16.85 6.5,16.33 6.5,15.7C6.5,15.06 6,14.54 5.33,14.54C4.68,14.54 4.15,15.06 4.15,15.7C4.15,16.34 4.68,16.85 5.34,16.85Z"/>
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
  name: 'TerritoryMenu',
  props: {
    display: {
      type: Boolean,
      default: false
    },
    screenw: {
      type: Number,
      default: 0
    },
    origin: {
      type: Object,
      default: null
      // default: () => ({x: 0, y: 0})
    },
    canConvoy: {
      type: Boolean,
      default: false
    },
    action: {
      type: String,
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
    isHold() {
      return this.action == 'hold'
    },
    isMove() {
      return this.action == 'move'
    },
    isSupportHold() {
      return this.action == 'support_hold'
    },
    isSupportMove() {
      return this.action == 'support_move'
    },
    isConvoy() {
      return this.action == 'convoy'
    },
    holdCssColorCls() {
      return this.isHold ? 'text-gray-200' : 'text-gray-500'
    },
    moveCssColorCls() {
      return this.isMove ? 'text-gray-200' : 'text-gray-500'
    },
    supportHoldCssColorCls() {
      return this.isSupportHold ? 'text-gray-200' : 'text-gray-500'
    },
    supportMoveCssColorCls() {
      return this.isSupportMove ? 'text-gray-200' : 'text-gray-500'
    },
    convoyCssColorCls() {
      return this.isConvoy ? 'text-gray-200' : 'text-gray-500'
    }
  },
  watch: {
    origin(value) {
      console.log('origin', value)
      if (value === null) {
        return
      }
      this.$nextTick(() => {
        let element = this.$refs.menu
        let multiplier = (value.x > (this.screenw / 2)) ? 1 : 0
        let mx = element.clientWidth * multiplier
        let my = Math.round(element.clientHeight / 2)
        console.log(value.x, value.y, multiplier, mx, my)
        this.position.x = value.x - mx
        this.position.y = value.y - my
      })
    }
  },
  methods: {
    hold() {
      this.$emit('action', 'hold')
    },
    move() {
      this.$emit('action', 'move')
    },
    supportHold() {
      this.$emit('action', 'support_hold')
    },
    supportMove() {
      this.$emit('action', 'support_move')
    },
    convoy() {
      this.$emit('action', 'convoy')
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
  @apply absolute z-20 w-64 flex items-center justify-center bg-gray-800 text-gray-500 text-xs rounded px-2 py-2;
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
