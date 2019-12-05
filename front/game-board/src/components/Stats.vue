<template>
  <div v-if="!loading" class="h-full flex flex-col">
    <div class="flex px-4 py-1 items-center border-b border-gray-600">
      <span class="w-full text-lg text-white">Stats</span>
    </div>
    <div class="flex flex-row flex-wrap overflow-y-auto stats-list">
      <div
        v-for="country in countries"
        :key="country.name"
        class="w-full mx-auto flex bg-gray-700 stats-element border-t first:border-t-0 border-gray-600"
        @click="selected(country.name)"
      >
        <div :class="`flex items-center px-4 py-4 ml-1 ${country.unread ? 'country-unread' : ''}`">
          <div class="block h-12 w-12 rounded-full bg-gray-200">
          </div>
          <div class="ml-3 text-left">
            <p class="text-lg leading-tight text-gray-100">{{ country.name }}</p>
            <p class="text-sm text-gray-400">3 days ago</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="h-full flex items-center justify-center">
    <dot-spinner></dot-spinner>
  </div>
</template>

<script>
import DotSpinner from './DotSpinner'

export default {
  name: 'Stats',
  components: {
    DotSpinner
  },
  data() {
    return {
      loading: true,
      countries: []
    }
  },
  methods: {

  }
}
</script>

<style scoped>
</style>
