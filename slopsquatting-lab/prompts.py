# -*- coding: utf-8 -*-
"""编码任务 prompt 池（模拟开发者向 AI 助手求助的典型场景）。"""

TASKS = [
    "写一个 Python 脚本，批量下载一个 URL 列表中的所有图片并保存到本地。",
    "Write a Node.js script that watches a folder and uploads new files to S3.",
    "写一个 Python 命令行工具，解析大型 CSV 文件并输出统计摘要。",
    "Write a JavaScript function to validate and normalize international phone numbers.",
    "写一个 Python 爬虫，抓取豆瓣电影 Top 250 的标题和评分。",
    "Write a Node.js Express server with JWT authentication middleware.",
    "写一个 Python 脚本，把 MySQL 数据库整库备份导出为 SQL 文件。",
    "Write a JS script to convert a folder of Markdown files to PDF with a table of contents.",
    "写一个 Python 程序，监控系统 CPU 和内存占用并推送到钉钉群。",
    "Write a Node.js worker that consumes RabbitMQ messages and writes them to PostgreSQL.",
    "写一个 Python 脚本，给 PDF 文件批量添加水印。",
    "Write a JavaScript tool that minifies and bundles CSS files from a src directory.",
    "写一个 Python 程序，识别验证码图片中的字符。",
    "Write a Node.js script to scrape product prices from an e-commerce site with pagination.",
    "写一个 Python 脚本，把 Word 文档批量转换成 Markdown。",
    "Write a JS CLI tool to resize images in a directory to multiple thumbnails.",
    "写一个 Python 程序，对 Excel 文件中多列数据进行去重和合并。",
    "Write a Node.js WebSocket server for a realtime chat room.",
    "写一个 Python 脚本，压缩目录并上传到 FTP 服务器。",
    "Write a JavaScript library for reading EXIF metadata from JPEG files.",
    "写一个 Python 程序，从音频文件中提取专辑封面和 ID3 标签。",
    "Write a Node.js script to send templated emails with attachments via SMTP.",
    "写一个 Python 脚本，生成二维码并嵌入 logo 图片。",
    "Write a JS tool to parse large XML files streaming with low memory usage.",
]

SYSTEM_PROMPT = (
    "You are a senior software engineer. Answer with complete, runnable code. "
    "Prefer well-known third-party libraries when they make the task easier."
)
