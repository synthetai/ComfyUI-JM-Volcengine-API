from .nodes.volcengine_seedream_v3 import VolcengineSeeDreamV3Node
from .nodes.volcengine_i2v_s2pro import VolcengineI2VS2Pro
from .nodes.volcengine_img_edit_v3 import VolcengineImgEditV3

NODE_CLASS_MAPPINGS = {
    "volcengine-seedream-v3": VolcengineSeeDreamV3Node,
    "volcengine-i2v-s2pro": VolcengineI2VS2Pro,
    "volcengine-img-edit-v3": VolcengineImgEditV3
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "volcengine-seedream-v3": "Volcengine SeeDream V3",
    "volcengine-i2v-s2pro": "Volcengine I2V S2.0Pro",
    "volcengine-img-edit-v3": "Volcengine Img Edit V3.0"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 