import os
import psutil


class MetricsService:
    embedding_calls = 0
    weather_api_calls = 0

    @classmethod
    def increment_embedding_calls(cls):
        cls.embedding_calls += 1

    @classmethod
    def increment_weather_calls(cls):
        cls.weather_api_calls += 1

    @classmethod
    def get_memory_usage_mb(cls):
        process = psutil.Process(os.getpid())
        memory_bytes = process.memory_info().rss
        return round(memory_bytes / 1024 / 1024, 2)

    @classmethod
    def get_cpu_percent(cls):
        return psutil.cpu_percent(interval=0.1)

    @classmethod
    def get_metrics(cls):
        return {
            "embedding_calls": cls.embedding_calls,
            "weather_api_calls": cls.weather_api_calls,
            "memory_usage_mb": cls.get_memory_usage_mb(),
            "cpu_percent": cls.get_cpu_percent(),
        }