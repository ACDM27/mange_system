"""
Test script for certificate recognition module
Usage: python test_certificate_recognition.py <path_to_certificate_image>
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from services.certificate_recognition import certificate_recognition_service
from config import settings


async def test_single_recognition(image_path: str):
    """Test single certificate recognition"""
    print(f"🔍 Testing certificate recognition for: {image_path}")
    print(f"📝 Using model: {settings.QWEN_MODEL_NAME}")
    print(f"🔑 API Key configured: {'Yes' if settings.QWEN_API_KEY else 'No'}")
    print("-" * 60)
    
    if not settings.QWEN_API_KEY:
        print("❌ Error: QWEN_API_KEY not configured in .env file")
        return
    
    # Check if file exists
    if not Path(image_path).exists():
        print(f"❌ Error: File not found: {image_path}")
        return
    
    try:
        # Recognize certificate
        print("⏳ Recognizing certificate...")
        result = await certificate_recognition_service.recognize_certificate(image_path)
        
        # Validate result
        validated_result = certificate_recognition_service.validate_recognition_result(result)
        
        print("\n📊 Recognition Result:")
        print("=" * 60)
        
        if validated_result["success"]:
            print("✅ Recognition successful!\n")
            data = validated_result["data"]
            
            print(f"📜 证书名称: {data.get('certificate_name')}")
            print(f"👤 获得者: {data.get('recipient_name')}")
            print(f"🏛️  颁发单位: {data.get('issuing_organization')}")
            print(f"📅 颁发日期: {data.get('issue_date')}")
            print(f"🔢 证书编号: {data.get('certificate_number')}")
            print(f"🏆 奖项等级: {data.get('award_level')}")
            print(f"📂 获奖类别: {data.get('category')}")
            print(f"ℹ️  其他信息: {data.get('additional_info')}")
            print(f"\n🤖 模型: {data.get('model_used')}")
            print(f"⏰ 识别时间: {data.get('recognition_time')}")
            print(f"💯 置信度: {data.get('confidence')}")
        else:
            print(f"❌ Recognition failed: {validated_result.get('error')}")
            
        print("\n" + "=" * 60)
        
        # Print raw response if needed for debugging
        if "--verbose" in sys.argv:
            print("\n📝 Raw Response:")
            print(result.get("raw_response", "N/A"))
        
    except Exception as e:
        print(f"❌ Error during recognition: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_health_check():
    """Test service health check"""
    print("🏥 Testing service health...")
    print("-" * 60)
    
    is_configured = bool(settings.QWEN_API_KEY and settings.QWEN_API_KEY != "")
    
    print(f"✅ Configuration Status: {'Ready' if is_configured else 'Not Configured'}")
    print(f"📝 Model: {settings.QWEN_MODEL_NAME}")
    print(f"🌐 API URL: {settings.QWEN_API_URL}")
    print(f"🔑 API Key: {'***' + settings.QWEN_API_KEY[-8:] if settings.QWEN_API_KEY else 'Not set'}")
    print("-" * 60)


def print_usage():
    """Print usage instructions"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Certificate Recognition Module - Test Script         ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python test_certificate_recognition.py <image_path> [--verbose]
    python test_certificate_recognition.py --health

Arguments:
    image_path    Path to the certificate image file
    --verbose     Show detailed output including raw API response
    --health      Check service configuration and health

Examples:
    python test_certificate_recognition.py certificate.jpg
    python test_certificate_recognition.py ./uploads/cert.png --verbose
    python test_certificate_recognition.py --health

Supported Image Formats:
    JPG, JPEG, PNG, BMP, GIF

Configuration:
    Make sure to set QWEN_API_KEY in .env file before running.
    """)


async def main():
    """Main function"""
    if len(sys.argv) < 2 or "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        return
    
    if "--health" in sys.argv:
        await test_health_check()
        return
    
    image_path = sys.argv[1]
    await test_single_recognition(image_path)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║    🎓 Student System - Certificate Recognition Test 🎓      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
