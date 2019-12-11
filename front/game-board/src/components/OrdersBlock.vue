<template>
  <div
    class="w-full flex flex-row flex-wrap border-t first:border-t-0 border-gray-600"
  >
    <button :class="`w-full flex py-2 px-2 text-left bg-gray-700 border-gray-600 focus:outline-none ${isPlayer ? 'country-self' : ''} ${expanded ? 'country-expanded' : ''}`" @click="toggle">
      <span class="w-full text-gray-200 leading-tight">{{ country }}</span>
      <svg class="ml-1 h-6 w-6 fill-current text-gray-200" viewBox="0 0 24 24">
        <path v-if="!expanded" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
        <path v-else d="M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z"/>
      </svg>
    </button>
    <div v-if="expanded" class="flex-1 flex-row flex-wrap px-2 py-1 items-center bg-gray-700">
      <order
        v-for="order in orders"
        :key="order.id"
        :territories="territories"
        :order="order"
      ></order>
    </div>
  </div>
</template>

<script>
import Order from './Order'

export default {
  name: 'OrdersBlock',
  components: {
    Order
  },
  props: {
    country: {
      type: String,
      default: null
    },
    territories: {
      type: Object,
      default: () => ({})
    },
    orders: {
      type: Array,
      default: () => ([])
    },
    isPlayer: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      expanded: !!this.isPlayer
    }
  },
  methods: {
    toggle() {
      this.expanded = !this.expanded
    }
  }
}
</script>

<style scoped>
.country-self {
  @apply bg-gray-600;
}
.country-expanded {
  @apply border-b;
}
</style>
