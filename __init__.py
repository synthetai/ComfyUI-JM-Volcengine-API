from .nodes.volcengine_seedream_v3 import VolcengineSeeDreamV3Node

NODE_CLASS_MAPPINGS = {
    "volcengine-seedream-v3": VolcengineSeeDreamV3Node
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "volcengine-seedream-v3": "Volcengine SeeDream V3"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 