<template>
  <transition name="fade" mode="out-in">
    <div v-if="display" class="absolute flex flex-row flex-wrap w-full items-center justify-center pb-4 bottom-0">
      <div class="max-w-sm flex flex-row flex-wrap bg-gray-800 rounded-sm px-5 py-4">
        <span class="w-full text-gray-200 text-base text-center py-2">{{ content }}</span>
        <div v-if="dismissable" class="flex flex-1 items-center justify-end">
          <button class="text-yellow-500 focus:outline-none" @click="dismiss">DISMISS</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'Alert',
  props: {
    message: String,
    dismissable: {
      type: Boolean,
      default: true
    },
    dismiss_after: Number
  },
  data() {
    return {
      content: null,
      timeout: null
    }
  },
  mounted() {
    this.content = this.message === undefined ? this.content : this.message
    if (this.dismiss_after) {
      this.scheduleDismiss()
    }
  },
  computed: {
    display() {
      return this.content !== null
    }
  },
  watch: {
    message(value) {
      if (value) {
        this.content = value
        return
      }
      this.dismiss()
    },
    dismiss_after(value) {
      if (value === null) {
        clearTimeout(this.timeout)
        return
      }
      this.scheduleDismiss()
    }
  },
  methods: {
    scheduleDismiss() {
      this.timeout = setTimeout(() => {
        this.dismiss()
      }, this.dismiss_after * 1000)
    },
    dismiss() {
      this.content = null
      clearTimeout(this.timeout)
    }
  }
}
</script>

<style scoped>
.territory-label-wrapper {
  @apply absolute block;
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
