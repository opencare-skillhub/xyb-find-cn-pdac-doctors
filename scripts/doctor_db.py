#!/usr/bin/env python3
"""找医生：从 CSV 查询完整名单；仅依赖 Python 3 标准库。"""
import argparse
from collections import Counter
import csv
from datetime import date
import json
from pathlib import Path
import sqlite3
import sys

SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIRED = {
    'doctors': ('序号', '姓名', '医院', '科室', '城市', '来源日期', '关键依据'),
    'trials': ('序号', '试验编号', '药物/方案', '医院/中心', '城市', '来源'),
}


def rows_from(path, table='doctors'):
    if path.suffix.lower() == '.csv':
        with path.open(newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError('缺少表头或存在重复列名')
            missing = set(REQUIRED[table]) - set(reader.fieldnames)
            if missing:
                raise ValueError('缺少字段：' + '、'.join(sorted(missing)))
            rows = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError('CSV 行列数不一致；含逗号或换行的单元格必须用双引号包围')
        return rows
    if path.suffix.lower() in ('.db', '.sqlite', '.sqlite3'):
        # 仅显式 --db 使用 SQLite；不创建或修改数据库。
        con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(f'SELECT * FROM {table}')]
        finally:
            con.close()
    raise ValueError('仅支持 CSV 或 SQLite')


def match(row, terms):
    blob = ' '.join(str(v or '') for v in row.values()).casefold()
    return all(t.casefold() in blob for t in terms)


def validate(rows, table):
    errors = []
    keys = Counter()
    ids = Counter()
    for i, row in enumerate(rows, 2):
        for field in REQUIRED[table]:
            if not str(row.get(field) or '').strip():
                errors.append(f'第 {i} 行缺少 {field}')
        ids[row.get('序号')] += 1
        if table == 'doctors':
            keys[tuple(row.get(k) for k in ('姓名', '医院', '科室'))] += 1
            try:
                date.fromisoformat(row.get('来源日期', ''))
            except ValueError:
                errors.append(f'第 {i} 行来源日期不是 YYYY-MM-DD')
    for key, count in ids.items():
        if count > 1:
            errors.append(f'重复序号：{key}')
    for key, count in keys.items():
        if count > 1:
            errors.append(f'重复医生身份：{key}')
    return errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--query', default='', help='空格分隔的关键词，全部匹配')
    ap.add_argument('--name', help='按姓名精确匹配，避免命中其他医生备注中的姓名')
    ap.add_argument('--city', help='按城市字段匹配')
    ap.add_argument('--dept', help='按科室字段匹配')
    ap.add_argument('--db', help='显式指定 CSV 或 SQLite；默认读取技能内 CSV')
    ap.add_argument('--table', default='doctors', choices=REQUIRED)
    ap.add_argument('--list', action='store_true', help='列出全部；不能与非空 query 同用')
    fmt = ap.add_mutually_exclusive_group()
    fmt.add_argument('--brief', action='store_true', help='完整编号列表（默认），不截断备注')
    fmt.add_argument('--json', action='store_true', help='返回所有匹配记录的所有字段')
    ap.add_argument('--audit', action='store_true', help='全部数据的分布及完整待复核记录')
    ap.add_argument('--validate', action='store_true', help='检查 CSV 字段、必填值、日期及重复记录')
    args = ap.parse_args()
    if args.list and (args.query.strip() or args.name or args.city or args.dept):
        ap.error('--list 与 --query 不能同时使用')
    path = Path(args.db).expanduser() if args.db else SKILL_DIR / 'data' / (args.table + '.csv')
    try:
        rows = rows_from(path, args.table)
        if args.validate:
            errors = validate(rows, args.table)
            print(json.dumps({'ok': not errors, 'table': args.table, 'count': len(rows), 'errors': errors}, ensure_ascii=False, indent=2))
            return 1 if errors else 0
        out = [r for r in rows if match(r, args.query.split())
               and (not args.name or r.get('姓名') == args.name)
               and (not args.city or args.city in r.get('城市', ''))
               and (not args.dept or args.dept in r.get('科室', ''))]
        if args.audit:
            pending = [r for r in rows if r.get('风险状态') in ('R1', 'RU') or r.get('未知项', '') not in ('', '—', '-') or any(k in (r.get('候选结论', '') + r.get('备注', '')) for k in ('待核', '待补', '待确认', '口径', '同名', '暂缓'))]
            result = {'ok': True, 'table': args.table, 'count': len(rows), 'risk_counts': dict(Counter(r.get('风险状态', '未记录') for r in rows)), 'pending_count': len(pending), 'pending_rows': pending}
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.json:
            print(json.dumps({'ok': True, 'db': str(path), 'table': args.table, 'count': len(out), 'rows': out}, ensure_ascii=False, indent=2))
        else:
            print(f'共 {len(out)} 条（全部匹配记录；库内清单，不代表全国穷尽名单）')
            fields = ('姓名', '医院', '科室', '城市', 'ABC分类', '风险状态', '主要用途', '来源日期', '关键依据', '备注') if args.table == 'doctors' else ('试验编号', '药物/方案', '医院/中心', '城市', '主要研究者(PI)', '状态', '来源', '备注')
            for i, row in enumerate(out, 1):
                # 保留完整内容；换行显示为字面 \\n，确保一条记录占一行。
                parts = [f'{k}：{row.get(k) or "未记录"}'.replace('\n', '\\n').replace('\r', '\\r') for k in fields]
                print(f'{i}. ' + ' | '.join(parts))
        return 0
    except (OSError, ValueError, sqlite3.Error, csv.Error) as exc:
        print(json.dumps({'ok': False, 'reason': str(exc), 'db': str(path)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
