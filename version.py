"""版本信息"""

__version__ = "1.0.0"
__title__ = "Card Battle Master"
__author__ = "Hiromichi123"
__release_date__ = "2024-12-02"

VERSION_INFO = {
    "version": __version__,
    "title": __title__,
    "author": __author__,
    "release_date": __release_date__,
    "build": "stable",
}

def get_version_string():
    """获取版本字符串"""
    return f"{__title__} v{__version__}"

def get_full_version_info():
    """获取完整版本信息"""
    return (
        f"{__title__}\n"
        f"Version: {__version__}\n"
        f"Release: {__release_date__}\n"
        f"Author: {__author__}"
    )
