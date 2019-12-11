<template>
  <div class="territory-label-wrapper">
    <transition name="fade" mode="out-in">
      <div
        v-if="display"
        class="territory-label"
        ref="label"
        :style="style"
      >
        {{ label }}
      </div>
    </transition>
    <div class="territory-label-dim" ref="labelDim">
      {{ label }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'TerritoryLabel',
  props: {
    label: String,
    position: Object
  },
  data() {
    return {
      style: null
    }
  },
  computed: {
    display() {
      return (!!this.style && !!this.label)
    }
  },
  watch: {
    position(value) {
      if (value === null) {
        this.style = null
        return
      }
      this.$nextTick(() => {
        let element = this.$refs.labelDim
        let mx = element.clientWidth / 2
        let my = element.clientHeight * 1.2
        this.style = {top: `${value.y - my}px`, left: `${value.x - mx}px`}
      })
    }
  }
}
</script>

<style scoped>
.territory-label-wrapper {
  @apply absolute block top-0;
}
.territory-label {
  @apply absolute z-10 bg-gray-800 text-gray-100 text-xs whitespace-no-wrap rounded px-4 py-1;
  opacity: 0.8;
}
.territory-label-dim {
  @apply absolute block text-xs px-4 py-1 whitespace-no-wrap invisible;
  z-index: -10;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
