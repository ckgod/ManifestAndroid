#!/usr/bin/env python3
"""Writerside 헤더 anchor ID 중복 린트.

Writerside는 헤더에서 anchor ID를 생성할 때, 명시 {#id} 가 있으면 그 값을,
없으면 헤더 텍스트의 영문/숫자만 추출해 소문자화한 값을 쓴다. 그래서
'### CoroutineScope란' 과 '### coroutineScope 빌더' 가 모두 'coroutinescope' 로
충돌하면 빌드가 MRK003(Element ID is not unique)으로 실패한다.

이 스크립트는 그 규칙을 재현해 한 파일 안의 ID 중복을 빌드 전에 잡는다.
- 영문 ID가 비는(순수 한글) 헤더는 Writerside가 별도 처리하므로 검사 제외.
- 같은 ID가 한 파일에서 둘 이상이면 종료 코드 1.

사용법: python .github/scripts/anchor_lint.py Writerside/topics
"""
import re, sys, glob, os


def header_id(line):
    m = re.match(r'^#{1,6}\s+(.*)', line)
    if not m:
        return None
    text = m.group(1)
    exp = re.search(r'\{#([^}]+)\}', text)
    if exp:
        return exp.group(1).strip()
    auto = re.sub(r'[^A-Za-z0-9]', '', re.sub(r'\{#[^}]*\}', '', text)).lower()
    return auto or None  # 빈 ID(순수 한글)는 검사 제외


def lint_file(path):
    seen, dups = {}, []
    in_code = False
    for i, line in enumerate(open(path, encoding='utf-8'), 1):
        # 코드 펜스 안의 '#'(주석 등)는 헤더가 아니므로 건너뛴다
        if line.lstrip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        hid = header_id(line)
        if hid is None:
            continue
        if hid in seen:
            dups.append((hid, seen[hid], i))
        else:
            seen[hid] = i
    return dups


def main(paths):
    files = []
    for p in paths:
        files += glob.glob(os.path.join(p, '*.md')) if os.path.isdir(p) else [p]
    bad = 0
    for f in sorted(files):
        dups = lint_file(f)
        if dups:
            bad += 1
            print(f'FAIL {os.path.basename(f)}')
            for hid, a, b in dups:
                print(f'   중복 anchor ID "{hid}": line {a}, {b}  → 헤더에 고유한 {{#id}} 를 부여하세요')
    if bad == 0:
        print(f'OK — {len(files)}개 파일, anchor ID 충돌 없음')
        return 0
    print(f'\n{bad}개 파일에서 anchor ID 충돌 발견 (Writerside MRK003 유발)')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:] or ['Writerside/topics']))
