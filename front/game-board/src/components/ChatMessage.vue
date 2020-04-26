<template>
  <div :class="`w-full flex flex-row flex-wrap py-1 text-sm ${direction === 'in' ? 'msg-in' : 'msg-out'}`">
    <div class="w-full px-1 rounded-lg border-2 msg-inner">
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
      return (this.roomMembersMap[this.message.sender].id === this.playerId) ? 'out' : 'in'
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
  @apply pr-6;
}
.msg-in .msg-inner {
  @apply bg-gray-600 border-gray-400;
}
.msg-out {
  @apply pl-6;
}
.msg-out .msg-inner {
  @apply bg-gray-700 border-gray-500;
}
</style>
