import nacos
import yaml


class ConfigManager:
    def __init__(self, config_file="config.yaml"):
        # 本地配置
        with open(config_file, "r", encoding="utf-8") as f:
            self.local_config = yaml.safe_load(f)

        self.remote_config = {}

        # 初始化 Nacos
        nacos_conf = self.local_config.get("nacos", {})
        self.client = nacos.NacosClient(
            nacos_conf.get("server_addr"),
            namespace=nacos_conf.get("namespace", "public"),
            username=nacos_conf.get("username"),
            password=nacos_conf.get("password")
        )

        self.data_id = nacos_conf.get("data_id")
        self.group = nacos_conf.get("group", "DEFAULT_GROUP")

        # 拉取远程配置
        self._load_remote_config()

        # 监听配置变化（自动更新🔥）
        self._start_listener()

    def _load_remote_config(self):
        try:
            config_str = self.client.get_config(self.data_id, self.group)
            if config_str:
                self.remote_config = yaml.safe_load(config_str)
        except Exception as e:
            print("加载 Nacos 配置失败:", e)

    def _start_listener(self):
        def callback(args):
            config_str = args[1]
            if config_str:
                self.remote_config = yaml.safe_load(config_str)
                print("Nacos 配置已更新")

        self.client.add_config_watcher(self.data_id, self.group, callback)

    def get(self, key: str, default=None):
        """
        支持 a.b.c 形式读取
        """
        def _get_from_dict(data, key):
            keys = key.split(".")
            for k in keys:
                if not isinstance(data, dict):
                    return None
                data = data.get(k)
                if data is None:
                    return None
            return data

        # 优先远程配置
        value = _get_from_dict(self.remote_config, key)
        if value is not None:
            return value

        # fallback 本地配置
        value = _get_from_dict(self.local_config, key)
        if value is not None:
            return value

        return default


# 单例
config = ConfigManager()