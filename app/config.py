"""服务端安全与处理上限配置。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """图像上传与限流相关硬上限。"""

    # 单文件最大字节数（10MB）
    max_upload_bytes: int = 10 * 1024 * 1024
    # 解码后最大像素数（25MP），防解压炸弹
    max_pixels: int = 25_000_000
    # 最长边硬上限，避免离谱输出
    max_output_edge: int = 8192
    # 每 IP 每分钟请求上限
    rate_limit_per_minute: int = 60
    # 质量参数范围
    quality_min: int = 1
    quality_max: int = 100
    # 拼接：最多张数
    max_stitch_files: int = 20
    # 拼接边距 / 间距上限（像素）
    max_margin: int = 512
    # 颜色提取：返回色数上下限
    colors_min: int = 2
    colors_max: int = 16
    # 二维码内容长度上限
    max_qr_content_len: int = 2000
    # 条码内容长度上限
    max_barcode_content_len: int = 200
    # 九宫格行列上下限
    grid_min: int = 2
    grid_max: int = 6


settings = Settings()