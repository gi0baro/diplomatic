<template>
  <button
    class="w-full mx-auto flex bg-gray-700 btn-chat border-t first:border-t-0 border-gray-600"
    @click="selected"
  >
    <div :class="`flex items-center px-4 py-4 ml-1 ${unread ? 'room-unread' : ''}`">
      <div class="block h-12 w-12 rounded-full bg-gray-200">
      </div>
      <div class="ml-3 text-left">
        <p class="text-lg leading-tight text-gray-100">{{ name }}</p>
        <p class="text-sm text-gray-400">{{ lastMessageDate }}</p>
      </div>
    </div>
  </button>
</template>

<script>
import moment from 'moment'

export default {
  name: 'ChatListItem',
  props: {
    room: {
      type: Object,
      default: null
    },
    reading: {
      type: Object,
      default: null
    },
    playersMap: {
      type: Object,
      default: null
    }
  },
  mounted() {
    if (this.room !== null && !this.room.messagesLoaded) {
      this.$emit('needMessages', this.room.id)
    }
  },
  watch: {
    room(val) {
      if (!val.messagesLoaded) {
        this.$emit('needMessages', val.id)
      }
    }
  },
  computed: {
    name() {
      if (this.room === null) {
        return null
      }
      if (this.room.type === 0) {
        return this.room.name
      }
      return this.playersMap[this.room.members[0].player].country
    },
    lastMessage() {
      if (this.room.messages.length === 0) {
        return null
      }
      return this.room.messages[this.room.messages.length - 1]
    },
    unread() {
      if (this.room === null) {
        return false
      }
      if (!this.room.messagesLoaded) {
        return false
      }
      if (this.lastMessage === null) {
        return false
      }
      if (this.reading === null) {
        return false
      }
      return this.reading.message !== this.lastMessage.id
    },
    lastMessageDate() {
      if (this.room === null) {
        return null
      }
      let lastMessage = this.lastMessage
      if (lastMessage === null) {
        return null
      }
      return moment.utc(this.lastMessage.created_at).local().fromNow()
    }
  },
  methods: {
    selected() {
      this.$emit('selected', this.room.id)
    }
  }
}
</script>

<style scoped>
.btn-chat:focus {
  outline: none;
}
.room-unread {
  @apply ml-0 border-l-1r;
}
</style>
