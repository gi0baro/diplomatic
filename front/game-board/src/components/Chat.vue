<template>
  <div class="h-full flex flex-wrap overflow-y-hidden">
    <div ref="scrollable" class="w-full flex flex-row flex-wrap overflow-y-auto chat px-1">
      <div class="w-full flex flex-col flex-wrap justify-end">
        <chat-message
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :playerId="playerId"
          :roomMembersMap="roomPlayersMap"
          :showSender="room.type === 0"
        ></chat-message>
      </div>
    </div>
    <div class="w-full flex px-2 py-1 items-center justify-between border-t border-gray-600">
      <div class="w-full relative">
        <textarea
          ref="input"
          class="h-32 w-full block bg-gray-900 rounded-lg pl-2 pr-6 py-1 text-sm placeholder-gray-400 text-gray-100 focus:outline-none text-input"
          placeholder="Write something here.."
          v-model="inputMessage"
          @keyup.enter="send"
        ></textarea>
        <button
          class="absolute bottom-0 right-0 h-8 w-8 ml-1 text-gray-400 focus:outline-none btn-send"
          :disabled="sendDisabled"
          @click="send"
        >
          <svg class="h-6 w-6 mx-auto fill-current" viewBox="0 0 24 24">
            <path d="M8,7.71L18,12L8,16.29V12.95L15.14,12L8,11.05V7.71M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4Z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import ChatMessage from './ChatMessage'

export default {
  name: 'Chat',
  components: {
    ChatMessage
  },
  props: {
    room: {
      type: Object,
      default: () => ({
        type: 0,
        messages: [],
        members: [],
        isSending: false
      })
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
      inputMessage: ''
    }
  },
  mounted() {
    if (this.room.messages.length === 0) {
      return
    }
    this.$emit('read', this.room.messages[this.room.messages.length - 1])
  },
  computed: {
    messages() {
      return this.room.messages
    },
    roomPlayersMap() {
      let rv = {}
      this.room.members.forEach((obj) => {
        rv[obj.id] = this.playersMap[obj.player]
      })
      return rv
    },
    sendDisabled() {
      return !this.inputMessage || this.room.isSending
    }
  },
  watch: {
    messages() {
      this.$nextTick(() => {
        this.$refs.scrollable.scrollTop = (this.$refs.scrollable.scrollHeight - this.$refs.scrollable.clientHeight)
      })
    }
  },
  methods: {
    send() {
      if (this.sendDisabled) {
        return
      }
      this.$emit('send', this.room.id, this.inputMessage)
      this.inputMessage = ''
    },
    messageSent() {
      // this.inputMessage = ''
      // this.$refs.input.focus()
    },
    messageFailed() {}
  }
}
</script>

<style scoped>
.chat {
  height: calc(100% - 8rem - 1px - 0.5rem);
}
.chat::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
  background-color: #2d3748;
}
.chat::-webkit-scrollbar {
  width: 6px;
  background-color: #2d3748;
}
.chat::-webkit-scrollbar-thumb {
  background-color: #718096;
}
.text-input {
  resize: none;
}
.text-input:disabled {
  @apply text-gray-600;
}
.btn-send:disabled {
  @apply text-gray-600;
}
.text-input::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 4px rgba(0,0,0,0.3);
  background-color: #2d3748;
}
.text-input::-webkit-scrollbar {
  width: 4px;
  background-color: #2d3748;
}
.text-input::-webkit-scrollbar-thumb {
  background-color: #718096;
}
</style>
