<template>
  <div :class="`w-full flex flex-row flex-wrap my-1 px-1 rounded-lg border-2 text-sm ${direction === 'in' ? 'msg-in' : 'msg-out'}`">
    <span
      v-if="senderDisplay"
      class="w-full flex mb-1 text-xs text-gray-200 uppercase"
    >
      {{ senderName }}
    </span>
    <span class="text-gray-100">
      {{ message.text }}
    </span>
  </div>
</template>

<script>
export default {
  name: 'ChatMessage',
  props: {
    message: {
      type: Object,
      default: () => ({
        text: null,
        sender: null
      })
    },
    playerId: {
      type: Number,
      default: null
    },
    roomMembersMap: {
      type: Object,
      default: () => ({})
    },
    showSender: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    direction() {
      return (this.message.sender === this.playerId) ? 'out' : 'in'
    },
    senderDisplay() {
      return this.showSender && this.direction == 'in'
    },
    senderName() {
      if (!this.showSender) {
        return null
      }
      if (!this.message.sender) {
        return 'nuDiplomacy'
      }
      return this.roomMembersMap[this.message.sender].country
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
