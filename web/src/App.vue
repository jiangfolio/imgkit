<script setup lang="ts">
import { computed, ref } from 'vue'
import FilePicker from './components/FilePicker.vue'
import FormRow from './components/FormRow.vue'
import PanelShell from './components/PanelShell.vue'
import { postProcess, triggerDownload } from './api'

type Tab = 'favicon' | 'compress' | 'resize' | 'convert'

const tab = ref<Tab>('favicon')
const file = ref<File | null>(null)
const loading = ref(false)
const error = ref('')
let abort: AbortController | null = null

const tabs: { id: Tab; label: string }[] = [
  { id: 'favicon', label: 'Favicon' },
  { id: 'compress', label: '压缩' },
  { id: 'resize', label: '缩放' },
  { id: 'convert', label: '格式转换' },
]

// 压缩
const cQuality = ref(85)
const cFormat = ref('')
const cMaxEdge = ref('')
const cKeepExif = ref('false')

// 缩放
const rMode = ref<'max_edge' | 'width_height'>('max_edge')
const rMaxEdge = ref('1280')
const rWidth = ref('800')
const rHeight = ref('600')
const rFit = ref('contain')
const rFormat = ref('')
const rQuality = ref(85)

// 转换
const vFormat = ref('webp')
const vQuality = ref(85)
const vMaxEdge = ref('')

const canSubmit = computed(() => !!file.value)

async function run(path: string, fields: Record<string, string>) {
  if (!file.value) return
  error.value = ''
  loading.value = true
  abort?.abort()
  abort = new AbortController()
  try {
    const { blob, filename } = await postProcess(path, file.value, fields, abort.signal)
    triggerDownload(blob, filename)
  } catch (e: any) {
    if (e?.name === 'AbortError') return
    error.value = e?.message || '处理失败'
  } finally {
    loading.value = false
  }
}

function onSubmit() {
  if (tab.value === 'favicon') {
    run('/api/favicon', {})
    return
  }
  if (tab.value === 'compress') {
    run('/api/compress', {
      quality: String(cQuality.value),
      format: cFormat.value,
      max_edge: cMaxEdge.value,
      keep_exif: cKeepExif.value,
    })
    return
  }
  if (tab.value === 'resize') {
    run('/api/resize', {
      mode: rMode.value,
      max_edge: rMaxEdge.value,
      width: rWidth.value,
      height: rHeight.value,
      fit: rFit.value,
      format: rFormat.value,
      quality: String(rQuality.value),
    })
    return
  }
  run('/api/convert', {
    format: vFormat.value,
    quality: String(vQuality.value),
    max_edge: vMaxEdge.value,
  })
}

const title = computed(() => {
  const map = {
    favicon: 'Favicon 包',
    compress: '图像压缩',
    resize: '图像缩放',
    convert: '格式转换',
  }
  return map[tab.value]
})

const desc = computed(() => {
  const map = {
    favicon: '生成 ICO / 多尺寸 PNG / apple-touch-icon / webmanifest，打包 ZIP 下载。',
    compress: '调整质量与最长边，可选输出 WebP / JPEG / PNG。',
    resize: '按最长边或目标宽高缩放，支持 contain / cover / stretch。',
    convert: '在 WebP / JPEG / PNG 之间转换；JPEG 透明区域铺白底。',
  }
  return map[tab.value]
})
</script>

<template>
  <div class="page">
    <header class="top">
      <div class="brand">
        <span class="mark" aria-hidden="true" />
        <div>
          <h1>imgkit</h1>
          <p class="tag">即时图像处理 · 不存储 · 处理完即丢</p>
        </div>
      </div>
    </header>

    <nav class="tabs" aria-label="功能">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        :class="{ active: tab === t.id }"
        @click="tab = t.id; error = ''"
      >
        {{ t.label }}
      </button>
    </nav>

    <PanelShell
      :title="title"
      :desc="desc"
      :loading="loading"
      :error="error"
      :can-submit="canSubmit"
      @submit="onSubmit"
    >
      <FilePicker v-model="file" />

      <template v-if="tab === 'compress'">
        <FormRow label="质量" hint="JPEG / WebP 1–100；PNG 映射为压缩级别">
          <input v-model.number="cQuality" type="number" min="1" max="100" />
        </FormRow>
        <FormRow label="输出格式">
          <select v-model="cFormat">
            <option value="">与源相同</option>
            <option value="webp">WebP</option>
            <option value="jpeg">JPEG</option>
            <option value="png">PNG</option>
          </select>
        </FormRow>
        <FormRow label="最长边" hint="可选；超出则等比缩小">
          <input v-model="cMaxEdge" type="number" min="1" max="8192" placeholder="不限制" />
        </FormRow>
        <FormRow label="保留 EXIF">
          <select v-model="cKeepExif">
            <option value="false">否（推荐）</option>
            <option value="true">是</option>
          </select>
        </FormRow>
      </template>

      <template v-else-if="tab === 'resize'">
        <FormRow label="模式">
          <select v-model="rMode">
            <option value="max_edge">最长边</option>
            <option value="width_height">宽 × 高</option>
          </select>
        </FormRow>
        <FormRow v-if="rMode === 'max_edge'" label="最长边">
          <input v-model="rMaxEdge" type="number" min="1" max="8192" />
        </FormRow>
        <template v-else>
          <FormRow label="宽度">
            <input v-model="rWidth" type="number" min="1" max="8192" />
          </FormRow>
          <FormRow label="高度">
            <input v-model="rHeight" type="number" min="1" max="8192" />
          </FormRow>
          <FormRow label="适应">
            <select v-model="rFit">
              <option value="contain">contain 适应</option>
              <option value="cover">cover 裁切</option>
              <option value="stretch">stretch 拉伸</option>
            </select>
          </FormRow>
        </template>
        <FormRow label="输出格式">
          <select v-model="rFormat">
            <option value="">与源相同</option>
            <option value="webp">WebP</option>
            <option value="jpeg">JPEG</option>
            <option value="png">PNG</option>
          </select>
        </FormRow>
        <FormRow label="质量">
          <input v-model.number="rQuality" type="number" min="1" max="100" />
        </FormRow>
      </template>

      <template v-else-if="tab === 'convert'">
        <FormRow label="目标格式">
          <select v-model="vFormat">
            <option value="webp">WebP</option>
            <option value="jpeg">JPEG</option>
            <option value="png">PNG</option>
          </select>
        </FormRow>
        <FormRow label="质量">
          <input v-model.number="vQuality" type="number" min="1" max="100" />
        </FormRow>
        <FormRow label="最长边" hint="可选">
          <input v-model="vMaxEdge" type="number" min="1" max="8192" placeholder="不限制" />
        </FormRow>
      </template>

      <p v-else class="note">上传任意图片，将下载包含多尺寸图标的 ZIP 包。</p>
    </PanelShell>

    <footer class="bottom">
      单文件 ≤ 10MB · 像素 ≤ 25MP · 拒绝 SVG · 无登录无落盘
    </footer>
  </div>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 1.5rem 1rem 2.5rem;
}

.top {
  margin-bottom: 1.25rem;
}

.brand {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.mark {
  width: 28px;
  height: 28px;
  background: var(--accent);
  border-radius: var(--radius-ctrl);
  border: 1px solid var(--ink);
  box-shadow: 8px 8px 0 0 var(--ink);
}

.brand h1 {
  margin: 0;
  font-size: 1.5rem;
  letter-spacing: 0.02em;
}

.tag {
  margin: 0.15rem 0 0;
  color: var(--muted);
  font-size: 0.85rem;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.tabs button {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-ctrl);
}

.tabs button.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.tabs button:hover:not(.active) {
  background: var(--accent-soft);
}

.note {
  margin: 0;
  color: var(--muted);
  font-size: 0.9rem;
}

.bottom {
  margin-top: 1.5rem;
  color: var(--muted);
  font-size: 0.8rem;
  text-align: center;
}
</style>
