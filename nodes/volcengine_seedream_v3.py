import json
import base64
import datetime
import hashlib
import hmac
import requests
import torch
import numpy as np
from PIL import Image
import io
import os


class VolcengineSeeDreamV3Node:
    """
    ComfyUI custom node for Volcengine SeeDream V3 text-to-image API
    """
    
    def __init__(self):
        self.method = 'POST'
        self.host = 'visual.volcengineapi.com'
        self.region = 'cn-north-1'
        self.endpoint = 'https://visual.volcengineapi.com'
        self.service = 'cv'
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "access_key": ("STRING", {"default": "", "multiline": False}),
                "secret_key": ("STRING", {"default": "", "multiline": False}),
                "prompt": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "use_pre_llm": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "guidance_scale": ("FLOAT", {"default": 2.5, "min": 1.0, "max": 10.0, "step": 0.1}),
                "aspect_ratio": (["1:1", "4:3", "3:2", "16:9", "9:16", "21:9"], {"default": "1:1"}),
                "return_url": ("BOOLEAN", {"default": True}),
                "filename_prefix": ("STRING", {"default": "seedream", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "image_url")
    FUNCTION = "generate_image"
    CATEGORY = "JM-Volcengine-API/Seedream"
    
    def sign(self, key, msg):
        """Generate HMAC signature"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    def get_signature_key(self, key, date_stamp, region_name, service_name):
        """Generate signature key"""
        k_date = self.sign(key.encode('utf-8'), date_stamp)
        k_region = self.sign(k_date, region_name)
        k_service = self.sign(k_region, service_name)
        k_signing = self.sign(k_service, 'request')
        return k_signing
    
    def format_query(self, parameters):
        """Format query parameters"""
        request_parameters_init = ''
        for key in sorted(parameters):
            request_parameters_init += key + '=' + parameters[key] + '&'
        request_parameters = request_parameters_init[:-1]
        return request_parameters
    
    def sign_v4_request(self, access_key, secret_key, service, req_query, req_body):
        """Sign request using AWS V4 signature"""
        if access_key is None or secret_key is None:
            raise ValueError('Access key and secret key are required.')
        
        t = datetime.datetime.utcnow()
        current_date = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = t.strftime('%Y%m%d')
        
        canonical_uri = '/'
        canonical_querystring = req_query
        signed_headers = 'content-type;host;x-content-sha256;x-date'
        payload_hash = hashlib.sha256(req_body.encode('utf-8')).hexdigest()
        content_type = 'application/json'
        
        canonical_headers = (
            f'content-type:{content_type}\n'
            f'host:{self.host}\n'
            f'x-content-sha256:{payload_hash}\n'
            f'x-date:{current_date}\n'
        )
        
        canonical_request = (
            f'{self.method}\n{canonical_uri}\n{canonical_querystring}\n'
            f'{canonical_headers}\n{signed_headers}\n{payload_hash}'
        )
        
        algorithm = 'HMAC-SHA256'
        credential_scope = f'{datestamp}/{self.region}/{service}/request'
        string_to_sign = (
            f'{algorithm}\n{current_date}\n{credential_scope}\n'
            f'{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
        )
        
        signing_key = self.get_signature_key(secret_key, datestamp, self.region, service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        authorization_header = (
            f'{algorithm} Credential={access_key}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )
        
        headers = {
            'X-Date': current_date,
            'Authorization': authorization_header,
            'X-Content-Sha256': payload_hash,
            'Content-Type': content_type
        }
        
        return headers
    
    def download_image_from_url(self, url):
        """Download image from URL and convert to tensor"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(image).astype(np.float32) / 255.0
            
            # Convert to tensor with batch dimension
            image_tensor = torch.from_numpy(image_array)[None,]
            
            return image_tensor
            
        except Exception as e:
            raise Exception(f"Failed to download image from URL: {str(e)}")
    
    def decode_base64_image(self, base64_string):
        """Decode base64 image string to tensor"""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(image).astype(np.float32) / 255.0
            
            # Convert to tensor with batch dimension
            image_tensor = torch.from_numpy(image_array)[None,]
            
            return image_tensor
            
        except Exception as e:
            raise Exception(f"Failed to decode base64 image: {str(e)}")
    
    def get_resolution_from_aspect_ratio(self, aspect_ratio):
        """Get width and height from aspect ratio (1.5K resolution)"""
        resolution_map = {
            "1:1": (1536, 1536),
            "4:3": (1472, 1104),
            "3:2": (1584, 1056),
            "16:9": (1664, 936),
            "9:16": (936, 1664),
            "21:9": (2016, 864)
        }
        return resolution_map.get(aspect_ratio, (1536, 1536))
    
    def get_unique_filename(self, prefix, output_dir="output", extension="png"):
        """Generate unique filename with auto-incrementing number"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        counter = 1
        while True:
            filename = f"{prefix}_{counter:04d}.{extension}"
            filepath = os.path.join(output_dir, filename)
            if not os.path.exists(filepath):
                return filepath, filename
            counter += 1
    
    def save_image_from_tensor(self, image_tensor, filename_prefix):
        """Save image tensor to local file and return filepath"""
        try:
            # Convert tensor back to PIL Image
            image_array = image_tensor.squeeze(0).cpu().numpy()
            image_array = (image_array * 255).astype(np.uint8)
            image = Image.fromarray(image_array)
            
            # Get unique filename
            filepath, filename = self.get_unique_filename(filename_prefix)
            
            # Save image
            image.save(filepath)
            print(f"Image saved to: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"Failed to save image: {str(e)}")
            return ""
    
    def generate_image(self, access_key, secret_key, prompt, use_pre_llm=False, 
                      seed=-1, guidance_scale=2.5, aspect_ratio="1:1", return_url=True, filename_prefix="seedream"):
        """
        Generate image using Volcengine SeeDream V3 API
        """
        try:
            # Validate inputs
            if not access_key or not secret_key:
                raise ValueError("Access key and secret key are required")
            
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            # Get resolution from aspect ratio
            width, height = self.get_resolution_from_aspect_ratio(aspect_ratio)
            
            # Prepare query parameters
            query_params = {
                'Action': 'CVProcess',
                'Version': '2022-08-31',
            }
            formatted_query = self.format_query(query_params)
            
            # Prepare body parameters
            body_params = {
                "req_key": "high_aes_general_v30l_zt2i",
                "prompt": prompt,
                "use_pre_llm": use_pre_llm,
                "seed": seed,
                "scale": guidance_scale,
                "width": width,
                "height": height,
                "return_url": return_url
            }
            formatted_body = json.dumps(body_params)
            
            # Sign the request
            headers = self.sign_v4_request(access_key, secret_key, self.service, 
                                         formatted_query, formatted_body)
            
            # Make the request
            request_url = f"{self.endpoint}?{formatted_query}"
            
            print(f"Making request to Volcengine SeeDream V3 API...")
            print(f"Resolution: {aspect_ratio} ({width}x{height})")
            print(f"Prompt: {prompt[:100]}...")
            
            response = requests.post(request_url, headers=headers, data=formatted_body, timeout=60)
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
            # Parse response
            result = response.json()
            print(f"API Response: {result}")
            
            # Check for API errors
            if result.get('code') != 10000:
                error_message = result.get('message', 'Unknown error')
                raise Exception(f"API Error (code: {result.get('code')}): {error_message}")
            
            # Extract image data
            if 'data' not in result:
                raise Exception("No data field in API response")
            
            data = result['data']
            
            # Handle URL or base64 response
            image_url = ""
            if return_url and 'image_urls' in data and data['image_urls']:
                # Download image from URL
                image_url = data['image_urls'][0]  # Get first image URL
                print(f"Downloading image from URL: {image_url}")
                image_tensor = self.download_image_from_url(image_url)
                
            elif 'binary_data_base64' in data and data['binary_data_base64']:
                # Decode base64 image
                print("Decoding base64 image data...")
                base64_data = data['binary_data_base64'][0] if isinstance(data['binary_data_base64'], list) else data['binary_data_base64']
                image_tensor = self.decode_base64_image(base64_data)
                image_url = "base64_image"  # Indicate this is from base64 data
                
            else:
                raise Exception("No valid image data found in API response")
            
            # Save image to local file
            saved_filepath = self.save_image_from_tensor(image_tensor, filename_prefix)
            
            print("Image generated successfully!")
            print(f"Image saved as: {saved_filepath}")
            return (image_tensor, image_url)
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            # Return a blank image in case of error
            blank_image = torch.zeros((1, height, width, 3), dtype=torch.float32)
            return (blank_image, "") 