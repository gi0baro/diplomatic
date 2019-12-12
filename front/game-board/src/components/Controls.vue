<template>
  <div>
    <button v-if="isPlayer" :class="`btn-ico ${readyCssColorCls}`">
      <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="ready">
        <path d="M19,19H5V5H15V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V11H19M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"/>
      </svg>
    </button>
    <button v-if="isPlayer" :class="`btn-ico ${saveCssColorCls}`">
      <svg class="btn-ico-svg" viewBox="0 0 24 24" @click="save">
        <path v-if="!isSaving" d="M17 3H5C3.89 3 3 3.9 3 5V19C3 20.1 3.89 21 5 21H19C20.1 21 21 20.1 21 19V7L17 3M19 19H5V5H16.17L19 7.83V19M12 12C10.34 12 9 13.34 9 15S10.34 18 12 18 15 16.66 15 15 13.66 12 12 12M6 6H15V10H6V6Z"/>
        <path v-else d="M4 19H10V21H4C2.89 21 2 20.1 2 19V5C2 3.9 2.89 3 4 3H16L20 7V9.12L18 11.12V7.83L15.17 5H4V19M14 10V6H5V10H14M20.42 12.3C20.31 12.19 20.18 12.13 20.04 12.13C19.9 12.13 19.76 12.19 19.65 12.3L18.65 13.3L20.7 15.35L21.7 14.35C21.92 14.14 21.92 13.79 21.7 13.58L20.42 12.3M12 19.94V22H14.06L20.12 15.93L18.07 13.88L12 19.94M14 15C14 13.34 12.66 12 11 12S8 13.34 8 15 9.34 18 11 18C11.04 18 11.08 18 11.13 18L14 15.13C14 15.09 14 15.05 14 15"/>
      </svg>
    </button>
    <button :class="`btn-ico ${ordersCssColorCls}`" @click="section('orders')">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M5,3C3.89,3 3,3.89 3,5V19C3,20.11 3.89,21 5,21H19C20.11,21 21,20.11 21,19V5C21,3.89 20.11,3 19,3H5M5,5H19V19H5V5M7,7V9H17V7H7M7,11V13H17V11H7M7,15V17H14V15H7Z"/>
      </svg>
    </button>
    <button :class="`btn-ico ${chatCssColorCls}`" @click="section('chat')">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M20,16H6L4,18V4H20"/>
      </svg>
    </button>
    <button :class="`btn-ico ${statsCssColorCls}`" @click="section('stats')">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M13,2.05V5.08C16.39,5.57 19,8.47 19,12C19,12.9 18.82,13.75 18.5,14.54L21.12,16.07C21.68,14.83 22,13.45 22,12C22,6.82 18.05,2.55 13,2.05M12,19A7,7 0 0,1 5,12C5,8.47 7.61,5.57 11,5.08V2.05C5.94,2.55 2,6.81 2,12A10,10 0 0,0 12,22C15.3,22 18.23,20.39 20.05,17.91L17.45,16.38C16.17,18 14.21,19 12,19Z"/>
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'Controls',
  props: {
    isPlayer: Boolean,
    isReady: Boolean,
    isSaving: Boolean,
    pendingSave: Boolean,
    activeSection: String
  },
  computed: {
    readyCssColorCls() {
      return this.isReady ? 'text-gray-400' : 'text-gray-500'
    },
    saveCssColorCls() {
      if (this.isSaving) {
        return 'text-gray-200'
      }
      if (this.pendingSave) {
        return 'text-gray-500'
      }
      return 'text-gray-400'
    },
    ordersCssColorCls() {
      return this.activeSection === 'orders' ? 'text-gray-200' : 'text-gray-400'
    },
    chatCssColorCls() {
      return this.activeSection === 'chat' ? 'text-gray-200' : 'text-gray-400'
    },
    statsCssColorCls() {
      return this.activeSection === 'stats' ? 'text-gray-200' : 'text-gray-400'
    }
  },
  methods: {
    section(key) {
      this.$emit('section', key)
    },
    ready() {
      this.isReady = !this.isReady
      this.$emit('ready', this.isReady)
    },
    save() {
      if (this.isSaving) {
        return
      }
      this.$emit('save')
    }
  }
}
</script>

<style scoped>
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
</style>
