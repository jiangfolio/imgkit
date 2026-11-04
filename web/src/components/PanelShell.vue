<script setup lang="ts">
import { ExperimentOutlined } from '@ant-design/icons-vue'

withDefaults(
  defineProps<{
    title: string
    desc: string
    loading: boolean
    error: string
    canSubmit: boolean
    submitLabel?: string
    showSubmit?: boolean
    showHead?: boolean
  }>(),
  {
    submitLabel: '生成预览',
    showSubmit: true,
    showHead: true,
  },
)
defineEmits<{ submit: [] }>()
</script>

<template>
  <a-card class="panel" :bordered="true">
    <template v-if="showHead" #title>
      <div class="head">
        <div class="title">{{ title }}</div>
        <div class="desc">{{ desc }}</div>
      </div>
    </template>
    <div class="body">
      <slot />
    </div>
    <div class="foot">
      <a-alert v-if="error" type="error" :message="error" show-icon banner class="err" />
      <slot name="footer">
        <a-button
          v-if="showSubmit"
          type="primary"
          :loading="loading"
          :disabled="!canSubmit || loading"
          @click="$emit('submit')"
        >
          <template v-if="!loading" #icon><ExperimentOutlined /></template>
          {{ loading ? '处理中…' : submitLabel }}
        </a-button>
      </slot>
    </div>
  </a-card>
</template>

<style scoped>
.panel {
  background: var(--surface);
}

.head .title {
  font-size: 1.05rem;
  font-weight: 600;
}

.head .desc {
  margin-top: 0.2rem;
  color: var(--muted);
  font-size: 0.88rem;
  font-weight: 400;
  white-space: normal;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.foot {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  align-items: flex-start;
}

.err {
  width: 100%;
}
</style>
