<template>
  <div v-if="display" class="mr-5 flex items-center justify-between">
    <button class="btn-ico" :disabled="!rewindEnabled" @click="begin">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M18.41,7.41L17,6L11,12L17,18L18.41,16.59L13.83,12L18.41,7.41M12.41,7.41L11,6L5,12L11,18L12.41,16.59L7.83,12L12.41,7.41Z"/>
      </svg>
    </button>
    <button class="btn-ico" :disabled="!rewindEnabled" @click="rewind">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z"/>
      </svg>
    </button>
    <span class="mx-3 w-24 text-center text-sm font-medium text-gray-200">{{ label }}</span>
    <button class="btn-ico" :disabled="!forwardEnabled" @click="forward">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
      </svg>
    </button>
    <button class="btn-ico" :disabled="!forwardEnabled" @click="end">
      <svg class="btn-ico-svg" viewBox="0 0 24 24">
        <path d="M5.59,7.41L7,6L13,12L7,18L5.59,16.59L10.17,12L5.59,7.41M11.59,7.41L13,6L19,12L13,18L11.59,16.59L16.17,12L11.59,7.41Z"/>
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'TimeControls',
  props: {
    active: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    step: {
      type: Object,
      default: null
    },
    rewindEnabled: {
      type: Boolean,
      default: true
    },
    forwardEnabled: {
      type: Boolean,
      default: true
    }
  },
  computed: {
    label() {
      if (this.loading) {
        return '...'
      }
      return this.step === null ? null : this.step.label()
    },
    display() {
      return this.active && !!this.label
    }
  },
  methods: {
    begin() {
      this.$emit('begin')
    },
    rewind() {
      this.$emit('rewind')
    },
    forward() {
      this.$emit('forward')
    },
    end() {
      this.$emit('end')
    }
  }
}
</script>

<style scoped>
.btn-ico {
  @apply mx-1 text-gray-400;
}
.btn-ico:hover {
  @apply text-gray-200;
}
.btn-ico:focus {
  outline: none;
}
.btn-ico:disabled {
  @apply text-gray-600;
}
.btn-ico-svg {
  @apply h-6 w-6 fill-current;
}
</style>
