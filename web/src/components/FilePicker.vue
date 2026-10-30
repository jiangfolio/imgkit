<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps<{ modelValue: File | null }>()
const emit = defineEmits<{ 'update:modelValue': [File | null] }>()

const dragOver = ref(false)
const previewUrl = ref('')
const error = ref('')

const preview = computed(() => previewUrl.value)

watch(
  () => props.modelValue,
  (file) => {
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = ''
    }
    if (file) {
      previewUrl.value = URL.createObjectURL(file)
    }
  },
)

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

function acceptFile(file: File | undefined) {
  error.value = ''
  if (!file) return
  const ok = ['image/png', 'image/jpeg', 'image/webp'].includes(file.type)
  if (!ok) {
    error.value = '仅支持 PNG / JPEG / WebP'
    emit('update:modelValue', null)
    return
  }
  emit('update:modelValue', file)
}

function onInput(e: Event) {
  const input = e.target as HTMLInputElement
  acceptFile(input.files?.[0])
  input.value = ''
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  acceptFile(e.dataTransfer?.files?.[0])
}

function clear() {
  emit('update:modelValue', null)
  error.value = ''
}
</script>

<template>
  <div
    class="picker"
    :class="{ over: dragOver }"
    @dragenter.prevent="dragOver = true"
    @dragover.prevent="dragOver = true"
    @dragleave.prevent="dragOver = false"
    @drop.prevent="onDrop"
  >
    <input
      id="file-input"
      class="sr-only"
      type="file"
      accept="image/png,image/jpeg,image/webp"
      @change="onInput"
    />
    <label v-if="!modelValue" for="file-input" class="hint">
      拖拽图片到此处，或点击选择
      <span class="sub">PNG / JPEG / WebP · 不支持 SVG · 不落盘</span>
    </label>
    <div v-else class="preview">
      <img :src="preview" alt="预览" />
      <div class="meta">
        <div class="name">{{ modelValue.name }}</div>
        <div class="sub">{{ (modelValue.size / 1024).toFixed(1) }} KB</div>
        <button type="button" class="link" @click="clear">更换</button>
      </div>
    </div>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<style scoped>
.picker {
  border: 1px dashed var(--border);
  background: var(--surface);
  border-radius: var(--radius-panel);
  padding: 1rem;
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker.over {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.hint {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  align-items: center;
  text-align: center;
  cursor: pointer;
  color: var(--text);
  width: 100%;
  padding: 1.5rem 0.5rem;
}

.sub {
  color: var(--muted);
  font-size: 0.85rem;
}

.preview {
  display: flex;
  gap: 1rem;
  align-items: center;
  width: 100%;
}

.preview img {
  width: 96px;
  height: 96px;
  object-fit: contain;
  border: 1px solid var(--border);
  border-radius: var(--radius-ctrl);
  background: #fff;
}

.meta .name {
  font-weight: 600;
  word-break: break-all;
}

.link {
  margin-top: 0.35rem;
  border: 0;
  background: transparent;
  color: var(--accent);
  padding: 0;
  text-decoration: underline;
}

.err {
  margin: 0.5rem 0 0;
  color: var(--danger);
  width: 100%;
}
</style>
