import yaml

class ConfigLoader:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def get_detection_params(self):
        return self.config["detection"]

    def get_evaluation_params(self):
        return self.config["evaluation"]
