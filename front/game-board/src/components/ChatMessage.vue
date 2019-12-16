<template>
  <span
    :class="`w-full flex my-1 px-1 rounded-lg border-2 text-sm text-gray-100 ${direction === 'in' ? 'msg-in' : 'msg-out'}`"
  >
    {{ message.text }}
  </span>
</template>

<script>
export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      default: null
    },
    playerId: {
      type: Number,
      default: null
    }
  },
  computed: {
    direction() {
      if (this.message === null) {
        return null
      }
      return (this.message.sender === this.playerId) ? 'out' : 'in'
    }
  }
}
</script>

<style scoped>
.msg-in {
  @apply bg-gray-600 border-gray-400 mr-6;
}
.msg-out {
  @apply bg-gray-700 border-gray-500 ml-6;
}
</style>
