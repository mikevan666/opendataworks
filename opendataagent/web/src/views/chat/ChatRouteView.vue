<template>
  <div class="chat-route">
    <AgentChatView />
  </div>
</template>

<script setup>
import AgentChatView from './AgentChatView.vue'
</script>

<style scoped>
.chat-route {
  height: 100%;
  min-height: 0;
}
</style>
