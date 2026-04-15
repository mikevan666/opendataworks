<template>
  <section class="flex h-full min-h-0 flex-col gap-4">
    <div v-if="$slots.actions" class="shrink-0 flex justify-end">
      <div class="flex flex-wrap gap-3">
        <slot name="actions" />
      </div>
    </div>

    <div class="flex-1 min-h-0 overflow-y-auto pr-1">
      <div
        class="grid gap-5"
        :class="$slots.sidebar ? sidebarGridClass : 'grid-cols-1'"
      >
        <aside v-if="$slots.sidebar" class="min-w-0">
          <slot name="sidebar" />
        </aside>
        <div class="flex min-w-0 flex-col gap-4 pb-4">
          <slot />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  stats: {
    type: Array,
    default: () => []
  },
  sidebarGridClass: {
    type: String,
    default: 'xl:grid-cols-[300px_minmax(0,1fr)]'
  }
})
</script>
