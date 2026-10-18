#!/usr/bin/env python3
"""Compile manual Agency uploads; no customer service or ChatGPT API is run.

Default --check is read-only. --write is a maintainer release-authoring command,
not a Project installer or an automatic learning write-back mechanism.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'starter' / 'chatgpt' / 'agency'
EXAMPLES = ROOT / 'examples' / 'agency'


def read_source(path):
    relative = path.relative_to(ROOT)
    current = ROOT
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError('Source symlink is not supported: ' + str(relative))
    if not path.is_file():
        raise ValueError('Required source is missing or not a file: ' + str(relative))
    return path.read_text(encoding='utf-8').rstrip('\n')


def documents():
    roles = read_source(KIT / 'AGENT_ROLES.md')
    workflow = read_source(KIT / 'WORKFLOW.md')
    skills = read_source(KIT / 'SKILL_PACK.md')
    example_marker = '\n# 一句需求的首輪實作\n'
    license_marker = '\n# 授權、溯源與改編聲明\n'
    if skills.count(example_marker) != 1 or skills.count(license_marker) != 1:
        raise ValueError('Skill Pack section contract changed; inspect demo exclusion before rebuilding.')
    framework, remainder = skills.split(example_marker)
    if license_marker not in remainder:
        raise ValueError('License must follow the excluded demonstration section.')
    _, license_text = remainder.split(license_marker)
    playbook = (
        '# AGENCY_PLAYBOOK｜Agency Edition v1.0｜通用工作規則\n\n'
        '這是上傳用的單一權威合併檔，由 AGENT_ROLES.md、WORKFLOW.md 與 '
        'SKILL_PACK.md 的通用方法及完整授權聲明編譯。示範客戶、示範文案不納入；'
        '不可從編寫參考或範例推定目前客戶事實。\n\n'
        '目前客戶只依 active CLIENT_BRIEF；核准經驗只依可核對的 CURRENT_RULES '
        '精確版本。此檔不是客戶資料、人工核准、身分服務或背景執行器。'
        '不要再上傳競爭版本的三份編寫參考。\n\n'
        '---\n\n' + roles + '\n\n---\n\n' + workflow + '\n\n---\n\n'
        + framework + license_marker + license_text + '\n'
    )
    sample = (
        '# SAMPLE_WORK｜Agency Edition v1.0｜獨立 demo Project 專用\n\n'
        '以下全部是標示的虛構示範，不是真實客戶、真人回饋、已核准規則、'
        '多人協作或平台 UI 測試證據。不要與真實客戶檔案一起上傳。'
        '主要上傳清單不包含此檔；此檔不能提供目前客戶事實或核准經驗。\n\n'
        '---\n\n' + read_source(EXAMPLES / 'skincare-brief.md')
        + '\n\n---\n\n' + read_source(EXAMPLES / 'first-round.md') + '\n'
    )
    return {'AGENCY_PLAYBOOK.md': playbook, 'SAMPLE_WORK.md': sample}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true', help='Explicitly rebuild release-authoring files.')
    group.add_argument('--check', action='store_true', help='Read-only check (default).')
    args = parser.parse_args()
    try:
        outputs = documents()
        # Validate every target before any write; never follow a target symlink.
        for name in outputs:
            target = KIT / name
            if target.is_symlink() or (target.exists() and not target.is_file()):
                raise ValueError('Output is a symlink or unsupported file type: ' + name)
        if args.write:
            for name, content in outputs.items():
                with (KIT / name).open('w', encoding='utf-8', newline='\n') as stream:
                    stream.write(content)
            print('Built two manual Agency documents; no account, client or backend was accessed.')
            return 0
        stale = [name for name, content in outputs.items()
                 if not (KIT / name).is_file() or (KIT / name).read_bytes() != content.encode('utf-8')]
        if stale:
            print('Missing/stale Agency outputs: ' + ', '.join(stale), file=sys.stderr)
            return 1
        print('Agency upload/demo documents exactly match authoring inputs.')
        return 0
    except (ValueError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
