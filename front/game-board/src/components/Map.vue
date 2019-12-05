<template>
  <div class="h-full relative">
    <transition name="fade" mode="out-in">
      <div v-if="loading" class="h-full w-full flex flex-wrap items-center justify-between bg-gray-900 loader">
        <div class="w-full flex flex-row flex-wrap items-center">
          <span class="w-full text-center text-2xl text-gray-500">Loading</span>
          <div class="w-full flex justify-center py-5">
            <atom-spinner color="gray-500"></atom-spinner>
          </div>
        </div>
      </div>
    </transition>
    <div
      :class="`w-full absolute inset-0 flex overflow-y-auto map-wrapper ${loading ? 'invisible' : ''}`"
      @click="mapClick"
      @mouseenter="mapMouseIn"
      @mousemove="mapMouseMovement"
      @mouseleave="mapMouseOut"
    >
      <img class="w-full" :src="currentSrc" :style="style" @load="imageLoaded" />
    </div>
    <territory-label
      :label="territoryLabel.name"
      :position="territoryLabel.position"
    ></territory-label>
  </div>
</template>

<script>
import AtomSpinner from './AtomSpinner'
import TerritoryLabel from './TerritoryLabel'

export default {
  name: 'Map',
  components: {
    AtomSpinner,
    TerritoryLabel
  },
  props: {
    src: String,
    loading: {
      type: Boolean,
      default: true
    },
    territoryLabel: Object
  },
  data() {
    return {
      currentSrc: null,
      srcLoaded: false,
      img: {
        width: 0,
        height: 0
      },
      canvas: {
        width: 0,
        height: 0
      },
      layer: {
        width: 0,
        height: 0
      },
      offsets: {
        x: 0,
        y: 0
      },
      zoom: 1,
      style: null,
      mouseTrack: {
        timeout: null,
        enabled: false
      }
    }
  },
  mounted() {
    this.currentSrc = this.src
  },
  methods: {
    imageLoaded(event) {
      if (this.srcLoaded) {
        return
      }
      let obj = event.path[0]
      this.img.width = obj.naturalWidth
      this.img.height = obj.naturalHeight
      this.canvas.width = obj.width
      this.canvas.height = obj.height
      this.zoom = this.canvas.width / this.img.width
      this.layer.width = this.canvas.width
      this.layer.height = Math.round(this.img.height * this.zoom)
      this.offsets.x = obj.x
      this.offsets.y = obj.y
      this.style = {height: `${this.layer.height}px`}
      this.srcLoaded = true
      this.$emit('imgLoaded')
    },
    updateFrame(value) {
      this.currentSrc = value
    },
    getEventPositions(event) {
      let sx = event.offsetX || event.layerX
      let sy = event.offsetY || event.layerY
      let rx = event.layerX || event.clientX
      let ry = event.layerY || event.clientY
      if (event.target.y === undefined) {
        let obj = event.path[0]
        sx -= this.offsets.x
        rx -= this.offsets.x
        sy -= this.offsets.y
        ry -= this.offsets.y
        sx += obj.parentNode.scrollLeft
        sy += obj.parentNode.scrollTop
      }
      let input = {x: sx, y: sy}
      let relative = {x: rx, y: ry}
      let position = {
        x: Math.round(input.x / this.zoom),
        y: Math.round(input.y / this.zoom)
      }
      return {input: input, relative: relative, position: position}
    },
    mapClick(event) {
      let data = this.getEventPositions(event)
      this.$emit('clicked', data.input, data.position)
    },
    mapMouseIn(event) {
      this.mouseTrack.enabled = true
    },
    mapMouseOut(event) {
      this.mouseTrack.enabled = false
      clearTimeout(this.mouseTrack.timeout)
      this.$emit('left')
    },
    mapMouseMovement(event) {
      if (!this.mouseTrack.enabled) {
        return
      }
      this.$emit('left')
      clearTimeout(this.mouseTrack.timeout)
      this.mouseTrack.timeout = setTimeout(() => {
        this.mapMouseMoved(event)
      }, 300)
    },
    mapMouseMoved(event) {
      let data = this.getEventPositions(event)
      this.$emit('holdOver', data.input, data.relative, data.position)
    }
  }
}
</script>

<style scoped>
.content {
  height: calc(100% - 3rem);
}
.fade-leave-active {
  transition: opacity .3s;
}
.fade-leave-to {
  opacity: 0;
}
.map-wrapper::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
  background-color: #2d3748;
}
.map-wrapper::-webkit-scrollbar {
  width: 6px;
  background-color: #2d3748;
}
.map-wrapper::-webkit-scrollbar-thumb {
  background-color: #718096;
}
</style>
