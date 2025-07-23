import json
import time
import base64
import hashlib
import hmac
import datetime
from urllib.parse import urlencode
import requests
import torch
import numpy as np
from PIL import Image
import io
import os
import folder_paths

class VolcengineImgEditV3:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "access_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "火山引擎访问密钥AccessKey"
                }),
                "secret_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "火山引擎访问密钥SecretKey"
                }),
                "image": ("IMAGE", {
                    "tooltip": "输入图片"
                }),
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "编辑指令，建议长度<=120字符，使用自然语言描述"
                }),
            },
            "optional": {
                "scale": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "文本描述影响程度，越大代表文本描述影响越大，输入图片影响越小"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2**32 - 1,
                    "tooltip": "随机种子，-1表示随机生成"
                }),
                "filename_prefix": ("STRING", {
                    "default": "seededit_v3",
                    "tooltip": "保存文件名前缀"
                }),
                "return_url": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否返回图片URL链接（24小时有效）"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "image_url", "local_image_path")
    FUNCTION = "edit_image"
    CATEGORY = "JM-Volcengine-API/ImgEdit"
    DESCRIPTION = "火山引擎图生图3.0指令编辑SeedEdit3.0模型 - 根据文字指令编辑图片"

    def __init__(self):
        self.service = "cv"
        self.region = "cn-north-1"
        self.host = "visual.volcengineapi.com"
        self.endpoint = "https://visual.volcengineapi.com"
        self.req_key = "seededit_v3.0"

    def sign(self, key, msg):
        """HMAC-SHA256签名"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def get_signature_key(self, key, date_stamp, region_name, service_name):
        """生成签名密钥"""
        k_date = self.sign(key.encode('utf-8'), date_stamp)
        k_region = self.sign(k_date, region_name)
        k_service = self.sign(k_region, service_name)
        k_signing = self.sign(k_service, 'request')
        return k_signing

    def format_query(self, parameters):
        """格式化查询参数"""
        request_parameters_init = ''
        for key in sorted(parameters):
            request_parameters_init += key + '=' + parameters[key] + '&'
        request_parameters = request_parameters_init[:-1]
        return request_parameters

    def sign_v4_request(self, access_key, secret_key, req_query, req_body):
        """AWS V4签名"""
        if access_key is None or secret_key is None:
            raise ValueError('No access key is available.')

        t = datetime.datetime.utcnow()
        current_date = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')
        
        canonical_uri = '/'
        canonical_querystring = req_query
        signed_headers = 'content-type;host;x-content-sha256;x-date'
        payload_hash = hashlib.sha256(req_body.encode('utf-8')).hexdigest()
        content_type = 'application/json'
        
        canonical_headers = 'content-type:' + content_type + '\n' + \
                          'host:' + self.host + '\n' + \
                          'x-content-sha256:' + payload_hash + '\n' + \
                          'x-date:' + current_date + '\n'
        
        canonical_request = 'POST' + '\n' + canonical_uri + '\n' + \
                          canonical_querystring + '\n' + canonical_headers + \
                          '\n' + signed_headers + '\n' + payload_hash
        
        algorithm = 'HMAC-SHA256'
        credential_scope = datestamp + '/' + self.region + '/' + self.service + '/' + 'request'
        string_to_sign = algorithm + '\n' + current_date + '\n' + \
                        credential_scope + '\n' + \
                        hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        
        signing_key = self.get_signature_key(secret_key, datestamp, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + \
                             credential_scope + ', ' + 'SignedHeaders=' + \
                             signed_headers + ', ' + 'Signature=' + signature
        
        headers = {
            'X-Date': current_date,
            'Authorization': authorization_header,
            'X-Content-Sha256': payload_hash,
            'Content-Type': content_type
        }
        
        return headers

    def image_to_base64(self, image):
        """将ComfyUI图片张量转换为base64字符串"""
        # 转换tensor到PIL Image
        if len(image.shape) == 4:
            image = image.squeeze(0)
        
        # 转换到numpy并调整到0-255范围
        image_np = (image.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np)
        
        # 转换为base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=95)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64

    def download_image(self, image_url):
        """下载图片并转换为ComfyUI格式"""
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                # 转换为PIL Image
                pil_image = Image.open(io.BytesIO(response.content))
                
                # 确保是RGB格式
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                
                # 转换为numpy数组
                image_np = np.array(pil_image).astype(np.float32) / 255.0
                
                # 转换为PyTorch张量
                image_tensor = torch.from_numpy(image_np)[None,]
                
                return image_tensor
            else:
                print(f"下载图片失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"下载图片异常: {str(e)}")
            return None

    def decode_base64_image(self, base64_str):
        """解码base64图片为ComfyUI格式"""
        try:
            # 解码base64
            image_data = base64.b64decode(base64_str)
            
            # 转换为PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            # 确保是RGB格式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # 转换为numpy数组
            image_np = np.array(pil_image).astype(np.float32) / 255.0
            
            # 转换为PyTorch张量
            image_tensor = torch.from_numpy(image_np)[None,]
            
            return image_tensor
        except Exception as e:
            print(f"解码base64图片异常: {str(e)}")
            return None

    def save_image(self, pil_image, filename_prefix):
        """保存图片到本地"""
        try:
            # 创建输出目录
            output_dir = os.path.join(folder_paths.output_directory)
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            counter = 1
            while True:
                filename = f"{filename_prefix}_{counter:04d}.png"
                filepath = os.path.join(output_dir, filename)
                if not os.path.exists(filepath):
                    break
                counter += 1
            
            # 保存文件
            pil_image.save(filepath, "PNG")
            print(f"图片已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存图片异常: {str(e)}")
            return None

    def create_blank_image(self):
        """创建空白图片作为错误时的返回值"""
        blank_image = Image.new('RGB', (512, 512), color='black')
        image_np = np.array(blank_image).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_np)[None,]
        return image_tensor

    def submit_task(self, access_key, secret_key, image_base64, prompt, scale=0.5, seed=-1):
        """提交图片编辑任务"""
        # 构造请求参数
        query_params = {
            'Action': 'CVSync2AsyncSubmitTask',
            'Version': '2022-08-31'
        }
        formatted_query = self.format_query(query_params)
        
        # 构造请求体
        body_params = {
            "req_key": self.req_key,
            "binary_data_base64": [image_base64],
            "prompt": prompt[:120],  # 限制最大长度
            "scale": scale
        }
        
        # 添加种子参数（如果指定）
        if seed != -1:
            body_params["seed"] = seed
        
        formatted_body = json.dumps(body_params)
        
        try:
            print("生成请求签名...")
            # 生成签名
            headers = self.sign_v4_request(access_key, secret_key, formatted_query, formatted_body)
            
            # 发送请求
            request_url = self.endpoint + '?' + formatted_query
            print("提交编辑任务...")
            
            response = requests.post(request_url, headers=headers, data=formatted_body, timeout=30)
            print(f"提交任务响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"提交任务响应: {result}")
                
                if result.get("code") == 10000:
                    return result["data"]["task_id"]
                else:
                    error_msg = result.get("message", "未知错误")
                    print(f"任务提交失败: {error_msg}")
                    return None
            else:
                print(f"HTTP请求失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return None

    def query_result(self, access_key, secret_key, task_id, return_url=True, max_retries=60, retry_interval=5):
        """查询任务结果"""
        # 构造请求参数
        query_params = {
            'Action': 'CVSync2AsyncGetResult',
            'Version': '2022-08-31'
        }
        formatted_query = self.format_query(query_params)
        
        # 构造请求体，添加req_json参数来控制返回格式
        req_json_config = {
            "return_url": return_url,
            "add_logo": False,
            "position": 0,
            "language": 0,
            "opacity": 0.3
        }
        
        body_params = {
            "req_key": self.req_key,
            "task_id": task_id,
            "req_json": json.dumps(req_json_config)
        }
        
        formatted_body = json.dumps(body_params)
        
        for attempt in range(max_retries):
            try:
                print(f"查询任务结果 (第{attempt+1}次)...")
                # 生成签名
                headers = self.sign_v4_request(access_key, secret_key, formatted_query, formatted_body)
                
                # 发送请求
                request_url = self.endpoint + '?' + formatted_query
                response = requests.post(request_url, headers=headers, data=formatted_body, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"查询结果响应: {result}")
                    
                    if result.get("code") == 10000:
                        data = result.get("data", {})
                        status = data.get("status", "")
                        
                        if status == "done":
                            # 任务完成，获取结果
                            image_urls = data.get("image_urls")
                            binary_data_base64 = data.get("binary_data_base64")
                            
                            if image_urls and len(image_urls) > 0:
                                print(f"获取到图片URL: {image_urls[0]}")
                                return {"type": "url", "data": image_urls[0]}
                            elif binary_data_base64 and len(binary_data_base64) > 0:
                                print("获取到base64图片数据")
                                return {"type": "base64", "data": binary_data_base64[0]}
                            else:
                                print("任务完成但未获取到图片数据")
                                return None
                        elif status in ["in_queue", "generating"]:
                            print(f"任务进行中，状态: {status}")
                        elif status == "not_found":
                            print("任务未找到")
                            return None
                        elif status == "expired":
                            print("任务已过期")
                            return None
                        else:
                            print(f"未知状态: {status}")
                    else:
                        error_msg = result.get("message", "未知错误")
                        print(f"查询失败: {error_msg}")
                        return None
                else:
                    print(f"HTTP请求失败: {response.status_code} - {response.text}")
                
                # 等待后重试
                if attempt < max_retries - 1:
                    print(f"等待 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                    
            except Exception as e:
                print(f"查询异常: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
        
        print("查询超时，任务可能仍在处理中")
        return None

    def edit_image(self, access_key, secret_key, image, prompt, scale=0.5, seed=-1, filename_prefix="seededit_v3", return_url=True):
        """主要的图片编辑函数"""
        
        # 验证必需参数
        if not access_key or not secret_key:
            return self.create_blank_image(), "错误：请提供有效的AccessKey和SecretKey", ""
        
        if not prompt.strip():
            return self.create_blank_image(), "错误：请提供编辑指令", ""
        
        try:
            print("开始处理图片...")
            # 转换图片为base64
            image_base64 = self.image_to_base64(image)
            print(f"图片转换完成，base64长度: {len(image_base64)}")
            
            # 提交任务
            task_id = self.submit_task(access_key, secret_key, image_base64, prompt, scale, seed)
            
            if not task_id:
                return self.create_blank_image(), "错误：任务提交失败", ""
            
            print(f"任务提交成功，task_id: {task_id}")
            print("等待任务完成...")
            
            # 查询结果
            result = self.query_result(access_key, secret_key, task_id, return_url)
            
            if not result:
                return self.create_blank_image(), "错误：任务执行失败或超时", ""
            
            # 处理结果
            if result["type"] == "url":
                image_url = result["data"]
                # 下载图片
                image_tensor = self.download_image(image_url)
                if image_tensor is not None:
                    # 保存图片
                    pil_image = Image.fromarray((image_tensor.squeeze(0).cpu().numpy() * 255).astype(np.uint8))
                    local_path = self.save_image(pil_image, filename_prefix)
                    return image_tensor, image_url, local_path or "保存失败"
                else:
                    return self.create_blank_image(), f"错误：下载图片失败 - {image_url}", ""
            elif result["type"] == "base64":
                base64_str = result["data"]
                # 解码base64图片
                image_tensor = self.decode_base64_image(base64_str)
                if image_tensor is not None:
                    # 保存图片
                    pil_image = Image.fromarray((image_tensor.squeeze(0).cpu().numpy() * 255).astype(np.uint8))
                    local_path = self.save_image(pil_image, filename_prefix)
                    # 返回base64数据类型说明，而不是简单的"base64数据"
                    image_url_info = f"Base64编码数据 (长度: {len(base64_str)} 字符)"
                    return image_tensor, image_url_info, local_path or "保存失败"
                else:
                    return self.create_blank_image(), "错误：解码base64图片失败", ""
            
            return self.create_blank_image(), "错误：未知的返回格式", ""
                
        except Exception as e:
            error_msg = f"编辑图片时发生错误: {str(e)}"
            print(error_msg)
            return self.create_blank_image(), error_msg, ""

# 节点映射
NODE_CLASS_MAPPINGS = {
    "VolcengineImgEditV3": VolcengineImgEditV3
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VolcengineImgEditV3": "Volcengine Img Edit V3.0"
} 