<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  InboxOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'

const props = defineProps<{ modelValue: File[] }>()
const emit = defineEmits<{ 'update:modelValue': [File[]] }>()

const error = ref('')
const previews = ref<{ name: string; url: string; size: number }[]>([])

const count = computed(() => props.modelValue.length)

watch(
  () => props.modelValue,
  (files) => {
    for (const p of previews.value) URL.revokeObjectURL(p.url)
    previews.value = files.map((f) => ({
      name: f.name,
      url: URL.createObjectURL(f),
      size: f.size,
    }))
  },
  { deep: true },
)

onBeforeUnmount(() => {
  for (const p of previews.value) URL.revokeObjectURL(p.url)
})

function acceptFiles(list: File[]) {
  error.value = ''
  const next = [...props.modelValue]
  for (const file of list) {
    const ok = ['image/png', 'image/jpeg', 'image/webp'].includes(file.type)
    if (!ok) {
      error.value = '仅支持 PNG / JPEG / WebP，已跳过不支持的文件'
      continue
    }
    if (next.length >= 20) {
      error.value = '最多 20 张图'
      message.warning('最多 20 张图')
      break
    }
    next.push(file)
  }
  emit('update:modelValue', next)
}

const beforeUpload: UploadProps['beforeUpload'] = (file, fileList) => {
  // 仅在本批次第一个文件时处理整批，避免重复追加
  if (file === fileList[0]) {
    acceptFiles(fileList as File[])
  }
  return false
}

function removeAt(i: number) {
  const next = props.modelValue.slice()
  next.splice(i, 1)
  emit('update:modelValue', next)
}

function clear() {
  emit('update:modelValue', [])
  error.value = ''
}

function move(i: number, delta: number) {
  const j = i + delta
  if (j < 0 || j >= props.modelValue.length) return
  const next = props.modelValue.slice()
  const [item] = next.splice(i, 1)
  next.splice(j, 0, item)
  emit('update:modelValue', next)
}
</script>

<template>
  <div>
    <a-upload-dragger
      name="files"
      :multiple="true"
      :show-upload-list="false"
      accept="image/png,image/jpeg,image/webp"
      :before-upload="beforeUpload"
    >
      <p class="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p class="ant-upload-text">
        {{ count === 0 ? '拖拽多张图片到此处，或点击选择' : '继续添加图片' }}
      </p>
      <p class="ant-upload-hint">PNG / JPEG / WebP · 最多 20 张 · 不落盘</p>
    </a-upload-dragger>

    <a-alert v-if="error" type="warning" :message="error" show-icon class="err" />

    <a-list v-if="count > 0" class="list" item-layout="horizontal" :data-source="previews">
      <template #header>
        <div class="toolbar">
          <a-typography-text>已选 {{ count }} 张</a-typography-text>
          <a-button type="link" danger size="small" @click="clear">清空</a-button>
        </div>
      </template>
      <template #renderItem="{ item, index }">
        <a-list-item>
          <template #actions>
            <a-button type="text" size="small" :disabled="index === 0" @click="move(index, -1)">
              <ArrowUpOutlined />
            </a-button>
            <a-button
              type="text"
              size="small"
              :disabled="index === count - 1"
              @click="move(index, 1)"
            >
              <ArrowDownOutlined />
            </a-button>
            <a-button type="text" size="small" danger @click="removeAt(index)">
              <DeleteOutlined />
            </a-button>
          </template>
          <a-list-item-meta>
            <template #avatar>
              <a-image :src="item.url" :width="56" :height="56" :preview="true" />
            </template>
            <template #title>{{ item.name }}</template>
            <template #description>{{ (item.size / 1024).toFixed(1) }} KB</template>
          </a-list-item-meta>
        </a-list-item>
      </template>
    </a-list>
  </div>
</template>

<style scoped>
.err {
  margin-top: 0.75rem;
}

.list {
  margin-top: 0.75rem;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list :deep(.ant-image img) {
  object-fit: contain;
  background: #fff;
}
</style>
