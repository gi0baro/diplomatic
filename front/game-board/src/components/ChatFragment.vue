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
      <chat-list v-if="!activeRoom" @selected="selectedRoom"></chat-list>
      <chat v-else :name="activeRoom"></chat>
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
  data() {
    return {
      activeRoom: null
    }
  },
  methods: {
    selectedRoom(val) {
      this.activeRoom = val
    },
    back() {
      if (this.activeRoom !== null) {
        this.activeRoom = null
      }
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
