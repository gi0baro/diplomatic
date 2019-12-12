<template>
  <div :class="`flex items-center text-sm text-gray-200 py-1 ${order.stage === 2 ? 'order-failed' : ''}`">
    <div class="flex">
      <svg v-if="isHold" class="order-ico" viewBox="0 0 24 24">
        <path d="M21,11C21,16.55 17.16,21.74 12,23C6.84,21.74 3,16.55 3,11V5L12,1L21,5V11M12,21C15.75,20 19,15.54 19,11.22V6.3L12,3.18L5,6.3V11.22C5,15.54 8.25,20 12,21Z"/>
      </svg>
      <svg v-if="isMove" class="order-ico" viewBox="0 0 24 24">
        <path d="M11,2V4.07C7.38,4.53 4.53,7.38 4.07,11H2V13H4.07C4.53,16.62 7.38,19.47 11,19.93V22H13V19.93C16.62,19.47 19.47,16.62 19.93,13H22V11H19.93C19.47,7.38 16.62,4.53 13,4.07V2M11,6.08V8H13V6.09C15.5,6.5 17.5,8.5 17.92,11H16V13H17.91C17.5,15.5 15.5,17.5 13,17.92V16H11V17.91C8.5,17.5 6.5,15.5 6.08,13H8V11H6.09C6.5,8.5 8.5,6.5 11,6.08M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11Z"/>
      </svg>
      <svg v-if="isSupportHold" class="order-ico" viewBox="0 0 24 24">
        <path d="M21 11C21 16.55 17.16 21.74 12 23C6.84 21.74 3 16.55 3 11V5L12 1L21 5V11M12 21C15.75 20 19 15.54 19 11.22V6.3L12 3.18L5 6.3V11.22C5 15.54 8.25 20 12 21M15.05 16L11.97 14.15L8.9 16L9.71 12.5L7 10.16L10.58 9.85L11.97 6.55L13.37 9.84L16.95 10.15L14.23 12.5L15.05 16"/>
      </svg>
      <svg v-if="isSupportMove" class="order-ico" viewBox="0 0 24 24">
        <path d="M12,2L16,6H13V13.82L22.39,19.25L21.39,21L12,15.56L2.61,21L1.61,19.25L11,13.82V6H8L12,2Z"/>
      </svg>
      <svg v-if="isConvoy" class="order-ico" viewBox="0 0 24 24">
        <path d="M2.2,9.76H4.44V11.94H2.2V9.76H2.2M4.95,9.76H7.2V11.94H4.95V9.76H4.95M4.95,6.96H7.2V9.14H4.95V6.96M7.71,9.76H9.95V11.94H7.71V9.76H7.71M7.71,6.96H9.95V9.14H7.71V6.96M10.46,9.76H12.71V11.94H10.46V9.76H10.46M10.46,6.96H12.71V9.14H10.46V6.96M13.22,9.76H15.46V11.94H13.22V9.76H13.22M10.46,4.16H12.71V6.34H10.46V4.16M5.33,15.09C5.68,15.09 5.96,15.36 5.96,15.7C5.96,16.03 5.68,16.31 5.33,16.31C5,16.31 4.71,16.03 4.71,15.7C4.71,15.36 5,15.09 5.33,15.09M22.69,10.89V10.89L23,11.06L22.84,11.37C22.2,12.58 20.87,12.95 19.57,12.89C17.62,17.6 13.37,19.84 8.23,19.84C5.57,19.84 3.13,18.87 1.74,16.58L1.72,16.54L1.5,16.14C1.05,15.13 0.89,14.03 1,12.92L1.03,12.59H15.8C16.33,12.59 16.87,12.5 17.36,12.34L18.12,12C17.81,11.6 17.64,11.09 17.6,10.59C17.53,9.91 17.67,9 18.15,8.5L18.39,8.22L18.67,8.44C19.38,9 19.97,9.77 20.08,10.65C20.93,10.41 21.94,10.46 22.69,10.89M5.34,16.85V16.85C6,16.85 6.5,16.33 6.5,15.7C6.5,15.06 6,14.54 5.33,14.54C4.68,14.54 4.15,15.06 4.15,15.7C4.15,16.34 4.68,16.85 5.34,16.85Z"/>
      </svg>
      <svg v-if="isRetreat" class="order-ico" viewBox="0 0 24 24">
        <path d="M5,13L9,17L7.6,18.42L1.18,12L7.6,5.58L9,7L5,11H21V13H5M21,6V8H11V6H21M21,16V18H11V16H21Z"/>
      </svg>
      <svg v-if="isBuildArmy" class="order-ico" viewBox="0 0 24 24">
        <path d="M20,12H4V11H6L7,6H12L13,11H20V12M13.22,7L13.62,9H22V7H13.22M22,16A3,3 0 0,1 19,19H5A3,3 0 0,1 2,16A3,3 0 0,1 5,13H19A3,3 0 0,1 22,16M6,16A1,1 0 0,0 5,15A1,1 0 0,0 4,16A1,1 0 0,0 5,17A1,1 0 0,0 6,16M13,16A1,1 0 0,0 12,15A1,1 0 0,0 11,16A1,1 0 0,0 12,17A1,1 0 0,0 13,16M20,16A1,1 0 0,0 19,15A1,1 0 0,0 18,16A1,1 0 0,0 19,17A1,1 0 0,0 20,16Z"/>
      </svg>
      <svg v-if="isBuildFleet" class="order-ico" viewBox="0 0 24 24">
        <path d="M6,6H18V9.96L12,8L6,9.96M3.94,19H4C5.6,19 7,18.12 8,17C9,18.12 10.4,19 12,19C13.6,19 15,18.12 16,17C17,18.12 18.4,19 20,19H20.05L21.95,12.31C22.03,12.06 22,11.78 21.89,11.54C21.76,11.3 21.55,11.12 21.29,11.04L20,10.62V6C20,4.89 19.1,4 18,4H15V1H9V4H6A2,2 0 0,0 4,6V10.62L2.71,11.04C2.45,11.12 2.24,11.3 2.11,11.54C2,11.78 1.97,12.06 2.05,12.31M20,21C18.61,21 17.22,20.53 16,19.67C13.56,21.38 10.44,21.38 8,19.67C6.78,20.53 5.39,21 4,21H2V23H4C5.37,23 6.74,22.65 8,22C10.5,23.3 13.5,23.3 16,22C17.26,22.65 18.62,23 20,23H22V21H20Z"/>
      </svg>
      <svg v-if="isDisband" class="order-ico" viewBox="0 0 24 24">
        <path d="M4.15,21.46L5.47,19.58C3.35,17.74 2,15.03 2,12A10,10 0 0,1 12,2C13.78,2 15.44,2.46 16.89,3.27L18.21,1.39L19.85,2.54L18.53,4.42C20.65,6.26 22,8.97 22,12A10,10 0 0,1 12,22C10.22,22 8.56,21.54 7.11,20.73L5.79,22.61L4.15,21.46M12,4A8,8 0 0,0 4,12C4,14.35 5,16.46 6.63,17.93L15.73,4.92C14.62,4.33 13.35,4 12,4M12,20A8,8 0 0,0 20,12C20,9.65 19,7.54 17.37,6.07L8.27,19.08C9.38,19.67 10.65,20 12,20Z"/>
      </svg>
    </div>
    <div class="flex">
      <span class="ml-2">{{ label }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Order',
  props: {
    territories: {
      type: Object,
      default: () => ({})
    },
    order: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      T: {
        get: (val) => (`:TERRITORY: ${val}`)
      }
    }
  },
  mounted() {
    this.T = window.T || this.T
  },
  computed: {
    action() {
      if (this.order === null) {
        return null
      }
      if (this.order.type === 6 && this.order.data.troop !== undefined) {
        if (this.order.data.troop === 0) {
          return 'build_army'
        }
        if (this.order.data.troop === 1) {
          return 'build_fleet'
        }
      }
      return {
        0: 'hold',
        1: 'move',
        2: 'support_hold',
        3: 'support_move',
        4: 'convoy',
        5: 'retreat',
        7: 'disband'
      }[this.order.type]
    },
    coast() {
      if (this.order === null) {
        return null
      }
      if (this.order.data.coast === undefined) {
        return null
      }
      return {
        0: 'north',
        1: 'south'
      }[this.order.data.coast]
    },
    label() {
      if (this.action === null) {
        return ''
      }
      return this.T.get(`orders.${this.action}`).replace(
        ':TERRITORY:', this.territories[this.order.territory]
      ).replace(
        ':SRC:', this.territories[this.order.data.src]
      ).replace(
        ':DST:', this.territories[this.order.data.dst]
      ).replace(
        ':THROUGH:', (this.order.data.through !== undefined ? this.T.get('orders.vec.through') : '')
      ).replace(
        ':COAST:', (this.coast !== null ? this.T.get(`orders.coasts.${this.coast}`) : '')
      )
      // .replace(
      //   ':TROOP:', this.T.get(`orders.troops.${this.order.data.troop === 0 ? 'army' : 'fleet'}`)
      // )
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
    isRetreat() {
      return this.action == 'retreat'
    },
    isBuildArmy() {
      return this.action == 'build_army'
    },
    isBuildFleet() {
      return this.action == 'build_fleet'
    },
    isDisband() {
      return this.action == 'disband'
    }
  }
}
</script>

<style scoped>
.order-ico {
  @apply h-5 w-5 fill-current;
}
.order-failed {
  @apply text-gray-500;
}
</style>
