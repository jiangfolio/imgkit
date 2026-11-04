<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { InboxOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'

const props = defineProps<{ modelValue: File | null }>()
const emit = defineEmits<{ 'update:modelValue': [File | null] }>()

const previewUrl = ref('')

const preview = computed(() => previewUrl.value)

watch(
  () => props.modelValue,
  (file) => {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = ''
    }
    if (file) previewUrl.value = URL.createObjectURL(file)
  },
)

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const ok = ['image/png', 'image/jpeg', 'image/webp'].includes(file.type)
  if (!ok) {
    message.error('仅支持 PNG / JPEG / WebP')
    return false
  }
  emit('update:modelValue', file as File)
  return false
}

function clear() {
  emit('update:modelValue', null)
}
</script>

<template>
  <div>
    <a-upload-dragger
      v-if="!modelValue"
      name="file"
      :multiple="false"
      :show-upload-list="false"
      accept="image/png,image/jpeg,image/webp"
      :before-upload="beforeUpload"
    >
      <p class="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p class="ant-upload-text">拖拽图片到此处，或点击选择</p>
      <p class="ant-upload-hint">PNG / JPEG / WebP · 不支持 SVG · 不落盘</p>
    </a-upload-dragger>

    <a-card v-else size="small" class="preview-card">
      <div class="preview">
        <a-image :src="preview" :width="96" :height="96" alt="预览" />
        <div class="meta">
          <div class="name">{{ modelValue.name }}</div>
          <a-typography-text type="secondary">
            {{ (modelValue.size / 1024).toFixed(1) }} KB
          </a-typography-text>
          <div>
            <a-button type="link" size="small" danger @click="clear">
              <template #icon><DeleteOutlined /></template>
              更换
            </a-button>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<style scoped>
.preview {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.preview :deep(.ant-image img) {
  object-fit: contain;
  background: #fff;
}

.meta .name {
  font-weight: 600;
  word-break: break-all;
}
</style>
