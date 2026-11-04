/** 调用后端处理接口并触发浏览器下载。 */

function parseFilename(cd: string | null, fallback = 'download'): string {
  if (!cd) return fallback
  const m = /filename\*=UTF-8''([^;]+)|filename="([^"]+)"/i.exec(cd)
  if (m) return decodeURIComponent(m[1] || m[2])
  return fallback
}

async function raiseIfNotOk(res: Response) {
  if (res.ok) return
  let message = '处理失败'
  try {
    const data = await res.json()
    if (data?.message) message = data.message
  } catch {
    /* ignore */
  }
  throw new Error(message)
}

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
  await raiseIfNotOk(res)

  const blob = await res.blob()
  return { blob, filename: parseFilename(res.headers.get('Content-Disposition')) }
}

/** 多文件上传（字段名 files）。 */
export async function postProcessFiles(
  path: string,
  files: File[],
  fields: Record<string, string>,
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string }> {
  const body = new FormData()
  for (const f of files) body.append('files', f)
  for (const [k, v] of Object.entries(fields)) {
    if (v !== undefined && v !== null) body.append(k, v)
  }

  const res = await fetch(path, { method: 'POST', body, signal })
  await raiseIfNotOk(res)

  const blob = await res.blob()
  return { blob, filename: parseFilename(res.headers.get('Content-Disposition')) }
}

/** 仅表单字段（无文件），用于二维码 / 条码生成。 */
export async function postForm(
  path: string,
  fields: Record<string, string>,
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string }> {
  const body = new FormData()
  for (const [k, v] of Object.entries(fields)) {
    if (v !== undefined && v !== null) body.append(k, v)
  }

  const res = await fetch(path, { method: 'POST', body, signal })
  await raiseIfNotOk(res)

  const blob = await res.blob()
  return { blob, filename: parseFilename(res.headers.get('Content-Disposition')) }
}

/** JSON 响应接口（如颜色提取）。 */
export async function postJson<T>(
  path: string,
  file: File | null,
  fields: Record<string, string>,
  signal?: AbortSignal,
): Promise<T> {
  const body = new FormData()
  if (file) body.append('file', file)
  for (const [k, v] of Object.entries(fields)) {
    if (v !== undefined && v !== null) body.append(k, v)
  }

  const res = await fetch(path, { method: 'POST', body, signal })
  await raiseIfNotOk(res)
  return (await res.json()) as T
}

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
