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


settings = Settings()