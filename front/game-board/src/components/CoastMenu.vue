<template>
  <div class="menu-wrapper">
    <transition name="fade" mode="out-in">
      <div v-if="display" class="action-menu" ref="menu" :style="style">
        <button class="btn-ico">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="north">
            <path d="M12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M17,14L12,9L7,14H17Z"/>
          </svg>
        </button>
        <button class="btn-ico">
          <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="south">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M7,10L12,15L17,10H7Z"/>
          </svg>
        </button>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'CoastMenu',
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
    north() {
      this.$emit('action', 'north_coast')
    },
    south() {
      this.$emit('action', 'south_coast')
    }
  }
}
</script>

<style scoped>
.menu-wrapper {
  @apply absolute block top-0;
}
.action-menu {
  @apply absolute z-20 w-20 flex items-center justify-center bg-gray-800 text-gray-500 text-xs rounded px-2 py-2;
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
