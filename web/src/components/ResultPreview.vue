<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { triggerDownload } from '../api'

const props = defineProps<{
  blob: Blob | null
  filename: string
}>()

const previewUrl = ref('')
const zipItems = ref<{ name: string; url: string }[]>([])
const busy = ref(false)

const kind = computed(() => {
  if (!props.blob) return 'none'
  const t = props.blob.type || ''
  if (t.startsWith('image/')) return 'image'
  if (t === 'application/zip' || props.filename.endsWith('.zip')) return 'zip'
  return 'file'
})

const sizeLabel = computed(() => {
  if (!props.blob) return ''
  const kb = props.blob.size / 1024
  return kb >= 1024 ? `${(kb / 1024).toFixed(2)} MB` : `${kb.toFixed(1)} KB`
})

function revokeAll() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
  for (const item of zipItems.value) URL.revokeObjectURL(item.url)
  zipItems.value = []
}

watch(
  () => props.blob,
  async (blob) => {
    revokeAll()
    if (!blob) return

    if (kind.value === 'image') {
      previewUrl.value = URL.createObjectURL(blob)
      return
    }

    if (kind.value === 'zip') {
      busy.value = true
      try {
        const { default: JSZip } = await import('jszip')
        const zip = await JSZip.loadAsync(blob)
        const items: { name: string; url: string }[] = []
        const names = Object.keys(zip.files).sort()
        for (const name of names) {
          const entry = zip.files[name]
          if (!entry || entry.dir) continue
          if (!/\.(png|jpe?g|webp|ico|gif)$/i.test(name)) continue
          const part = await entry.async('blob')
          const type = name.endsWith('.ico')
            ? 'image/x-icon'
            : part.type || 'image/png'
          items.push({
            name: name.split('/').pop() || name,
            url: URL.createObjectURL(new Blob([part], { type })),
          })
        }
        zipItems.value = items
      } catch {
        zipItems.value = []
      } finally {
        busy.value = false
      }
    }
  },
  { immediate: true },
)

onBeforeUnmount(revokeAll)

function download() {
  if (!props.blob) return
  triggerDownload(props.blob, props.filename || 'download')
}
</script>

<template>
  <a-card v-if="blob" size="small" class="result" title="预览结果">
    <template #extra>
      <a-space>
        <a-typography-text type="secondary">{{ filename }} · {{ sizeLabel }}</a-typography-text>
        <a-button type="primary" size="small" @click="download">
          <template #icon><DownloadOutlined /></template>
          下载
        </a-button>
      </a-space>
    </template>

    <div v-if="kind === 'image'" class="image-wrap">
      <a-image :src="previewUrl" :alt="filename" :preview="true" />
    </div>

    <a-spin v-else-if="kind === 'zip'" :spinning="busy" tip="正在解析 ZIP…">
      <a-empty v-if="!busy && zipItems.length === 0" description="ZIP 已就绪，可直接下载" />
      <div v-else class="grid">
        <figure v-for="item in zipItems" :key="item.url" class="tile">
          <a-image :src="item.url" :alt="item.name" :width="72" :height="72" />
          <figcaption>{{ item.name }}</figcaption>
        </figure>
      </div>
    </a-spin>

    <a-typography-text v-else type="secondary">文件已就绪，点击下载保存。</a-typography-text>
  </a-card>
</template>

<style scoped>
.result {
  margin-top: 0.5rem;
}

.image-wrap {
  display: flex;
  justify-content: center;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 0;
  padding: 0.75rem;
}

.image-wrap :deep(.ant-image img) {
  max-height: 380px;
  object-fit: contain;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 0.6rem;
  min-height: 48px;
}

.tile {
  margin: 0;
  border: 1px solid var(--border);
  border-radius: 0;
  background: var(--bg);
  padding: 0.4rem;
  text-align: center;
}

.tile :deep(.ant-image) {
  display: block;
  margin: 0 auto;
}

.tile :deep(.ant-image img) {
  object-fit: contain;
}

.tile figcaption {
  margin-top: 0.3rem;
  font-size: 0.68rem;
  color: var(--muted);
  word-break: break-all;
  line-height: 1.25;
}
</style>
