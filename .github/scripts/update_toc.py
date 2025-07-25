import xml.etree.ElementTree as ET
import re
import os

BASE_URL = "https://ckgod.github.io/ManifestAndroid/"
TREE_FILE_PATH = "Writerside/mi.tree"
README_PATH = "README.md"

def generate_title_from_filename(filename):
    base_name = os.path.splitext(filename)[0]
    return base_name.replace('-', ' ').title()

def parse_toc_elements(element, depth):
    markdown_lines = []
    indent = "  " * depth

    for toc_element in element.findall('toc-element'):
        topic = toc_element.get('topic')
        title = toc_element.get('title')

        if topic:
            display_title = title if title else generate_title_from_filename(topic)
            html_file = topic.replace('.md', '.html')
            url = f"{BASE_URL}{html_file}"
            markdown_lines.append(f"{indent}* [{display_title}]({url})")

        # Recursive call for nested elements
        markdown_lines.extend(parse_toc_elements(toc_element, depth + 1))

    return markdown_lines

def main():
    try:
        tree = ET.parse(TREE_FILE_PATH)
        root = tree.getroot()

        toc_lines = parse_toc_elements(root, 0)
        toc_markdown = "\n".join(toc_lines)

        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        if '' not in content or '' not in content:
            print("오류: README.md 파일에서 TOC 주석을 찾을 수 없습니다.")
            return

        new_content = re.sub(
            r'(?s)(.*?)',
            f'\n{toc_markdown}\n',
            content
        )

        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("README.md 목차가 성공적으로 업데이트되었습니다.")

    except FileNotFoundError:
        print(f"오류: {TREE_FILE_PATH} 또는 {README_PATH} 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()