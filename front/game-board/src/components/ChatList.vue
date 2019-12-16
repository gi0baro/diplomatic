<template>
  <div class="flex flex-row flex-wrap overflow-y-auto chat-list">
    <chat-list-item
      v-for="room in rooms"
      :key="room.id"
      :room="room"
      :reading="readingsMap[room.id]"
      :playersMap="playersMap"
      @selected="selected"
      @needMessages="needMessages"
    >
    </chat-list-item>
  </div>
</template>

<script>
import ChatListItem from './ChatListItem'

export default {
  name: 'ChatList',
  components: {
    ChatListItem
  },
  props: {
    rooms: {
      type: Array,
      default: () => ([])
    },
    readingsMap: {
      type: Object,
      default: () => ({})
    },
    playersMap: {
      type: Object,
      default: () => ({})
    }
  },
  methods: {
    selected(val) {
      this.$emit('selected', val)
    },
    needMessages(val) {
      this.$emit('needMessages', val)
    }
  }
}
</script>

<style scoped>
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
