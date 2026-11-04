<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    hint?: string
    /** 是否占满整行（长文本等） */
    full?: boolean
  }>(),
  { full: false },
)
</script>

<template>
  <a-form-item
    :label="label"
    :extra="hint || undefined"
    class="row"
    :class="{ full }"
  >
    <slot />
  </a-form-item>
</template>

<style scoped>
.row {
  margin-bottom: 0;
  min-width: 0;
}

.row.full {
  grid-column: 1 / -1;
}

.row :deep(.ant-input-number),
.row :deep(.ant-select),
.row :deep(.ant-input),
.row :deep(textarea.ant-input) {
  width: 100%;
}
</style>
