/** 浏览器端二维码 / 条码解码（ZXing）。 */

import {
  BrowserMultiFormatReader,
  DecodeHintType,
  BarcodeFormat,
} from '@zxing/library'

const qrHints = new Map()
qrHints.set(DecodeHintType.POSSIBLE_FORMATS, [BarcodeFormat.QR_CODE])
qrHints.set(DecodeHintType.TRY_HARDER, true)

const barcodeHints = new Map()
barcodeHints.set(DecodeHintType.POSSIBLE_FORMATS, [
  BarcodeFormat.CODE_128,
  BarcodeFormat.CODE_39,
  BarcodeFormat.EAN_13,
  BarcodeFormat.EAN_8,
  BarcodeFormat.UPC_A,
  BarcodeFormat.UPC_E,
  BarcodeFormat.ITF,
  BarcodeFormat.CODABAR,
  BarcodeFormat.RSS_14,
  BarcodeFormat.RSS_EXPANDED,
])
barcodeHints.set(DecodeHintType.TRY_HARDER, true)

export type ScanKind = 'qr' | 'barcode'

function readerFor(kind: ScanKind) {
  return new BrowserMultiFormatReader(kind === 'qr' ? qrHints : barcodeHints)
}

/** 从图片 File 解码。 */
export async function decodeFromFile(file: File, kind: ScanKind): Promise<string> {
  const url = URL.createObjectURL(file)
  try {
    const reader = readerFor(kind)
    const result = await reader.decodeFromImageUrl(url)
    return result.getText()
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** 从 video 当前帧解码；失败返回 null。 */
export async function decodeFromVideo(
  video: HTMLVideoElement,
  kind: ScanKind,
): Promise<string | null> {
  if (!video.videoWidth || !video.videoHeight) return null
  try {
    const reader = readerFor(kind)
    const result = reader.decode(video)
    return result.getText()
  } catch {
    return null
  }
}
