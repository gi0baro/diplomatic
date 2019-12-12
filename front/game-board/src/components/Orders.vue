<template>
  <div v-if="!loading" class="h-full flex flex-col">
    <div class="flex px-4 py-1 items-center border-b border-gray-600">
      <span class="w-full text-lg text-white">Orders</span>
    </div>
    <div class="flex flex-row flex-wrap overflow-y-auto order-blocks">
      <orders-block
        v-for="orderGroup in orders"
        :key="orderGroup.country"
        :territories="territories"
        :country="orderGroup.country"
        :orders="orderGroup.orders"
        :isPlayer="orderGroup.self"
      ></orders-block>
    </div>
  </div>
  <div v-else class="h-full flex items-center justify-center">
    <dot-spinner></dot-spinner>
  </div>
</template>

<script>
import DotSpinner from './DotSpinner'
import OrdersBlock from './OrdersBlock'

export default {
  name: 'Orders',
  components: {
    DotSpinner,
    OrdersBlock
  },
  props: {
    player: {
      type: String,
      default: null
    },
    territories: {
      type: Object,
      default: () => ({})
    },
    step: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    orders() {
      if (this.step === null) {
        return []
      }
      let rv = []
      Object.keys(this.step.orders || {}).forEach((country) => {
        if (this.step.orders[country].length > 0) {
          rv.push({
            country: country,
            orders: this.step.orders[country],
            self: (country === this.player)
          })
        }
      })
      return rv.sort((a, b) => {
        return (a.self && !b.self) ? -1 : 1
      })
    }
  }
}
</script>

<style scoped>
.order-blocks::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
  background-color: #2d3748;
}
.order-blocks::-webkit-scrollbar {
  width: 6px;
  background-color: #2d3748;
}
.order-blocks::-webkit-scrollbar-thumb {
  background-color: #718096;
}
</style>
