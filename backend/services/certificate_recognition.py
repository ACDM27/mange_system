"""
Certificate Recognition Service
Uses Alibaba Cloud Bailian (Qwen-plus) to recognize and extract information from achievement certificates
"""

import base64
import json
from typing import Dict, Optional
from datetime import datetime
import httpx
from config import settings


class CertificateRecognitionService:
    """Service for recognizing and extracting information from certificates using AI"""
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.model_name = settings.QWEN_MODEL_NAME
        self.api_url = settings.QWEN_API_URL
        
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image file to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def recognize_certificate(self, image_path: str) -> Dict:
        """
        Recognize certificate and extract structured information
        
        Args:
            image_path: Path to the certificate image
            
        Returns:
            Dictionary containing extracted certificate information
        """
        try:
            # Encode image to base64
            image_base64 = self.encode_image_to_base64(image_path)
            
            # Prepare the prompt for certificate recognition
            prompt = """请识别这张获奖证书/成果证书，并提取以下信息：
1. 证书名称/奖项名称
2. 获得者姓名
3. 颁发单位/组织
4. 获奖时间/颁发日期
5. 证书编号（如果有）
6. 奖项等级（如：一等奖、二等奖、三等奖等）
7. 获奖类别（如：学术竞赛、科技创新、文体活动等）
8. 其他重要信息

请以JSON格式返回结果，格式如下：
{
    "certificate_name": "证书/奖项名称",
    "recipient_name": "获得者姓名",
    "issuing_organization": "颁发单位",
    "issue_date": "YYYY-MM-DD",
    "certificate_number": "证书编号（如果有）",
    "award_level": "奖项等级",
    "category": "获奖类别",
    "additional_info": "其他重要信息"
}

如果某个字段无法识别，请使用null。"""
            
            # Call Qwen API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": f"data:image/jpeg;base64,{image_base64}"
                                },
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract the response text
                if "output" in result and "choices" in result["output"]:
                    content = result["output"]["choices"][0]["message"]["content"]
                    
                    # Try to parse JSON from the response
                    # The model might return JSON wrapped in markdown code blocks
                    if "```json" in content:
                        json_start = content.find("```json") + 7
                        json_end = content.find("```", json_start)
                        content = content[json_start:json_end].strip()
                    elif "```" in content:
                        json_start = content.find("```") + 3
                        json_end = content.find("```", json_start)
                        content = content[json_start:json_end].strip()
                    
                    certificate_data = json.loads(content)
                    
                    # Add metadata
                    certificate_data["recognition_time"] = datetime.utcnow().isoformat()
                    certificate_data["model_used"] = self.model_name
                    certificate_data["confidence"] = "high"  # Can be enhanced with actual confidence scores
                    
                    return {
                        "success": True,
                        "data": certificate_data,
                        "raw_response": content
                    }
                else:
                    return {
                        "success": False,
                        "error": "Unexpected response format from API",
                        "raw_response": result
                    }
                    
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON response: {str(e)}",
                "raw_response": content if 'content' in locals() else None
            }
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def batch_recognize_certificates(self, image_paths: list[str]) -> list[Dict]:
        """
        Batch recognize multiple certificates
        
        Args:
            image_paths: List of paths to certificate images
            
        Returns:
            List of dictionaries containing extracted information for each certificate
        """
        results = []
        for image_path in image_paths:
            result = await self.recognize_certificate(image_path)
            results.append(result)
        return results
    
    def validate_recognition_result(self, result: Dict) -> Dict:
        """
        Validate and clean the recognition result
        
        Args:
            result: Recognition result dictionary
            
        Returns:
            Validated and cleaned result
        """
        if not result.get("success"):
            return result
        
        data = result.get("data", {})
        
        # Validate required fields
        required_fields = ["certificate_name", "recipient_name", "issuing_organization"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "data": data
            }
        
        # Clean and normalize data
        cleaned_data = {
            "certificate_name": data.get("certificate_name", "").strip(),
            "recipient_name": data.get("recipient_name", "").strip(),
            "issuing_organization": data.get("issuing_organization", "").strip(),
            "issue_date": data.get("issue_date"),
            "certificate_number": data.get("certificate_number"),
            "award_level": data.get("award_level"),
            "category": data.get("category"),
            "additional_info": data.get("additional_info"),
            "recognition_time": data.get("recognition_time"),
            "model_used": data.get("model_used"),
            "confidence": data.get("confidence")
        }
        
        return {
            "success": True,
            "data": cleaned_data
        }


# Create a singleton instance
certificate_recognition_service = CertificateRecognitionService()
