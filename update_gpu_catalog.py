"""从 AutoDL 官网只读接口刷新型号和公开区域：python update_gpu_catalog.py。"""
import json
from pathlib import Path

import requests

BASE = 'https://www.autodl.com/api/v1/'
CATALOG_PATH = Path(__file__).with_name('gpu_catalog.json')


def fetch_catalog():
    def get(path):
        response = requests.get(BASE + path, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get('code') != 'Success' or not isinstance(payload.get('data'), list):
            raise ValueError(f'官网接口 {path} 返回无效数据')
        return payload['data']

    models = [item['gpu_name'] for item in get('machine/gpu_type')]
    groups = {}
    for region in get('region/list'):
        if region.get('visible') != 'all':
            continue
        group = groups.setdefault(region['data_center'], {
            'name': region['region_name'], 'signs': [],
        })
        group['signs'].append(region['region_sign'])
    if not models or not groups:
        raise ValueError('官网型号或区域列表为空，保留现有文件')
    return {
        'sources': [BASE + 'machine/gpu_type', BASE + 'region/list'],
        'note': '公开区域查询候选集，不代表每个型号在所有区域都有部署；实际分布由 region/gpu_type 返回。',
        'models': models,
        'regions': list(groups.values()),
    }


if __name__ == '__main__':
    catalog = fetch_catalog()
    temporary = CATALOG_PATH.with_suffix('.tmp')
    temporary.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(CATALOG_PATH)
    print(f"已更新 {len(catalog['models'])} 个型号、{len(catalog['regions'])} 个公开区域组")
