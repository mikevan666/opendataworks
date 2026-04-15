<template>
  <div class="space-y-1">
    <button
      type="button"
      class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm transition"
      :class="node.type === 'file' && node.documentId === selectedDocumentId
        ? 'bg-blue-700 text-white'
        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
      :style="{ paddingLeft: `${12 + level * 16}px` }"
      @click="handleClick"
    >
      <ChevronRight
        v-if="node.type === 'folder'"
        class="h-4 w-4 shrink-0 transition"
        :class="{ 'rotate-90': expanded }"
      />
      <span v-else class="w-4 shrink-0" />

      <component
        :is="node.type === 'folder' ? FolderTree : FileText"
        class="h-4 w-4 shrink-0"
      />

      <span class="min-w-0 truncate">{{ node.label }}</span>
    </button>

    <div v-if="node.type === 'folder' && expanded" class="space-y-1">
      <SkillFileTreeNode
        v-for="child in node.children || []"
        :key="child.key"
        :node="child"
        :level="level + 1"
        :selected-document-id="selectedDocumentId"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ChevronRight, FileText, FolderTree } from 'lucide-vue-next'

defineOptions({
  name: 'SkillFileTreeNode'
})

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  level: {
    type: Number,
    default: 0
  },
  selectedDocumentId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])

const expanded = ref(true)

const handleClick = () => {
  if (props.node.type === 'folder') {
    expanded.value = !expanded.value
    return
  }
  if (props.node.documentId) {
    emit('select', props.node.documentId)
  }
}
</script>
