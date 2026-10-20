import logging

import requests

logger = logging.getLogger(__name__)
from fake_useragent import UserAgent

# 官网型号与公开区域快照；运行 python update_gpu_catalog.py 刷新。
# 这里是查询范围，不是部署断言：实际型号分布由官网响应筛选。
import json
from pathlib import Path

_catalog = json.loads(Path(__file__).with_name('gpu_catalog.json').read_text(encoding='utf-8'))
region2name = {str(region['signs']): region['name'] for region in _catalog['regions']}
gpu2region = {
    model: [list(region['signs']) for region in _catalog['regions']]
    for model in _catalog['models']
}
# 兼容官网已更名的旧配置。
gpu_aliases = {'RTX 3080*2': 'RTX 3080x2', 'RTX 2080 Ti *2': 'RTX 2080 Ti x2'}
gpu2region.update({old: gpu2region[new] for old, new in gpu_aliases.items()})


def watch_gpu(config, gpu):
    gpu = gpu_aliases.get(gpu, gpu)
    url = 'https://www.autodl.com/api/v1/sub_user/machine/region/gpu_type'
    headers = {
        'User-Agent': UserAgent().random,
        'Authorization': config.Authorization
    }
    gpu_info = {}
    for region in gpu2region[gpu]:
        try:
            result = requests.post(
                url=url, headers=headers,
                json={'region_sign_list': region}, timeout=30,
            )
            result.raise_for_status()
            response = result.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning('GPU query failed for region %s: %s', region, exc)
            continue

        if not isinstance(response, dict):
            logger.warning('Invalid GPU response for region %s: expected an object', region)
            continue

        data = response.get('data')
        if not isinstance(data, list):
            logger.warning(
                'GPU query returned no valid data for region %s (code=%s, message=%s). '
                'Check authorization if authentication failed.',
                region, response.get('code'),
                response.get('msg') or response.get('message'),
            )
            continue

        for v in data:
            if isinstance(v, dict) and isinstance(v.get(gpu), dict):
                gpu_info[str(region)] = {'gpu': gpu, **v[gpu]}
                break
    return gpu_info


