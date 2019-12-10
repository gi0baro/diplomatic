<template>
  <transition name="fade" mode="out-in">
    <div v-if="display" class="absolute flex flex-row flex-wrap w-full items-center justify-center pb-4 bottom-0">
      <div class="max-w-sm flex flex-row flex-wrap bg-gray-800 rounded-sm px-5 py-4 alert-solid">
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
    dismissAfter: Number
  },
  data() {
    return {
      content: null,
      timeout: null
    }
  },
  mounted() {
    this.content = (this.message === undefined) ? this.content : this.message
    if (!!this.dismissAfter) {
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
      if (!value) {
        if (!!this.content) {
          this.dismiss()
        }
        clearTimeout(this.timeout)
        return
      }
      this.content = value
      this.scheduleDismiss()
    },
    dismissAfter(value) {
      this.scheduleDismiss()
    }
  },
  methods: {
    scheduleDismiss() {
      clearTimeout(this.timeout)
      if (!this.dismissAfter) {
        return
      }
      this.timeout = setTimeout(() => {
        this.dismiss()
      }, this.dismissAfter * 1000)
    },
    dismiss() {
      this.content = null
      this.$emit('clear')
    }
  }
}
</script>

<style scoped>
.alert-solid {
  opacity: 0.95;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
