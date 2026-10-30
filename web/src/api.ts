/** 调用后端处理接口并触发浏览器下载。 */

export async function postProcess(
  path: string,
  file: File,
  fields: Record<string, string>,
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string }> {
  const body = new FormData()
  body.append('file', file)
  for (const [k, v] of Object.entries(fields)) {
    if (v !== undefined && v !== null) body.append(k, v)
  }

  const res = await fetch(path, { method: 'POST', body, signal })
  if (!res.ok) {
    let message = '处理失败'
    try {
      const data = await res.json()
      if (data?.message) message = data.message
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }

  const blob = await res.blob()
  const cd = res.headers.get('Content-Disposition') || ''
  let filename = 'download'
  const m = /filename\*=UTF-8''([^;]+)|filename="([^"]+)"/i.exec(cd)
  if (m) {
    filename = decodeURIComponent(m[1] || m[2])
  }
  return { blob, filename }
}

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
