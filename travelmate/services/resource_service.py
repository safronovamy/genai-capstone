import psutil
import os


def get_resource_usage():
    process = psutil.Process(os.getpid())

    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = psutil.cpu_percent(interval=0.1)

    return {
        "memory_mb": round(memory_mb, 2),
        "cpu_percent": cpu_percent,
    }