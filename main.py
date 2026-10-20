import gpu
from config_loader import config
from login_helper import login_and_update_config
import time

import watch
from desktop_popup import show_notification

def send_notification(title, content):
    """发送本地桌面通知，失败不影响监控和购买结果。"""
    try:
        return show_notification(title, content)
    except Exception as exc:
        print(f"系统通知失败: {exc}")
        return False

def available_count(regions):
    """统计区域返回的空闲卡数，不把字典字段当作机器。"""
    total = 0
    for info in regions.values():
        idle = info.get('idle_gpu_num', info.get('idle', 0))
        if isinstance(idle, (int, float)) and not isinstance(idle, bool) and idle > 0:
            total += idle
    return total


def monitor(config):
    if config.mode not in ("monitor_only", "monitor_and_buy"):
        raise ValueError(f"未知的运行模式: {config.mode}")
    print(f"开始监控GPU: {', '.join(config.gpu_models)}")
    while True:
        available = {}
        for model in config.gpu_models:
            regions = watch.watch_gpu(config=config, gpu=model)
            print(f"{model} 监控结果: {regions}")
            if available_count(regions) > 0:
                available[model] = regions

        if config.mode == "monitor_only" and available:
            summary = "；".join(
                f"{model}: {available_count(regions)} 张空闲卡"
                for model, regions in available.items()
            )
            print(f"GPU可用: {summary}")
            if config.notification_enabled:
                send_notification(title=f"GPU可用通知 - {', '.join(available)}", content=summary)
            return

        if config.mode == "monitor_and_buy":
            for model in available:
                result = gpu.buy(
                    config=config, gpu=model, gpu_num=config.gpu_num,
                    image=config.image, private_image_uuid=config.private_image_uuid,
                )
                if result['success']:
                    print(f"抢卡成功，机器ID: {result['machine_id']}，停止抢卡。")
                    if config.notification_enabled:
                        send_notification(
                            title=f"GPU购买成功 - {model}",
                            content=f"成功购买 {config.gpu_num} 张 {model}\n机器 ID：{result['machine_id']}\n抢卡程序已停止。",
                        )
                    return
                print(f"购买失败: {result['message']}")

        print("继续监控...")
        time.sleep(10 if available else 30)


def main():
    if not config.has_authorization():
        print("检测到配置文件中没有 authorization，开始登录...")
        config.Authorization = login_and_update_config()
    monitor(config)


if __name__ == "__main__":
    main()
