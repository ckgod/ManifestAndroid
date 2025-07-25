import xml.etree.ElementTree as ET
import os

BASE_URL = "https://ckgod.github.io/ManifestAndroid/"
TREE_FILE_PATH = "Writerside/mi.tree"
README_PATH = "README.md"
TOC_START_COMMENT = "목차"
TOC_END_COMMENT = "참고"

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
            html_file = topic.replace('.md', '.html').lower()
            url = f"{BASE_URL}{html_file}"
            markdown_lines.append(f"{indent}* [{display_title}]({url})")

        markdown_lines.extend(parse_toc_elements(toc_element, depth + 1))

    return markdown_lines

def main():
    try:
        tree = ET.parse(TREE_FILE_PATH)
        root = tree.getroot()

        toc_lines = parse_toc_elements(root, 0)
        toc_markdown = "\n".join(toc_lines)

        with open(README_PATH, 'r', encoding='utf-8') as f:
            readme_lines = f.readlines()

        start_index = -1
        end_index = -1

        for i, line in enumerate(readme_lines):
            if TOC_START_COMMENT in line:
                start_index = i
            if TOC_END_COMMENT in line:
                end_index = i
                break

        if start_index == -1 or end_index == -1:
            print(f"오류: README.md 파일에서 TOC 주석을 찾을 수 없습니다.")
            return

        new_readme_content = "".join(readme_lines[:start_index+1])
        new_readme_content += toc_markdown + "\n"
        new_readme_content += "".join(readme_lines[end_index:])

        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_readme_content)

        print("README.md 목차가 성공적으로 업데이트되었습니다.")

    except FileNotFoundError:
        print(f"오류: {TREE_FILE_PATH} 또는 {README_PATH} 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()