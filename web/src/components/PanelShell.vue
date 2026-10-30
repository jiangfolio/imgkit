<script setup lang="ts">
defineProps<{
  title: string
  desc: string
  loading: boolean
  error: string
  canSubmit: boolean
}>()
defineEmits<{ submit: [] }>()
</script>

<template>
  <section class="panel">
    <header class="head">
      <h2>{{ title }}</h2>
      <p>{{ desc }}</p>
    </header>
    <div class="body">
      <slot />
    </div>
    <footer class="foot">
      <p v-if="error" class="err">{{ error }}</p>
      <button
        type="button"
        class="primary"
        :disabled="!canSubmit || loading"
        @click="$emit('submit')"
      >
        {{ loading ? '处理中…' : '开始处理并下载' }}
      </button>
    </footer>
  </section>
</template>

<style scoped>
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-panel);
  padding: 1.25rem;
}

.head h2 {
  margin: 0 0 0.25rem;
  font-size: 1.15rem;
}

.head p {
  margin: 0 0 1rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.foot {
  margin-top: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: flex-start;
}

.primary {
  border: 0;
  background: var(--accent);
  color: #fff;
  padding: 0.55rem 1rem;
  border-radius: var(--radius-ctrl);
}

.primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.err {
  margin: 0;
  color: var(--danger);
  font-size: 0.9rem;
}
</style>
