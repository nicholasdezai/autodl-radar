import json
import os
from pathlib import Path

from dotenv import dotenv_values, set_key

class Config:
    def __init__(self, config_file='config.json'):
        self.config_path = Path(__file__).parent / config_file
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config_data = json.load(f)
        
        # 环境变量 > 配置文件同目录的 .env > JSON 中的明文令牌。
        self.env_path = self.config_path.parent / '.env'
        env_values = dotenv_values(self.env_path, interpolate=False)
        authorization = self.config_data.get('authorization', '')
        if not isinstance(authorization, str):
            raise ValueError('authorization 必须是字符串')
        if authorization.startswith('${') and authorization.endswith('}'):
            key = authorization[2:-1]
            self.Authorization = os.environ.get(key, env_values.get(key)) or ''
        else:
            self.Authorization = (
                os.environ.get('API_TOKEN') or env_values.get('API_TOKEN') or authorization
            )
        
        # 运行模式配置
        self.mode = self.config_data.get('mode', 'monitor_only')  # monitor_only 或 monitor_and_buy
        
        # GPU 配置
        models = self.config_data['gpu']['model']
        if isinstance(models, str):
            models = [models]
        if (not isinstance(models, list) or not models
                or any(not isinstance(model, str) or not model.strip() for model in models)):
            raise ValueError('gpu.model 必须是非空型号字符串或非空字符串列表')
        from watch import gpu2region
        self.gpu_models = list(dict.fromkeys(model.strip() for model in models))
        unknown = [model for model in self.gpu_models if model not in gpu2region]
        if unknown:
            raise ValueError(f"不支持的 GPU 型号: {', '.join(unknown)}")
        self.gpu_model = self.gpu_models[0]  # 兼容旧代码
        self.gpu_num = self.config_data['gpu']['num']
        
        # 镜像配置
        self.private_image_uuid = self.config_data['image']['private_image_uuid']
        self.image = self.config_data['image']['autodl_image']

        # 通知配置
        self.notification_enabled = self.config_data.get('notification', {}).get('enabled', True)
        if not isinstance(self.notification_enabled, bool):
            raise ValueError('notification.enabled 必须为布尔值 true 或 false')

    def has_authorization(self):
        """检查是否有有效的 authorization"""
        return bool(self.Authorization and self.Authorization.strip())
    
    def update_authorization(self, authorization):
        """仅保存到本地 .env，避免把新令牌写入可提交的 JSON。"""
        placeholder = self.config_data.get('authorization', '')
        key = (placeholder[2:-1] if placeholder.startswith('${')
               and placeholder.endswith('}') else 'API_TOKEN')
        set_key(str(self.env_path), key, authorization)
        self.Authorization = authorization

# 创建配置实例
config = Config()
