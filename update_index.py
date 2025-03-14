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
    is_hidden = False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 检查是否有隐藏标记
            hidden_match = re.search(r'<meta\s+name=["\']hidden["\']\s+content=["\']true["\']\s*/?>', content)
            if hidden_match:
                is_hidden = True
            
            # 先尝试提取<title>标签
            title_match = re.search(r'<title>(.*?)</title>', content)
            if title_match:
                title = title_match.group(1).strip()
                # 移除可能的网站名称后缀
                title = re.sub(r'\s*[|｜-]\s*.*$', '', title)
                return title, is_hidden
            
            # 如果没有title，尝试提取第一个h1
            h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content)
            if h1_match:
                return re.sub(r'<.*?>', '', h1_match.group(1)).strip(), is_hidden
            
            # 如果没有h1，尝试提取第一个h2
            h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', content)
            if h2_match:
                return re.sub(r'<.*?>', '', h2_match.group(1)).strip(), is_hidden
                
    except Exception as e:
        print(f"提取文件标题时出错: {file_path} - {str(e)}")
    
    # 如果无法提取标题，返回格式化的文件名
    base_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(base_name)[0]
    return get_pretty_name(name_without_ext), is_hidden

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
                        article_title, is_hidden = extract_html_title(file_item)
                        
                        files.append({
                            "name": file_item.name,
                            "title": article_title,
                            "path": str(rel_path),
                            "size": size_str,
                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(file_item.stat().st_mtime)),
                            "is_hidden": is_hidden
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

def generate_docs_index_html(topics):
    """生成docs目录下的index.html文件，使用优化后的样式"""
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
        .topics-list {{
            list-style: none;
            margin-top: 30px;
        }}
        .topic-item {{
            border: 1px solid #eaecef;
            border-radius: 10px;
            margin-bottom: 30px;
            overflow: hidden;
            background-color: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}
        .topic-header {{
            padding: 25px 30px;
            border-bottom: 2px solid #eaecef;
            background-color: #f8fafc;
        }}
        .topic-title {{
            font-size: 1.8rem;
            margin-bottom: 12px;
            color: #2c3e50;
            font-weight: 600;
        }}
        .topic-desc {{
            color: #666;
            font-size: 1.05rem;
            margin-bottom: 0;
            line-height: 1.5;
        }}
        .articles-list {{
            list-style: none;
            padding: 0;
            background-color: #fff;
        }}
        .article-item {{
            padding: 20px 30px;
            border-bottom: 1px solid #eaecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }}
        .article-item:last-child {{
            border-bottom: none;
        }}
        .article-item:hover {{
            background-color: #f8fafc;
        }}
        .article-link {{
            text-decoration: none;
            color: #2c3e50;
            flex-grow: 1;
            padding-right: 20px;
            font-size: 1.1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .article-link:hover {{
            color: #3498db;
        }}
        .article-meta {{
            color: #7f8c8d;
            font-size: 0.95rem;
            white-space: nowrap;
            padding-left: 15px;
            border-left: 1px solid #eaecef;
        }}
        p.description {{
            font-size: 1.1rem;
            color: #666;
            max-width: 800px;
            margin: 0 auto;
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
        .no-articles {{
            padding: 20px 25px;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>技术文档中心</h1>
            <p class="description">这里收集了各种技术主题的文档和学习资料，帮助您快速了解和掌握各种技术知识。</p>
        </header>

        <ul class="topics-list">
            {topic_items}
        </ul>

        <footer>
            <p>&copy; {current_year} 技术文档中心 | 基于 <a href="https://pages.github.com/" target="_blank">GitHub Pages</a> 构建</p>
            <p class="update-info">最后更新: {last_update}</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # 生成主题列表项HTML
    topic_items = []
    for topic in topics:
        # 生成文章列表
        articles_html = ""
        # 过滤掉隐藏的文章
        visible_files = [file for file in topic['files'] if not file.get('is_hidden', False)]
        
        if visible_files:
            articles_html = "".join([
                f"""<li class="article-item">
                    <a href="{file['path']}" class="article-link">{file['title']}</a>
                    <span class="article-meta">{file['modified']}</span>
                </li>""" for file in sorted(visible_files, key=lambda x: x['modified'], reverse=True)
            ])
        else:
            articles_html = '<li class="no-articles">暂无文章</li>'

        item = f"""<li class="topic-item">
                <div class="topic-header">
                    <h2 class="topic-title">{topic['pretty_name']}</h2>
                    <p class="topic-desc">{topic['description']}</p>
                </div>
                <ul class="articles-list">
                    {articles_html}
                </ul>
            </li>"""
        topic_items.append(item)
    
    # 合并所有主题列表项，去除可能产生的空行
    all_items = "".join(topic_items)
    
    # 获取当前年份和时间
    current_year = time.strftime("%Y")
    last_update = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 填充模板
    html_content = template.format(
        topic_items=all_items,
        current_year=current_year,
        last_update=last_update
    )
    
    # 去除多余的换行，防止每次运行产生不同的空行
    html_content = re.sub(r'\n{3,}', '\n\n', html_content)
    
    # 检查文件是否存在并且内容没有变化
    docs_index_path = os.path.join("docs", "index.html")
    if os.path.exists(docs_index_path):
        try:
            with open(docs_index_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            
            # 如果内容没有实质性变化，则不写入
            if existing_content.strip() == html_content.strip():
                print("docs/index.html 内容无变化，跳过更新")
                return
        except Exception as e:
            print(f"读取现有文件时出错: {e}")
    
    # 写入文件
    with open(docs_index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"已更新docs/index.html，包含 {len(topics)} 个主题")

def add_home_button_to_pages():
    """为所有子页面添加或更新返回首页按钮"""
    docs_dir = Path("docs")
    
    if not docs_dir.exists() or not docs_dir.is_dir():
        print("警告: docs目录不存在")
        return
    
    # 遍历docs目录下的所有子目录中的HTML文件
    for html_file in docs_dir.rglob('*.html'):
        # 跳过index.html文件，它是主页
        if html_file.name == 'index.html' and html_file.parent == docs_dir:
            continue
        
        try:
            with open(html_file, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 先移除所有已存在的返回首页按钮和相关样式，避免重复
            updated_content = content
            
            # 移除多余的style标签
            updated_content = re.sub(r'(\s*</style>){2,}', '</style>', updated_content)
            
            # 移除所有已存在的返回首页按钮
            updated_content = re.sub(
                r'<a [^>]*class="home-button-fixed"[^>]*>.*?</a>',
                '',
                updated_content,
                flags=re.DOTALL
            )
            
            # 清理其他可能存在的返回首页按钮
            updated_content = re.sub(
                r'<div[^>]*>\s*<a[^>]*class="home-link"[^>]*>.*?返回首页\s*</a>\s*</div>',
                '',
                updated_content,
                flags=re.DOTALL
            )
            
            updated_content = re.sub(
                r'<div class="mb-4">\s*<a href="[^"]*" class="home-link">.*?返回首页\s*</a>\s*</div>',
                '',
                updated_content,
                flags=re.DOTALL
            )
            
            # 移除旧的按钮样式
            updated_content = re.sub(
                r'/\* 返回首页按钮样式 \*/.*?}(\s*</style>)',
                r'\1',
                updated_content,
                flags=re.DOTALL
            )
            
            # 添加新的样式定义
            if '<style' in updated_content and '</style>' in updated_content:
                updated_content = re.sub(
                    r'(</style>)',
                    r'''/* 返回首页按钮样式 */
        .home-button-fixed {
            position: fixed;
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background-color: #3498db;
            color: white;
            border-radius: 50%;
            text-decoration: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: background-color 0.3s, transform 0.2s;
        }
        .home-button-fixed:hover {
            background-color: #2980b9;
            transform: translateY(-50%) translateX(2px);
        }
        .home-button-fixed svg {
            width: 20px;
            height: 20px;
        }
        @media (max-width: 768px) {
            .home-button-fixed {
                top: 50%;
                left: 10px;
                width: 36px;
                height: 36px;
            }
            .home-button-fixed svg {
                width: 18px;
                height: 18px;
            }
        }\1''',
                    updated_content,
                    count=1  # 只替换第一个</style>，避免重复
                )
            
            # 添加新的按钮元素
            if updated_content.find('<body') != -1:
                # 在body标签后添加新按钮
                updated_content = re.sub(
                    r'<body[^>]*>',
                    r'''\g<0><a href="../index.html" class="home-button-fixed" title="返回首页"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg></a>''',
                    updated_content,
                    count=1  # 只添加一次
                )
            
            # 去除多余的换行，防止每次运行产生不同的空行
            updated_content = re.sub(r'\n{3,}', '\n\n', updated_content)
            
            # 检查内容是否有实质性变化
            if content.strip() == updated_content.strip():
                continue
                
            # 保存更新后的内容
            with open(html_file, 'w', encoding='utf-8') as file:
                file.write(updated_content)
                
        except Exception as e:
            print(f"处理文件 {html_file} 时出错: {e}")
    
    print("所有页面的返回首页按钮已更新为仅图标样式")

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
    
    # 生成docs/index.html
    generate_docs_index_html(topics)
    
    # 为所有页面添加/更新返回首页按钮
    add_home_button_to_pages()
    
    print("索引文件和返回首页按钮已自动更新")

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