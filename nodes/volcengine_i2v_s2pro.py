import json
import time
import base64
import hashlib
import hmac
import datetime
from urllib.parse import quote, urlencode
import requests
import torch
import numpy as np
from PIL import Image
import io
import os
import folder_paths

class VolcengineI2VS2Pro:
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
                "aspect_ratio": (["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "9:21"], {
                    "default": "16:9",
                    "tooltip": "视频宽高比"
                }),
            },
            "optional": {
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "视频生成提示词，支持中英文，最大150字符"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2**32 - 1,
                    "tooltip": "随机种子，-1表示随机生成"
                }),
                "filename_prefix": ("STRING", {
                    "default": "volcengine_i2v",
                    "tooltip": "保存文件名前缀"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "local_video_path")
    FUNCTION = "generate_video"
    CATEGORY = "JM-Volcengine-API/I2V"
    DESCRIPTION = "火山引擎即梦AI图生视频S2.0Pro - 从图片生成高质量视频"

    def __init__(self):
        self.service = "cv"
        self.region = "cn-north-1"
        self.host = "visual.volcengineapi.com"
        self.api_version = "2022-08-31"
        self.req_key = "jimeng_vgfm_i2v_l20"

    def get_sign_key(self, secret_key, date, region, service):
        """生成签名密钥"""
        def sign(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
        
        k_date = sign(secret_key.encode('utf-8'), date)
        k_region = sign(k_date, region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, 'request')
        return k_signing

    def get_authorization(self, access_key, secret_key, method, uri, query_params, headers, payload, timestamp):
        """生成Authorization头"""
        # 时间格式
        iso_timestamp = timestamp.strftime('%Y%m%dT%H%M%SZ')
        date = timestamp.strftime('%Y%m%d')
        
        # 规范化请求字符串
        canonical_headers = []
        signed_headers = []
        
        # 排序并处理headers
        sorted_headers = sorted(headers.items(), key=lambda x: x[0].lower())
        for key, value in sorted_headers:
            canonical_headers.append(f"{key.lower()}:{value}")
            signed_headers.append(key.lower())
        
        canonical_headers_str = '\n'.join(canonical_headers)
        signed_headers_str = ';'.join(signed_headers)
        
        # 规范化查询字符串
        canonical_query_string = urlencode(sorted(query_params.items()))
        
        # payload哈希
        payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        
        # 规范化请求
        canonical_request = f"{method}\n{uri}\n{canonical_query_string}\n{canonical_headers_str}\n\n{signed_headers_str}\n{payload_hash}"
        
        # 构造待签名字符串
        algorithm = 'HMAC-SHA256'
        credential_scope = f"{date}/{self.region}/{self.service}/request"
        string_to_sign = f"{algorithm}\n{iso_timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        
        # 生成签名
        signing_key = self.get_sign_key(secret_key, date, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # 构造Authorization头
        authorization = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers_str}, Signature={signature}"
        
        return authorization

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

    def submit_task(self, access_key, secret_key, image_base64, aspect_ratio, prompt="", seed=-1):
        """提交视频生成任务"""
        # 构造请求参数
        query_params = {
            "Action": "CVSync2AsyncSubmitTask",
            "Version": self.api_version
        }
        
        # 构造请求体
        body_data = {
            "req_key": self.req_key,
            "binary_data_base64": [image_base64],
            "aspect_ratio": aspect_ratio
        }
        
        if prompt:
            body_data["prompt"] = prompt[:150]  # 限制最大长度
        
        if seed != -1:
            body_data["seed"] = seed
        
        payload = json.dumps(body_data, separators=(',', ':'))
        
        # 构造headers
        timestamp = datetime.datetime.utcnow()
        headers = {
            "Content-Type": "application/json",
            "Host": self.host,
            "X-Date": timestamp.strftime('%Y%m%dT%H%M%SZ')
        }
        
        # 生成Authorization
        authorization = self.get_authorization(
            access_key, secret_key, "POST", "/", query_params, headers, payload, timestamp
        )
        headers["Authorization"] = authorization
        
        # 发送请求
        url = f"https://{self.host}/" + "?" + urlencode(query_params)
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=30)
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

    def query_result(self, access_key, secret_key, task_id, max_retries=60, retry_interval=5):
        """查询任务结果"""
        # 构造请求参数
        query_params = {
            "Action": "CVSync2AsyncGetResult", 
            "Version": self.api_version
        }
        
        # 构造请求体
        body_data = {
            "req_key": self.req_key,
            "task_id": task_id
        }
        
        payload = json.dumps(body_data, separators=(',', ':'))
        
        for attempt in range(max_retries):
            try:
                # 构造headers
                timestamp = datetime.datetime.utcnow()
                headers = {
                    "Content-Type": "application/json",
                    "Host": self.host,
                    "X-Date": timestamp.strftime('%Y%m%dT%H%M%SZ')
                }
                
                # 生成Authorization
                authorization = self.get_authorization(
                    access_key, secret_key, "POST", "/", query_params, headers, payload, timestamp
                )
                headers["Authorization"] = authorization
                
                # 发送请求
                url = f"https://{self.host}/" + "?" + urlencode(query_params)
                response = requests.post(url, headers=headers, data=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"查询结果 (第{attempt+1}次): {result}")
                    
                    if result.get("code") == 10000:
                        data = result.get("data", {})
                        status = data.get("status", "")
                        
                        if status == "done":
                            video_url = data.get("video_url")
                            if video_url:
                                print(f"视频生成完成: {video_url}")
                                return video_url
                            else:
                                print("任务完成但未获取到视频URL")
                                return None
                        elif status == "failed":
                            print("任务失败")
                            return None
                        else:
                            print(f"任务进行中，状态: {status}")
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

    def download_video(self, video_url, filename_prefix):
        """下载视频文件"""
        try:
            response = requests.get(video_url, timeout=60)
            if response.status_code == 200:
                # 创建输出目录
                output_dir = os.path.join(folder_paths.output_directory)
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成文件名
                counter = 1
                while True:
                    filename = f"{filename_prefix}_{counter:04d}.mp4"
                    filepath = os.path.join(output_dir, filename)
                    if not os.path.exists(filepath):
                        break
                    counter += 1
                
                # 保存文件
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"视频已保存到: {filepath}")
                return filepath
            else:
                print(f"下载失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"下载异常: {str(e)}")
            return None

    def generate_video(self, access_key, secret_key, image, aspect_ratio, prompt="", seed=-1, filename_prefix="volcengine_i2v"):
        """主要的视频生成函数"""
        
        # 验证必需参数
        if not access_key or not secret_key:
            return "错误：请提供有效的AccessKey和SecretKey", ""
        
        try:
            print("开始处理图片...")
            # 转换图片为base64
            image_base64 = self.image_to_base64(image)
            print(f"图片转换完成，base64长度: {len(image_base64)}")
            
            print("提交视频生成任务...")
            # 提交任务
            task_id = self.submit_task(access_key, secret_key, image_base64, aspect_ratio, prompt, seed)
            
            if not task_id:
                return "错误：任务提交失败", ""
            
            print(f"任务提交成功，task_id: {task_id}")
            print("等待视频生成完成...")
            
            # 查询结果
            video_url = self.query_result(access_key, secret_key, task_id)
            
            if not video_url:
                return "错误：视频生成失败或超时", ""
            
            print("开始下载视频...")
            # 下载视频
            local_path = self.download_video(video_url, filename_prefix)
            
            if local_path:
                return video_url, local_path
            else:
                return video_url, "下载失败，但可通过URL访问"
                
        except Exception as e:
            error_msg = f"生成视频时发生错误: {str(e)}"
            print(error_msg)
            return error_msg, ""

# 节点映射
NODE_CLASS_MAPPINGS = {
    "VolcengineI2VS2Pro": VolcengineI2VS2Pro
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VolcengineI2VS2Pro": "Volcengine I2V S2.0Pro"
} 