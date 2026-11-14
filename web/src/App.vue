<script setup lang="ts">
import { computed, h, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  AppleOutlined,
  AppstoreOutlined,
  BarcodeOutlined,
  BgColorsOutlined,
  CameraOutlined,
  CompressOutlined,
  CopyOutlined,
  ColumnWidthOutlined,
  GithubOutlined,
  MenuOutlined,
  PictureOutlined,
  QrcodeOutlined,
  ScanOutlined,
  SwapOutlined,
  TableOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import FilePicker from './components/FilePicker.vue'
import FormRow from './components/FormRow.vue'
import MultiFilePicker from './components/MultiFilePicker.vue'
import PanelShell from './components/PanelShell.vue'
import ResultPreview from './components/ResultPreview.vue'
import { postForm, postJson, postProcess, postProcessFiles } from './api'
import type { ScanKind } from './scan'

type Tab =
  | 'favicon'
  | 'compress'
  | 'resize'
  | 'convert'
  | 'stitch'
  | 'barcode'
  | 'qrcode'
  | 'colors'
  | 'grid'
  | 'scan_qr'
  | 'scan_barcode'

const tab = ref<Tab>('favicon')
const file = ref<File | null>(null)
const files = ref<File[]>([])
const loading = ref(false)
const error = ref('')
const resultBlob = ref<Blob | null>(null)
const resultName = ref('')
const sidebarOpen = ref(false)
const isMobile = ref(false)
let abort: AbortController | null = null

function clearResult() {
  resultBlob.value = null
  resultName.value = ''
}

function setResult(blob: Blob, filename: string) {
  resultBlob.value = blob
  resultName.value = filename
}

const navGroups: {
  title: string
  items: { id: Tab; label: string; icon: any }[]
}[] = [
  {
    title: '基础处理',
    items: [
      { id: 'favicon', label: 'Favicon', icon: AppleOutlined },
      { id: 'compress', label: '压缩', icon: CompressOutlined },
      { id: 'resize', label: '缩放', icon: ColumnWidthOutlined },
      { id: 'convert', label: '格式转换', icon: SwapOutlined },
    ],
  },
  {
    title: '图像组合',
    items: [
      { id: 'stitch', label: '拼接', icon: AppstoreOutlined },
      { id: 'grid', label: '九宫格', icon: TableOutlined },
      { id: 'colors', label: '取色', icon: BgColorsOutlined },
    ],
  },
  {
    title: '码生成',
    items: [
      { id: 'qrcode', label: '二维码', icon: QrcodeOutlined },
      { id: 'barcode', label: '条形码', icon: BarcodeOutlined },
    ],
  },
  {
    title: '码扫描',
    items: [
      { id: 'scan_qr', label: '扫二维码', icon: ScanOutlined },
      { id: 'scan_barcode', label: '扫条形码', icon: CameraOutlined },
    ],
  },
]

const selectedKeys = computed(() => [tab.value])

const themeConfig = {
  token: {
    colorPrimary: '#1677ff',
    colorInfo: '#1677ff',
    colorLink: '#1677ff',
    borderRadius: 0,
    borderRadiusLG: 0,
    borderRadiusSM: 0,
    borderRadiusXS: 0,
    fontFamily: '"IBM Plex Sans", "Noto Sans SC", "Segoe UI", sans-serif',
    colorBgLayout: '#f0f2f5',
    colorBgContainer: '#ffffff',
  },
}

function selectTab(id: Tab) {
  tab.value = id
  sidebarOpen.value = false
}

function onMenuClick(info: { key: string | number }) {
  selectTab(String(info.key) as Tab)
}

function checkMobile() {
  isMobile.value = window.matchMedia('(max-width: 860px)').matches
  if (!isMobile.value) sidebarOpen.value = false
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

// 压缩
const cQuality = ref(85)
const cFormat = ref('')
const cMaxEdge = ref<number | null>(null)
const cKeepExif = ref('false')

// 缩放
const rMode = ref<'max_edge' | 'width_height'>('max_edge')
const rMaxEdge = ref(1280)
const rWidth = ref(800)
const rHeight = ref(600)
const rFit = ref('contain')
const rFormat = ref('')
const rQuality = ref(85)

// 转换
const vFormat = ref('webp')
const vQuality = ref(85)
const vMaxEdge = ref<number | null>(null)

// 拼接
const sDirection = ref('horizontal')
const sSort = ref('original')
const sMargin = ref(0)
const sGap = ref(8)
const sAlign = ref('center')
const sBg = ref('#ffffff')
const sFormat = ref('png')
const sQuality = ref(90)

// 二维码生成
const qContent = ref('')
const qBox = ref(10)
const qBorder = ref(2)
const qEc = ref('M')
const qFormat = ref('png')

// 条码生成
const bContent = ref('')
const bType = ref('code128')
const bWriteText = ref('true')
const bFormat = ref('png')

// 取色
const colorCount = ref(6)
const palette = ref<{ hex: string; rgb: number[]; ratio: number }[]>([])
const copied = ref('')

// 九宫格
const gRows = ref(3)
const gCols = ref(3)
const gFormat = ref('png')

// 扫描
const scanText = ref('')
const scanMode = ref<'file' | 'camera'>('file')
const cameraOn = ref(false)
const videoEl = ref<HTMLVideoElement | null>(null)
let mediaStream: MediaStream | null = null
let scanTimer: number | null = null
let scanBusy = false

const formatOptions = [
  { value: 'webp', label: 'WebP' },
  { value: 'jpeg', label: 'JPEG' },
  { value: 'png', label: 'PNG' },
]

const formatOptionsWithSame = [{ value: '', label: '与源相同' }, ...formatOptions]

const needsFile = computed(() =>
  ['favicon', 'compress', 'resize', 'convert', 'colors', 'grid', 'scan_qr', 'scan_barcode'].includes(
    tab.value,
  ),
)

const canSubmit = computed(() => {
  if (tab.value === 'stitch') return files.value.length >= 2
  if (tab.value === 'qrcode') return qContent.value.trim().length > 0
  if (tab.value === 'barcode') return bContent.value.trim().length > 0
  if (tab.value === 'scan_qr' || tab.value === 'scan_barcode') {
    if (scanMode.value === 'camera') return false
    return !!file.value
  }
  return !!file.value
})

const submitLabel = computed(() => {
  if (tab.value === 'colors') return '提取主色'
  if (tab.value === 'scan_qr' || tab.value === 'scan_barcode') return '识别图片'
  if (tab.value === 'qrcode' || tab.value === 'barcode') return '生成预览'
  if (tab.value === 'grid') return '裁切预览'
  if (tab.value === 'stitch') return '拼接预览'
  return '生成预览'
})

const showSubmit = computed(() => {
  if ((tab.value === 'scan_qr' || tab.value === 'scan_barcode') && scanMode.value === 'camera') {
    return false
  }
  return true
})

const title = computed(() => {
  const map: Record<Tab, string> = {
    favicon: 'Favicon 包',
    compress: '图像压缩',
    resize: '图像缩放',
    convert: '格式转换',
    stitch: '图片拼接',
    barcode: '条形码生成',
    qrcode: '二维码生成',
    colors: '颜色提取',
    grid: '九宫格裁剪',
    scan_qr: '二维码扫描',
    scan_barcode: '条形码扫描',
  }
  return map[tab.value]
})

const desc = computed(() => {
  const map: Record<Tab, string> = {
    favicon: '生成 ICO / 多尺寸 PNG / apple-touch-icon / webmanifest，打包 ZIP 下载。',
    compress: '调整质量与最长边，可选输出 WebP / JPEG / PNG。',
    resize: '按最长边或目标宽高缩放，支持 contain / cover / stretch。',
    convert: '在 WebP / JPEG / PNG 之间转换；JPEG 透明区域铺白底。',
    stitch: '多图水平 / 垂直拼接，可配置排序、边距、间距、对齐与背景色。',
    barcode: '输入内容生成条形码（Code128 / Code39 / EAN / UPC 等）。',
    qrcode: '输入文本或链接生成二维码，可调容错级别与边框。',
    colors: '从图片中提取主色，点击色块复制 HEX。',
    grid: '将图片按网格裁切（默认 3×3 九宫格），打包 ZIP 下载。',
    scan_qr: '上传图片或摄像头识别二维码，结果仅在浏览器本地解码。',
    scan_barcode: '上传图片或摄像头识别条形码，结果仅在浏览器本地解码。',
  }
  return map[tab.value]
})

watch(tab, async () => {
  error.value = ''
  palette.value = []
  scanText.value = ''
  copied.value = ''
  clearResult()
  await stopCamera()
})

watch(file, () => {
  clearResult()
  palette.value = []
  scanText.value = ''
})

watch(files, () => clearResult(), { deep: true })

watch(
  [
    cQuality,
    cFormat,
    cMaxEdge,
    cKeepExif,
    rMode,
    rMaxEdge,
    rWidth,
    rHeight,
    rFit,
    rFormat,
    rQuality,
    vFormat,
    vQuality,
    vMaxEdge,
    sDirection,
    sSort,
    sMargin,
    sGap,
    sAlign,
    sBg,
    sFormat,
    sQuality,
    qContent,
    qBox,
    qBorder,
    qEc,
    qFormat,
    bContent,
    bType,
    bWriteText,
    bFormat,
    gRows,
    gCols,
    gFormat,
    colorCount,
  ],
  () => {
    clearResult()
  },
)

watch(scanMode, async () => {
  scanText.value = ''
  error.value = ''
  if (scanMode.value !== 'camera') await stopCamera()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
  void stopCamera()
  clearResult()
})

function edgeStr(v: number | null | undefined) {
  return v == null || Number.isNaN(v) ? '' : String(v)
}

async function onSubmit() {
  error.value = ''
  clearResult()
  loading.value = true
  abort?.abort()
  abort = new AbortController()
  try {
    if (tab.value === 'favicon') {
      const { blob, filename } = await postProcess('/api/favicon', file.value!, {}, abort.signal)
      setResult(blob, filename)
      return
    }
    if (tab.value === 'compress') {
      const { blob, filename } = await postProcess(
        '/api/compress',
        file.value!,
        {
          quality: String(cQuality.value),
          format: cFormat.value,
          max_edge: edgeStr(cMaxEdge.value),
          keep_exif: cKeepExif.value,
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'resize') {
      const { blob, filename } = await postProcess(
        '/api/resize',
        file.value!,
        {
          mode: rMode.value,
          max_edge: String(rMaxEdge.value),
          width: String(rWidth.value),
          height: String(rHeight.value),
          fit: rFit.value,
          format: rFormat.value,
          quality: String(rQuality.value),
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'convert') {
      const { blob, filename } = await postProcess(
        '/api/convert',
        file.value!,
        {
          format: vFormat.value,
          quality: String(vQuality.value),
          max_edge: edgeStr(vMaxEdge.value),
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'stitch') {
      const { blob, filename } = await postProcessFiles(
        '/api/stitch',
        files.value,
        {
          direction: sDirection.value,
          sort: sSort.value,
          margin: String(sMargin.value),
          gap: String(sGap.value),
          align: sAlign.value,
          bgcolor: sBg.value,
          format: sFormat.value,
          quality: String(sQuality.value),
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'qrcode') {
      const { blob, filename } = await postForm(
        '/api/qrcode',
        {
          content: qContent.value,
          box_size: String(qBox.value),
          border: String(qBorder.value),
          error_correction: qEc.value,
          format: qFormat.value,
          quality: '90',
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'barcode') {
      const { blob, filename } = await postForm(
        '/api/barcode',
        {
          content: bContent.value,
          barcode_type: bType.value,
          write_text: bWriteText.value,
          format: bFormat.value,
          quality: '90',
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'colors') {
      const data = await postJson<{ colors: typeof palette.value }>(
        '/api/colors',
        file.value,
        { count: String(colorCount.value) },
        abort.signal,
      )
      palette.value = data.colors || []
      return
    }
    if (tab.value === 'grid') {
      const { blob, filename } = await postProcess(
        '/api/grid',
        file.value!,
        {
          rows: String(gRows.value),
          cols: String(gCols.value),
          format: gFormat.value,
          quality: '90',
        },
        abort.signal,
      )
      setResult(blob, filename)
      return
    }
    if (tab.value === 'scan_qr' || tab.value === 'scan_barcode') {
      if (!file.value) return
      const kind: ScanKind = tab.value === 'scan_qr' ? 'qr' : 'barcode'
      const { decodeFromFile } = await import('./scan')
      scanText.value = await decodeFromFile(file.value, kind)
      return
    }
  } catch (e: any) {
    if (e?.name === 'AbortError') return
    error.value = e?.message || '处理失败'
    if (tab.value === 'scan_qr' || tab.value === 'scan_barcode') {
      error.value = e?.message || '未识别到有效码，请换一张更清晰的图'
      scanText.value = ''
    }
  } finally {
    loading.value = false
  }
}

async function copyHex(hex: string) {
  try {
    await navigator.clipboard.writeText(hex)
    copied.value = hex
    message.success(`已复制 ${hex}`)
    setTimeout(() => {
      if (copied.value === hex) copied.value = ''
    }, 1500)
  } catch {
    error.value = '复制失败，请手动选择'
  }
}

async function copyScan() {
  if (!scanText.value) return
  try {
    await navigator.clipboard.writeText(scanText.value)
    copied.value = 'scan'
    message.success('已复制识别结果')
    setTimeout(() => {
      if (copied.value === 'scan') copied.value = ''
    }, 1500)
  } catch {
    error.value = '复制失败'
  }
}

async function startCamera() {
  error.value = ''
  scanText.value = ''
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
      audio: false,
    })
    cameraOn.value = true
    await new Promise((r) => requestAnimationFrame(() => r(null)))
    if (videoEl.value) {
      videoEl.value.srcObject = mediaStream
      await videoEl.value.play()
    }
    const kind: ScanKind = tab.value === 'scan_qr' ? 'qr' : 'barcode'
    const { decodeFromVideo } = await import('./scan')
    scanTimer = window.setInterval(async () => {
      if (!videoEl.value || scanText.value || scanBusy) return
      scanBusy = true
      try {
        const text = await decodeFromVideo(videoEl.value, kind)
        if (text) {
          scanText.value = text
          await stopCamera()
        }
      } finally {
        scanBusy = false
      }
    }, 600)
  } catch {
    error.value = '无法打开摄像头，请检查权限或改用上传图片'
    cameraOn.value = false
  }
}

async function stopCamera() {
  if (scanTimer != null) {
    clearInterval(scanTimer)
    scanTimer = null
  }
  if (mediaStream) {
    for (const t of mediaStream.getTracks()) t.stop()
    mediaStream = null
  }
  if (videoEl.value) videoEl.value.srcObject = null
  cameraOn.value = false
}
</script>

<template>
  <a-config-provider :theme="themeConfig">
    <a-layout class="app-layout">
      <a-layout-sider
        v-if="!isMobile"
        width="240"
        theme="light"
        class="app-sider"
      >
        <div class="brand">
          <span class="mark" aria-hidden="true" />
          <div>
            <div class="brand-title">imgkit</div>
            <div class="brand-tag">即时 · 不落盘</div>
          </div>
        </div>
        <div class="sider-scroll">
          <a-menu
            mode="inline"
            :selected-keys="selectedKeys"
            :items="
              navGroups.map((g) => ({
                type: 'group',
                label: g.title,
                children: g.items.map((item) => ({
                  key: item.id,
                  label: item.label,
                  icon: () => h(item.icon),
                })),
              }))
            "
            @click="onMenuClick"
          />
        </div>
      </a-layout-sider>

      <a-drawer
        v-model:open="sidebarOpen"
        placement="left"
        :width="260"
        :body-style="{ padding: 0 }"
        title="功能导航"
      >
        <div class="app-sider drawer-sider">
          <a-menu
            mode="inline"
            :selected-keys="selectedKeys"
            :items="
              navGroups.map((g) => ({
                type: 'group',
                label: g.title,
                children: g.items.map((item) => ({
                  key: item.id,
                  label: item.label,
                  icon: () => h(item.icon),
                })),
              }))
            "
            @click="onMenuClick"
          />
        </div>
      </a-drawer>

      <a-layout>
        <a-layout-header class="topbar">
          <div class="topbar-left">
            <a-button
              v-if="isMobile"
              type="text"
              class="menu-btn"
              @click="sidebarOpen = true"
            >
              <template #icon><MenuOutlined /></template>
            </a-button>
            <div class="page-title">{{ title }}</div>
          </div>
          <a
            class="github-link"
            href="https://github.com/jiangfolio/imgkit"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub 仓库"
            title="GitHub"
          >
            <GithubOutlined />
          </a>
        </a-layout-header>

        <a-layout-content class="content">
          <PanelShell
            :title="title"
            :desc="desc"
            :loading="loading"
            :error="error"
            :can-submit="canSubmit"
            :submit-label="submitLabel"
            :show-submit="showSubmit"
            :show-head="false"
            @submit="onSubmit"
          >
            <FilePicker
              v-if="needsFile && !((tab === 'scan_qr' || tab === 'scan_barcode') && scanMode === 'camera')"
              v-model="file"
            />
            <MultiFilePicker v-else-if="tab === 'stitch'" v-model="files" />

            <a-form layout="vertical" class="tool-form">
              <div v-if="tab === 'compress'" class="form-grid">
                <FormRow label="质量" hint="JPEG / WebP 1–100；PNG 映射为压缩级别">
                  <a-input-number v-model:value="cQuality" :min="1" :max="100" />
                </FormRow>
                <FormRow label="输出格式">
                  <a-select v-model:value="cFormat" :options="formatOptionsWithSame" />
                </FormRow>
                <FormRow label="最长边" hint="可选；超出则等比缩小">
                  <a-input-number
                    v-model:value="cMaxEdge"
                    :min="1"
                    :max="8192"
                    placeholder="不限制"
                  />
                </FormRow>
                <FormRow label="保留 EXIF">
                  <a-select
                    v-model:value="cKeepExif"
                    :options="[
                      { value: 'false', label: '否（推荐）' },
                      { value: 'true', label: '是' },
                    ]"
                  />
                </FormRow>
              </div>

              <div v-else-if="tab === 'resize'" class="form-grid">
                <FormRow label="模式">
                  <a-select
                    v-model:value="rMode"
                    :options="[
                      { value: 'max_edge', label: '最长边' },
                      { value: 'width_height', label: '宽 × 高' },
                    ]"
                  />
                </FormRow>
                <FormRow v-if="rMode === 'max_edge'" label="最长边">
                  <a-input-number v-model:value="rMaxEdge" :min="1" :max="8192" />
                </FormRow>
                <template v-else>
                  <FormRow label="宽度">
                    <a-input-number v-model:value="rWidth" :min="1" :max="8192" />
                  </FormRow>
                  <FormRow label="高度">
                    <a-input-number v-model:value="rHeight" :min="1" :max="8192" />
                  </FormRow>
                  <FormRow label="适应">
                    <a-select
                      v-model:value="rFit"
                      :options="[
                        { value: 'contain', label: 'contain 适应' },
                        { value: 'cover', label: 'cover 裁切' },
                        { value: 'stretch', label: 'stretch 拉伸' },
                      ]"
                    />
                  </FormRow>
                </template>
                <FormRow label="输出格式">
                  <a-select v-model:value="rFormat" :options="formatOptionsWithSame" />
                </FormRow>
                <FormRow label="质量">
                  <a-input-number v-model:value="rQuality" :min="1" :max="100" />
                </FormRow>
              </div>

              <div v-else-if="tab === 'convert'" class="form-grid">
                <FormRow label="目标格式">
                  <a-select v-model:value="vFormat" :options="formatOptions" />
                </FormRow>
                <FormRow label="质量">
                  <a-input-number v-model:value="vQuality" :min="1" :max="100" />
                </FormRow>
                <FormRow label="最长边" hint="可选">
                  <a-input-number
                    v-model:value="vMaxEdge"
                    :min="1"
                    :max="8192"
                    placeholder="不限制"
                  />
                </FormRow>
              </div>

              <div v-else-if="tab === 'stitch'" class="form-grid">
                <FormRow label="方向">
                  <a-select
                    v-model:value="sDirection"
                    :options="[
                      { value: 'horizontal', label: '水平' },
                      { value: 'vertical', label: '垂直' },
                    ]"
                  />
                </FormRow>
                <FormRow label="排序" hint="也可在列表中手动调整顺序">
                  <a-select
                    v-model:value="sSort"
                    :options="[
                      { value: 'original', label: '上传顺序' },
                      { value: 'name_asc', label: '文件名升序' },
                      { value: 'name_desc', label: '文件名降序' },
                      { value: 'size_asc', label: '体积升序' },
                      { value: 'size_desc', label: '体积降序' },
                    ]"
                  />
                </FormRow>
                <FormRow label="外边距">
                  <a-input-number v-model:value="sMargin" :min="0" :max="512" />
                </FormRow>
                <FormRow label="间距">
                  <a-input-number v-model:value="sGap" :min="0" :max="512" />
                </FormRow>
                <FormRow label="对齐">
                  <a-select
                    v-model:value="sAlign"
                    :options="[
                      { value: 'start', label: '靠前' },
                      { value: 'center', label: '居中' },
                      { value: 'end', label: '靠后' },
                    ]"
                  />
                </FormRow>
                <FormRow label="背景色" hint="#RGB / #RRGGBB / #RRGGBBAA">
                  <a-input v-model:value="sBg" placeholder="#ffffff" />
                </FormRow>
                <FormRow label="输出格式">
                  <a-select v-model:value="sFormat" :options="formatOptions" />
                </FormRow>
                <FormRow label="质量">
                  <a-input-number v-model:value="sQuality" :min="1" :max="100" />
                </FormRow>
              </div>

              <div v-else-if="tab === 'qrcode'" class="form-grid">
                <FormRow label="内容" full>
                  <a-textarea v-model:value="qContent" placeholder="文本或 URL" :rows="3" />
                </FormRow>
                <FormRow label="模块大小">
                  <a-input-number v-model:value="qBox" :min="2" :max="40" />
                </FormRow>
                <FormRow label="边框">
                  <a-input-number v-model:value="qBorder" :min="0" :max="16" />
                </FormRow>
                <FormRow label="容错">
                  <a-select
                    v-model:value="qEc"
                    :options="[
                      { value: 'L', label: 'L（约 7%）' },
                      { value: 'M', label: 'M（约 15%）' },
                      { value: 'Q', label: 'Q（约 25%）' },
                      { value: 'H', label: 'H（约 30%）' },
                    ]"
                  />
                </FormRow>
                <FormRow label="输出格式">
                  <a-select v-model:value="qFormat" :options="formatOptions" />
                </FormRow>
              </div>

              <div v-else-if="tab === 'barcode'" class="form-grid">
                <FormRow label="内容" full>
                  <a-textarea v-model:value="bContent" placeholder="条码内容" :rows="2" />
                </FormRow>
                <FormRow label="类型" hint="EAN / UPC / ISBN 需符合位数与校验规则">
                  <a-select
                    v-model:value="bType"
                    :options="[
                      { value: 'code128', label: 'Code128' },
                      { value: 'code39', label: 'Code39' },
                      { value: 'ean13', label: 'EAN-13' },
                      { value: 'ean8', label: 'EAN-8' },
                      { value: 'upc', label: 'UPC-A' },
                      { value: 'isbn13', label: 'ISBN-13' },
                    ]"
                  />
                </FormRow>
                <FormRow label="显示文字">
                  <a-select
                    v-model:value="bWriteText"
                    :options="[
                      { value: 'true', label: '是' },
                      { value: 'false', label: '否' },
                    ]"
                  />
                </FormRow>
                <FormRow label="输出格式">
                  <a-select v-model:value="bFormat" :options="formatOptions" />
                </FormRow>
              </div>

              <div v-else-if="tab === 'colors'" class="form-grid">
                <FormRow label="色数">
                  <a-input-number v-model:value="colorCount" :min="2" :max="16" />
                </FormRow>
              </div>

              <template v-else-if="tab === 'grid'">
                <div class="form-grid">
                  <FormRow label="行数">
                    <a-input-number v-model:value="gRows" :min="2" :max="6" />
                  </FormRow>
                  <FormRow label="列数">
                    <a-input-number v-model:value="gCols" :min="2" :max="6" />
                  </FormRow>
                  <FormRow label="输出格式">
                    <a-select v-model:value="gFormat" :options="formatOptions" />
                  </FormRow>
                </div>
                <a-typography-paragraph type="secondary" class="note">
                  默认 3×3 九宫格；余数像素归入右下侧格子。
                </a-typography-paragraph>
              </template>

              <div v-else-if="tab === 'scan_qr' || tab === 'scan_barcode'" class="form-grid">
                <FormRow label="方式">
                  <a-select
                    v-model:value="scanMode"
                    :options="[
                      { value: 'file', label: '上传图片' },
                      { value: 'camera', label: '摄像头' },
                    ]"
                  />
                </FormRow>
              </div>

              <a-typography-paragraph v-else-if="tab === 'favicon'" type="secondary" class="note">
                上传任意图片，生成多尺寸图标 ZIP，可先预览再下载。
              </a-typography-paragraph>
            </a-form>

            <div v-if="tab === 'colors' && palette.length" class="palette">
              <a-tooltip
                v-for="c in palette"
                :key="c.hex"
                :title="`${c.hex} · ${(c.ratio * 100).toFixed(1)}%`"
              >
                <a-button class="swatch" @click="copyHex(c.hex)">
                  <span class="chip" :style="{ background: c.hex }" />
                  <span class="hex">{{ c.hex }}</span>
                  <span class="ratio">{{ (c.ratio * 100).toFixed(1) }}%</span>
                </a-button>
              </a-tooltip>
            </div>

            <div v-if="(tab === 'scan_qr' || tab === 'scan_barcode') && scanMode === 'camera'" class="camera">
              <video ref="videoEl" class="preview-video" playsinline muted />
              <a-space>
                <a-button v-if="!cameraOn" type="primary" @click="startCamera">
                  <template #icon><CameraOutlined /></template>
                  打开摄像头
                </a-button>
                <a-button v-else @click="stopCamera">关闭摄像头</a-button>
              </a-space>
              <a-typography-text type="secondary">
                对准码后自动识别；识别成功后会自动关闭摄像头。
              </a-typography-text>
            </div>

            <a-card v-if="scanText" size="small" title="识别结果" class="scan-result">
              <template #extra>
                <a-button type="link" size="small" @click="copyScan">
                  <template #icon><CopyOutlined /></template>
                  {{ copied === 'scan' ? '已复制' : '复制结果' }}
                </a-button>
              </template>
              <pre>{{ scanText }}</pre>
            </a-card>

            <ResultPreview v-if="resultBlob" :blob="resultBlob" :filename="resultName" />
          </PanelShell>

          <div class="bottom">
            <PictureOutlined />
            单文件 ≤ 10MB · 像素 ≤ 25MP · 拒绝 SVG · 无登录无落盘
          </div>
        </a-layout-content>
      </a-layout>
    </a-layout>
  </a-config-provider>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  background: var(--bg);
}

.app-sider {
  background: var(--sidebar) !important;
  border-right: 1px solid var(--border);
  height: 100vh;
  position: sticky !important;
  top: 0;
  overflow: hidden !important;
}

.app-sider :deep(.ant-layout-sider-children) {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.drawer-sider {
  height: auto;
  border-right: 0;
  overflow: visible !important;
}

.drawer-sider :deep(.ant-layout-sider-children) {
  display: block;
  height: auto;
  overflow: visible;
}

.brand {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--sidebar);
  z-index: 1;
}

.sider-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0.65rem 0 0.75rem;
  background: var(--sidebar);
}

.sider-scroll :deep(.ant-menu) {
  background: transparent;
  border-inline-end: none !important;
  padding-inline: 0.35rem;
}

.sider-scroll :deep(.ant-menu-item-group-title) {
  padding: 0.5rem 0.85rem 0.35rem;
  font-size: 0.72rem;
  line-height: 1.3;
}

.sider-scroll :deep(.ant-menu-item) {
  margin-inline: 0.35rem;
  width: auto;
}

.mark {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  background: var(--accent);
  border-radius: 0;
}

.brand-title {
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.15;
}

.brand-tag {
  margin-top: 0.1rem;
  color: var(--muted);
  font-size: 0.68rem;
  line-height: 1.2;
}

.topbar {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between;
  gap: 0.75rem;
  height: 56px !important;
  line-height: 1 !important;
  padding: 0 1.25rem !important;
  background: var(--surface) !important;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 5;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.menu-btn {
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0 !important;
}

.page-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text);
  line-height: 1.2;
  margin: 0;
}

.github-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--text);
  font-size: 1.25rem;
  flex-shrink: 0;
  transition: color 0.15s;
}

.github-link:hover {
  color: var(--accent);
}

.content {
  padding: 1.25rem;
  width: 100%;
}

.tool-form {
  margin-top: 0.5rem;
}

/* 按可用宽度自动排布：短项均分剩余空间，长项可 full 占满整行 */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr));
  gap: 8px 16px;
  align-items: start;
}

.note {
  margin: 0 0 0.5rem !important;
}

.bottom {
  margin-top: 1.25rem;
  color: var(--muted);
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.palette {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.5rem 0 0.75rem;
}

.swatch {
  height: auto !important;
  padding: 0.4rem 0.5rem !important;
  display: flex !important;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  min-width: 4.5rem;
}

.chip {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0;
  border: 1px solid var(--border);
}

.hex {
  font-size: 0.75rem;
  font-family: ui-monospace, monospace;
}

.ratio {
  font-size: 0.7rem;
  color: var(--muted);
}

.camera {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.preview-video {
  width: 100%;
  max-height: 320px;
  background: #111;
  border-radius: 0;
  border: 1px solid var(--border);
  object-fit: cover;
}

.scan-result {
  margin-top: 0.75rem;
}

.scan-result pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 0.95rem;
}

@media (max-width: 860px) {
  .content {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .content {
    padding: 0.75rem;
  }
}
</style>
