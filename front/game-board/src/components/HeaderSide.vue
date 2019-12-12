<template>
  <div v-if="userId" class="w-64 xl:w-1/5 flex items-center justify-end px-4 py-2 bg-gray-700">
    <button class="h-8 w-8 mx-1 text-gray-400 rounded-full hover:bg-gray-800 hover:text-gray-200 focus:outline-none">
      <svg class="h-6 w-6 mx-auto fill-current" viewBox="0 0 24 24">
        <path d="M16,17H7V10.5C7,8 9,6 11.5,6C14,6 16,8 16,10.5M18,16V10.5C18,7.43 15.86,4.86 13,4.18V3.5A1.5,1.5 0 0,0 11.5,2A1.5,1.5 0 0,0 10,3.5V4.18C7.13,4.86 5,7.43 5,10.5V16L3,18V19H20V18M11.5,22A2,2 0 0,0 13.5,20H9.5A2,2 0 0,0 11.5,22Z"/>
      </svg>
    </button>
    <button class="h-8 w-8 mx-1 text-gray-400 rounded-full hover:bg-gray-800 hover:text-gray-200 focus:outline-none">
      <svg class="h-6 w-6 mx-auto fill-current" viewBox="0 0 24 24">
        <path d="M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z"/>
      </svg>
    </button>
    <button class="py-1 flex items-center rounded-lg hover:bg-gray-800 focus:outline-none">
      <span class="ml-5 mr-3 text-left text-sm font-medium text-white">{{ username }}</span>
      <img v-if="avatarSrc" class="h-8 w-8 rounded-full object-cover border-2 border-gray-600" :src="avatarSrc" />
      <div v-else class="block h-8 w-8 rounded-full bg-gray-600 border-2 border-gray-600"></div>
      <svg class="ml-1 h-6 w-6 fill-current text-gray-400" viewBox="0 0 24 24">
        <path d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
      </svg>
    </button>
  </div>
  <div v-else class="w-64 xl:w-1/5 flex items-center justify-end px-4 py-2 bg-gray-700"></div>
</template>

<script>
export default {
  name: 'HeaderSide',
  props: {
    userId: {
      type: Number,
      default: null
    },
    username: {
      type: String,
      default: null
    },
    avatarSrc: {
      type: String,
      default: null
    }
  }
}
</script>
