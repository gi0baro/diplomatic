<template>
  <div class="flex flex-row flex-wrap overflow-y-auto chat-list">
    <button
      v-for="room in rooms"
      :key="room.name"
      class="w-full mx-auto flex bg-gray-700 btn-chat border-t first:border-t-0 border-gray-600"
      @click="selected(room.name)"
    >
      <div :class="`flex items-center px-4 py-4 ml-1 ${room.unread ? 'room-unread' : ''}`">
        <div class="block h-12 w-12 rounded-full bg-gray-200">
        </div>
        <div class="ml-3 text-left">
          <p class="text-lg leading-tight text-gray-100">{{ room.name }}</p>
          <p class="text-sm text-gray-400">3 days ago</p>
        </div>
      </div>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ChatList',
  data() {
    return {
      rooms: [
        {name: 'Global', unread: true},
        {name: 'Russia'},
        {name: 'England'},
        {name: '100'},
        {name: '101'},
        {name: '102'},
        {name: '103'},
        {name: '104'},
        {name: '105'},
        {name: '106'},
        {name: '107'},
        {name: '108'},
        {name: '109'},
        {name: '110'},
        {name: '111'},
        {name: '112'},
        {name: '113'},
        {name: '114'},
        {name: '115'},
        {name: '116'},
        {name: '117'}
      ]
    }
  },
  methods: {
    selected(val) {
      this.$emit('selected', val)
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
.chat-list::-webkit-scrollbar-track {
  -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3);
  background-color: #2d3748;
}
.chat-list::-webkit-scrollbar {
  width: 6px;
  background-color: #2d3748;
}
.chat-list::-webkit-scrollbar-thumb {
  background-color: #718096;
}
</style>
