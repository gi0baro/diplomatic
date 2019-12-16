<template>
  <div class="h-full flex flex-col">
    <div class="flex px-4 py-1 items-center border-b border-gray-600">
      <span class="w-full text-lg text-white">Chat</span>
      <button v-if="activeRoom" class="mx-1 text-gray-400 focus:outline-none" @click="back">
        <svg class="h-6 w-6 fill-current" viewBox="0 0 24 24">
          <path d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z"/>
        </svg>
      </button>
    </div>
    <transition name="fade" mode="out-in">
      <chat-list 
        v-if="!activeRoom" 
        :rooms="rooms"
        :readingsMap="readingsMap"
        :playersMap="playersMap"
        @selected="selectedRoom"
        @needMessages="roomNeedMessages"
      ></chat-list>
      <chat
        v-else 
        :room="activeRoom"
        :playerId="playerId"
        :playersMap="playersMap"
        @send="sendMessage"
        @read="readMessage"
        ref="active_chat"
      ></chat>
    </transition>
  </div>
</template>

<script>
import ChatList from './ChatList'
import Chat from './Chat'

export default {
  name: 'ChatFragment',
  components: {
    ChatList,
    Chat
  },
  props: {
    rooms: {
      type: Array,
      default: () => ([])
    },
    roomsMap: {
      type: Object,
      default: () => ({})
    },
    readings: {
      type: Array,
      default: () => ([])
    },
    playerId: {
      type: Number,
      default: null
    },
    playersMap: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      activeRoom: null
    }
  },
  computed: {
    readingsMap() {
      let rv = {}
      this.readings.forEach((element) => {
        rv[element.room] = element
      })
      return rv
    }
  },
  methods: {
    selectedRoom(val) {
      this.activeRoom = this.roomsMap[val]
    },
    roomNeedMessages(val) {
      this.$emit('fetchRoomMessages', this.roomsMap[val])
    },
    sendMessage(roomId, message) {
      this.$emit('send', this.roomsMap[roomId], message)
    },
    readMessage(message) {
      this.$emit('read', this.readingsMap[message.room], message)
    },
    back() {
      if (this.activeRoom !== null) {
        this.activeRoom = null
      }
    },
    messageSent(message) {
      this.readingsMap[message.room].message = message.id
      this.$refs.active_chat.messageSent()
    },
    messageFailed() {
      this.$refs.active_chat.messageFailed()
    }
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
