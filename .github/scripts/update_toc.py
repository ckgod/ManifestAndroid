import xml.etree.ElementTree as ET
import re

BASE_URL = "https://ckgod.github.io/ManifestAndroid/"
TREE_FILE_PATH = "Writerside/mi.tree"
README_PATH = "README.md"

# 1. .tree 파일 파싱
tree = ET.parse(TREE_FILE_PATH)
root = tree.getroot()

# 2. 목차 리스트 생성
toc_list = []
for element in root.findall('toc-element'):
    title = element.get('title')
    topic_file = element.get('topic')
    if title and topic_file:
        # .md -> .html로 변경하여 URL 생성
        html_file = topic_file.replace('.md', '.html')
        url = f"{BASE_URL}{html_file}"
        toc_list.append(f"* [{title}]({url})")

toc_markdown = "\n".join(toc_list)

# 3. README.md 파일에 주입
with open(README_PATH, 'r+', encoding='utf-8') as f:
    content = f.read()
    # 와 사이의 내용을 교체
    new_content = re.sub(
        r'(?s)(.*?)',
        f'\n{toc_markdown}\n',
        content
    )
    f.seek(0)
    f.write(new_content)
    f.truncate()

print("README.md 목차가 성공적으로 업데이트되었습니다.")