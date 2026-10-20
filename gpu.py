import ast

import requests
from fake_useragent import UserAgent

from watch import watch_gpu, region2name, gpu_aliases



def get_machine_info(config, gpu, region,gpu_num):
    url = config.api_url('user/machine/list')
    headers = {
        'User-Agent': UserAgent().random,
        'Authorization': config.Authorization
    }
    data = {
        'charge_type': 'payg',
        'default_order': True,
        'gpu_idle_num': gpu_num,
        'gpu_type_name': [gpu],
        'page_index': 1,
        'page_size': 10,
        'region_sign_list': ast.literal_eval(region),
    }
    
    machine_info = []
    response = requests.post(url = url, headers = headers, json = data).json()
  
    if not isinstance(response.get('data'), dict) or not isinstance(response['data'].get('list'), list):
        print(f"机器列表查询失败: code={response.get('code')}, message={response.get('msg') or response.get('message')}", flush=True)
        return []
    print(f"{gpu} 区域 {region}: 返回 {len(response['data']['list'])} 台机器，需要 {gpu_num} 张卡", flush=True)
    for v in response['data']['list']:
        
        if v['gpu_idle_num']<gpu_num:
            continue
      
        machine_info.append({
            'machine_id': v['machine_id'],
            'machine_price': v['payg_price']
        })
    
    # exit()
    return machine_info


def buy(config, gpu, gpu_num,image,private_image_uuid):
    gpu = gpu_aliases.get(gpu, gpu)
    if image is None:
        image = 'hub.kce.ksyun.com/autodl-image/torch:cuda12.4-cudnn-devel-ubuntu22.04-py312-torch2.5.1'
    url = config.api_url('order/instance/create/payg')
    headers = {
        'User-Agent': UserAgent().random,
        'Authorization': config.Authorization
    }
    data = {
        'instance_info': {
            'charge_type': 'payg',
            'expand_data_disk': 0,
            'image': image,
            'machine_id': '',
            'req_gpu_amount': gpu_num,
            'private_image_uuid': private_image_uuid,
        },
        'price_info': {
            'charge_type': 'payg',
            'expand_data_disk': 0,
            'machine_id': '',
            'num': gpu_num
        }
    }
    
    # 购买结果
    result = {
        'success': False,
        'message': '',
        'region': '',
        'machine_id': '',
        'price': '',
        'region_name': '',
        'gpu_info': {}
    }
    
    gpu_info = watch_gpu(config, gpu)
    result['gpu_info'] = gpu_info
    
    for region in gpu_info.keys():
        code = ''
        machine_info = get_machine_info(config, gpu, region, gpu_num)
        for info in machine_info:
            data['instance_info']['machine_id'] = info['machine_id']
            data['price_info']['machine_id'] = info['machine_id']
            print(f"正在尝试租用 {gpu}，机器 {info['machine_id']}，卡数 {gpu_num}", flush=True)
            response = requests.post(url = url, headers = headers, json = data).json()
            if response.get('code') == 'Success':
                info['machine_price'] = info['machine_price']/1000  # 转换为元/小时
                code = 'Success'
                result['success'] = True
                result['region'] = region
                result['machine_id'] = info['machine_id']
                result['price'] = info['machine_price']
                result['region_name'] = region2name.get(str(region), str(region))
                result['message'] = f"购买成功: {result['region_name']} - {info['machine_id']} - {info['machine_price']}元/小时"
                print(result['message'])
                return result
            else:
                result['message'] = f"创建实例失败: code={response.get('code')}, message={response.get('msg') or response.get('message')}"
                print(result['message'], flush=True)
                continue
        if code == 'Success':
            break
        else:
            continue
    
    # 如果没有购买成功
    if not result['message']:
        result['message'] = f"购买失败: 没有找到可用的 {gpu} GPU"
    print(result['message'])
    return result

