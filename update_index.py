#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, DirDeletedEvent

# 主题描述映射（如果没有自动检测到描述，将使用这些默认描述）
DEFAULT_DESCRIPTIONS = {
    "redis": "Redis 数据库的核心概念、用法、配置和最佳实践。",
    "data-structure": "常见数据结构的原理、实现和应用场景分析。",
    "mysql": "MySQL 数据库的基础知识、优化技巧和进阶内容。",
    "cicd": "持续集成和持续部署的流程、工具和实践指南。"
}

# 上次修改时的目录哈希值
last_dir_hash = ""

def get_pretty_name(directory_name):
    """将目录名转换为更美观的显示名称"""
    # 替换连字符为空格并对每个单词首字母大写
    pretty_name = directory_name.replace('-', ' ').title()
    
    # 特殊处理某些缩写
    replacements = {
        "Ci Cd": "CI/CD",
        "Mysql": "MySQL",
        "Redis": "Redis",
    }
    
    for key, value in replacements.items():
        if key in pretty_name:
            pretty_name = pretty_name.replace(key, value)
    
    return pretty_name

def extract_description(directory_path):
    """尝试从目录中的README.md或index.html文件中提取描述"""
    # 首先尝试从README.md提取
    readme_path = os.path.join(directory_path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 尝试匹配第一段或一句简短描述
            match = re.search(r'# .+?\n\n(.+?)(\n\n|\Z)', content, re.DOTALL)
            if match:
                description = match.group(1).strip()
                # 如果描述太长，截取前100个字符
                if len(description) > 100:
                    description = description[:97] + "..."
                return description
    
    # 然后尝试从index.html提取
    index_path = os.path.join(directory_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 尝试匹配meta描述标签
            match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content)
            if match:
                return match.group(1)
            
            # 尝试匹配第一个段落
            match = re.search(r'<p>(.*?)</p>', content)
            if match:
                description = re.sub(r'<.*?>', '', match.group(1)).strip()
                if len(description) > 100:
                    description = description[:97] + "..."
                return description
    
    # 使用默认描述或生成一个基本描述
    dir_name = os.path.basename(directory_path)
    return DEFAULT_DESCRIPTIONS.get(dir_name, f"{get_pretty_name(dir_name)}相关的文档和教程。")

def extract_html_title(file_path):
    """从HTML文件中提取标题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 先尝试提取<title>标签
            title_match = re.search(r'<title>(.*?)</title>', content)
            if title_match:
                title = title_match.group(1).strip()
                # 移除可能的网站名称后缀
                title = re.sub(r'\s*[|｜-]\s*.*$', '', title)
                return title
            
            # 如果没有title，尝试提取第一个h1
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content)
            if h1_match:
                return re.sub(r'<.*?>', '', h1_match.group(1)).strip()
            
            # 如果没有h1，尝试提取第一个h2
            h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', content)
            if h2_match:
                return re.sub(r'<.*?>', '', h2_match.group(1)).strip()
                
    except Exception as e:
        print(f"提取文件标题时出错: {file_path} - {str(e)}")
    
    # 如果无法提取标题，返回格式化的文件名
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    return get_pretty_name(name_without_ext)

def scan_docs_directory():
    """扫描docs目录，返回主题列表及其描述和文件列表（带有标题）"""
    topics = []
    docs_dir = Path("docs")
    
    if not docs_dir.exists() or not docs_dir.is_dir():
        print("警告: docs目录不存在")
        return topics
    
    # 遍历docs目录下的所有子目录（每个子目录为一个主题）
    for item in docs_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
            topic_name = item.name
            topic_path = item
            pretty_name = get_pretty_name(topic_name)
            description = extract_description(item)
            
            # 获取该主题目录下的所有文件
            files = []
            for file_item in topic_path.rglob('*'):
                if file_item.is_file() and not file_item.name.startswith('.') and not file_item.name.startswith('_'):
                    # 仅处理HTML文件
                    if file_item.suffix.lower() == '.html':
                        # 计算文件相对于docs目录的路径
                        rel_path = file_item.relative_to(docs_dir)
                        # 获取文件信息
                        file_size = file_item.stat().st_size
                        # 格式化文件大小
                        if file_size < 1024:
                            size_str = f"{file_size} B"
                        elif file_size < 1024 * 1024:
                            size_str = f"{file_size/1024:.1f} KB"
                        else:
                            size_str = f"{file_size/(1024*1024):.1f} MB"
                        
                        # 提取文章标题
                        article_title = extract_html_title(file_item)
                        
                        files.append({
                            "name": file_item.name,
                            "title": article_title,
                            "path": str(rel_path),
                            "size": size_str,
                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(file_item.stat().st_mtime))
                        })
            
            topics.append({
                "name": topic_name,
                "pretty_name": pretty_name,
                "description": description,
                "path": f"docs/{topic_name}/",
                "files": files
            })
    
    # 按名称字母顺序排序
    topics.sort(key=lambda x: x["name"])
    
    return topics

def generate_root_index_html(topics):
    """生成根目录的index.html文件，包含多级目录结构"""
    template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>技术文档中心</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f9f9fc;
            padding: 0;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: transparent;
        }}
        header {{
            text-align: center;
            margin-bottom: 50px;
            padding-top: 40px;
        }}
        h1 {{
            font-size: 2.8rem;
            margin-bottom: 20px;
            color: #2c3e50;
            font-weight: 600;
        }}
        h2 {{
            font-size: 1.8rem;
            margin: 40px 0 20px;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        p.description {{
            font-size: 1.1rem;
            color: #666;
            max-width: 800px;
            margin: 0 auto;
        }}
        .topic-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }}
        .topic-card {{
            border: 1px solid #eaecef;
            border-radius: 10px;
            padding: 25px;
            transition: all 0.3s ease;
            background-color: #ffffff;
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.03);
        }}
        .topic-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07);
        }}
        .topic-card h3 {{
            font-size: 1.5rem;
            margin-bottom: 12px;
            color: #3498db;
        }}
        .topic-card p {{
            color: #666;
            margin-bottom: 15px;
        }}
        .file-list {{
            margin-top: 15px;
            border-top: 1px solid #eee;
            padding-top: 15px;
        }}
        .file-list table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            table-layout: fixed;
        }}
        .file-list th, .file-list td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #eee;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .file-list th:first-child, .file-list td:first-child {{
            width: 60%;
        }}
        .file-list th:nth-child(2), .file-list td:nth-child(2) {{
            width: 15%;
            text-align: right;
        }}
        .file-list th:nth-child(3), .file-list td:nth-child(3) {{
            width: 25%;
        }}
        .file-list tr:last-child td {{
            border-bottom: none;
        }}
        .file-list th {{
            color: #7f8c8d;
            font-weight: 500;
        }}
        .file-list tr:hover {{
            background-color: #f8f9fa;
        }}
        .file-list a {{
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .file-list a:hover {{
            text-decoration: underline;
        }}
        .file-list .file-size, .file-list .file-date {{
            color: #7f8c8d;
            white-space: nowrap;
            font-size: 0.85rem;
        }}
        .file-list .file-size {{
            text-align: right;
        }}
        footer {{
            text-align: center;
            margin-top: 50px;
            color: #7f8c8d;
            font-size: 0.9rem;
        }}
        footer a {{
            color: #3498db;
            text-decoration: none;
        }}
        footer a:hover {{
            text-decoration: underline;
        }}
        .update-info {{
            text-align: center;
            font-size: 0.8rem;
            color: #999;
            margin-top: 10px;
        }}
        .no-files {{
            font-style: italic;
            color: #999;
            padding: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>技术文档中心</h1>
            <p class="description">这里收集了各种技术主题的文档和学习资料，帮助您快速了解和掌握各种技术知识。</p>
        </header>

        <div class="topic-grid">
            {topic_cards}
        </div>

        <footer>
            <p>&copy; {current_year} 技术文档中心 | 基于 <a href="https://pages.github.com/" target="_blank">GitHub Pages</a> 构建</p>
            <p class="update-info">最后更新: {last_update}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # 生成每个主题的卡片HTML
    topic_cards = []
    for topic in topics:
        # 准备文件列表HTML
        files_html = ""
        if topic["files"]:
            files_table = """
                <table>
                    <thead>
                        <tr>
                            <th>文章标题</th>
                            <th>大小</th>
                            <th>修改日期</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for file in sorted(topic["files"], key=lambda x: x["name"]):
                file_path = f"docs/{file['path']}"
                file_title = file["title"]
                file_size = file["size"]
                file_date = file["modified"]
                
                files_table += f"""
                        <tr>
                            <td><a href="{file_path}" target="_blank">{file_title}</a></td>
                            <td class="file-size">{file_size}</td>
                            <td class="file-date">{file_date}</td>
                        </tr>
                """
            
            files_table += """
                    </tbody>
                </table>
            """
            files_html = files_table
        else:
            files_html = "<p class='no-files'>该主题目录下暂无文件</p>"

        card = f"""
            <div class="topic-card">
                <h3>{topic['pretty_name']}</h3>
                <p>{topic['description']}</p>
                <div class="file-list">
                    {files_html}
                </div>
            </div>"""
        topic_cards.append(card)
    
    # 合并所有卡片
    all_cards = "\n".join(topic_cards)
    
    # 获取当前年份和时间
    current_year = time.strftime("%Y")
    last_update = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 填充模板
    html_content = template.format(
        topic_cards=all_cards,
        current_year=current_year,
        last_update=last_update
    )
    
    # 写入文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"已更新根目录index.html，包含 {len(topics)} 个主题")

def update_indexes():
    """扫描目录并更新索引文件"""
    global last_dir_hash
    
    # 扫描目录
    topics = scan_docs_directory()
    
    # 计算当前目录状态的哈希值
    current_hash = hashlib.md5(str(topics).encode()).hexdigest()
    
    # 如果目录没有变化，跳过更新
    if current_hash == last_dir_hash:
        return
    
    # 更新哈希值
    last_dir_hash = current_hash
    
    # 生成索引文件
    generate_root_index_html(topics)
    print("索引文件已更新")

class DocsChangeHandler(FileSystemEventHandler):
    """处理文档目录的文件系统事件"""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_triggered = 0
        self.cooldown = 2  # 冷却时间（秒）
    
    def on_any_event(self, event):
        # 忽略临时文件和隐藏文件
        if event.src_path.endswith("~") or "/." in event.src_path:
            return
            
        # 限制触发频率
        current_time = time.time()
        if current_time - self.last_triggered < self.cooldown:
            return
            
        self.last_triggered = current_time
        self.callback()

def main():
    """主程序入口点"""
    print("启动目录监控服务...")
    
    # 初始化：确保docs目录存在
    if not os.path.exists("docs"):
        print("警告: docs目录不存在，正在创建...")
        os.makedirs("docs")
    
    # 初始更新一次索引
    update_indexes()
    
    # 设置文件系统观察者
    event_handler = DocsChangeHandler(update_indexes)
    observer = Observer()
    observer.schedule(event_handler, "docs", recursive=True)
    observer.start()
    
    try:
        print("监控服务已启动，按Ctrl+C退出")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main() 