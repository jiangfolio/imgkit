<script setup lang="ts">
defineProps<{ label: string; hint?: string }>()
</script>

<template>
  <label class="row">
    <span class="label">{{ label }}</span>
    <span class="ctrl"><slot /></span>
    <span v-if="hint" class="hint">{{ hint }}</span>
  </label>
</template>

<style scoped>
.row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: 0.35rem 0.75rem;
  align-items: center;
}

.label {
  font-size: 0.9rem;
  color: var(--text);
}

.ctrl :deep(input),
.ctrl :deep(select) {
  width: 100%;
  max-width: 16rem;
  border: 1px solid var(--border);
  background: #fff;
  border-radius: var(--radius-ctrl);
  padding: 0.4rem 0.55rem;
}

.hint {
  grid-column: 2;
  color: var(--muted);
  font-size: 0.8rem;
}

@media (max-width: 560px) {
  .row {
    grid-template-columns: 1fr;
  }
  .hint {
    grid-column: 1;
  }
}
</style>
