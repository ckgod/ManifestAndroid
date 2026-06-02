#!/usr/bin/env python3
"""닫는 ** 강조가 렌더링되지 않는 케이스 검출 (Writerside/CommonMark).

CommonMark의 right-flanking 규칙상, 닫는 `**` 바로 앞이 구두점이고 바로 뒤가
비공백·비구두점(한글/영숫자)이면 그 `**`는 강조 종료로 인식되지 않아 굵게가
풀리지 않는다.
  예) '**결합도(coupling)**입니다' → ')' + '**' + '입' → 굵게 깨짐.
해결: 닫는 `**` 뒤에 공백을 넣는다 → '**결합도(coupling)** 입니다'.

코드펜스(```) 안은 검사 제외. 충돌 발견 시 종료 코드 1.
사용법: python .github/scripts/bold_lint.py Writerside/topics [--fix]
"""
import re, sys, glob, os

CLOSE_PUNCT = set(')]}>.,!?;:%"’”」』\'')


def _is_word(ch):
    return ch.isalnum() or '가' <= ch <= '힣'  # 영숫자 또는 한글


def _hits(line):
    out = []
    for m in re.finditer(r'\*\*(.+?)\*\*', line):
        inner = m.group(1)
        if not inner:
            continue
        after = line[m.end():m.end() + 1]
        if inner[-1] in CLOSE_PUNCT and after and _is_word(after):
            out.append((m.end(), line[max(0, m.start()):m.end() + 2]))
    return out


def process(path, apply):
    total, out, in_code = 0, [], False
    for i, line in enumerate(open(path, encoding='utf-8'), 1):
        raw = line.rstrip('\n')
        if raw.lstrip().startswith('```'):
            in_code = not in_code
            out.append(line); continue
        if in_code:
            out.append(line); continue
        hits = _hits(raw)
        for _, prev in hits:
            print(f'  {os.path.basename(path)}:{i}  …{prev}  → 닫는 "**" 뒤에 공백 필요')
        total += len(hits)
        if apply and hits:
            for end, _ in sorted(hits, key=lambda x: -x[0]):
                raw = raw[:end] + ' ' + raw[end:]
            out.append(raw + '\n')
        else:
            out.append(line)
    if apply and total:
        open(path, 'w', encoding='utf-8').write(''.join(out))
    return total


def main(argv):
    apply = '--fix' in argv
    paths = [a for a in argv if not a.startswith('--')] or ['Writerside/topics']
    files = []
    for p in paths:
        files += glob.glob(os.path.join(p, '*.md')) if os.path.isdir(p) else [p]
    grand = sum(process(f, apply) for f in sorted(files))
    if grand == 0:
        print(f'OK — {len(files)}개 파일, 깨지는 강조 없음')
        return 0
    print(('수정' if apply else '검출') + f' 총 {grand}건')
    return 0 if apply else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
