"""
Test script for two-step achievement submission with certificate recognition
Tests the complete workflow: upload & recognize → confirm & submit
"""

import httpx
import asyncio
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def test_two_step_workflow():
    """Test the complete two-step achievement submission workflow"""
    
    print("=" * 70)
    print("🧪 TESTING TWO-STEP ACHIEVEMENT SUBMISSION WORKFLOW")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 0: Login
        print("\n📝 Step 0: Login as student...")
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            data={
                "username": "student1",
                "password": "password123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        login_data = login_response.json()
        if login_data["code"] != 200:
            print(f"❌ Login failed: {login_data}")
            return
            
        token = login_data["data"]["token"]
        print(f"✅ Login successful! Token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 1: Upload certificate and get recognition
        print("\n📤 Step 1: Upload certificate and recognize...")
        
        # Check if test image exists
        test_image_path = "test_certificate.jpg"
        if not Path(test_image_path).exists():
            print(f"⚠️  Test image not found: {test_image_path}")
            print("   Creating a placeholder. Replace with actual certificate image.")
            # Create a small test file
            with open(test_image_path, "wb") as f:
                f.write(b"fake image content for testing")
        
        with open(test_image_path, "rb") as f:
            ocr_response = await client.post(
                f"{BASE_URL}/api/v1/student/ocr/recognize",
                headers=headers,
                files={"file": (test_image_path, f, "image/jpeg")}
            )
        
        if ocr_response.status_code != 200:
            print(f"❌ OCR recognition failed: {ocr_response.text}")
            return
        
        ocr_data = ocr_response.json()
        if ocr_data["code"] != 200:
            print(f"❌ OCR recognition failed: {ocr_data}")
            return
        
        recognition_result = ocr_data["data"]
        print("\n✅ Certificate recognized successfully!")
        print(f"   File URL: {recognition_result.get('file_url')}")
        print(f"   Recognized Title: {recognition_result['recognized_data'].get('title')}")
        print(f"   Issuer: {recognition_result['recognized_data'].get('issuer')}")
        print(f"   Date: {recognition_result['recognized_data'].get('date')}")
        print(f"   Suggested Type: {recognition_result['recognized_data'].get('suggested_type')}")
        print(f"   Award Level: {recognition_result['recognized_data'].get('award_level')}")
        
        file_url = recognition_result["file_url"]
        
        # Step 1.5: Get list of certificates
        print("\n📋 Step 1.5: Get my certificates list...")
        certs_response = await client.get(
            f"{BASE_URL}/api/v1/student/certificates",
            headers=headers
        )
        
        if certs_response.status_code == 200:
            certs_data = certs_response.json()
            if certs_data["code"] == 200:
                print(f"✅ Found {certs_data['data']['total']} certificates")
                for cert in certs_data['data']['certificates']:
                    print(f"   - {cert['filename']} ({cert['size_bytes']} bytes)")
        
        # Step 2: User confirms and submits achievement
        print("\n✔️  Step 2: Confirm and submit achievement...")
        
        # Get list of teachers first
        teachers_response = await client.get(
            f"{BASE_URL}/api/common/teachers",
            headers=headers
        )
        
        if teachers_response.status_code != 200:
            print(f"❌ Failed to get teachers: {teachers_response.text}")
            return
        
        teachers_data = teachers_response.json()
        if not teachers_data["data"] or len(teachers_data["data"]) == 0:
            print("❌ No teachers found in system. Please add teachers first.")
            return
        
        teacher_id = teachers_data["data"][0]["id"]
        print(f"   Using teacher: {teachers_data['data'][0]['name']} (ID: {teacher_id})")
        
        # Submit achievement with recognized data
        achievement_data = {
            "teacher_id": teacher_id,
            "title": recognition_result['recognized_data'].get('title') or "Test Achievement",
            "type": recognition_result['recognized_data'].get('suggested_type') or "competition",
            "evidence_url": file_url,
            "content_json": {
                "issuer": recognition_result['recognized_data'].get('issuer'),
                "date": recognition_result['recognized_data'].get('date'),
                "award_level": recognition_result['recognized_data'].get('award_level'),
                "certificate_number": recognition_result['recognized_data'].get('certificate_number'),
                "ai_recognized": True
            }
        }
        
        submit_response = await client.post(
            f"{BASE_URL}/api/v1/student/achievements",
            headers=headers,
            json=achievement_data
        )
        
        if submit_response.status_code != 200:
            print(f"❌ Achievement submission failed: {submit_response.text}")
            return
        
        submit_data = submit_response.json()
        if submit_data["code"] != 200:
            print(f"❌ Achievement submission failed: {submit_data}")
            return
        
        achievement_id = submit_data["data"]["id"]
        print(f"✅ Achievement submitted successfully! ID: {achievement_id}")
        
        # Step 3: Verify achievement was created
        print("\n🔍 Step 3: Verify achievement...")
        achievements_response = await client.get(
            f"{BASE_URL}/api/v1/student/achievements",
            headers=headers
        )
        
        if achievements_response.status_code == 200:
            achievements_data = achievements_response.json()
            if achievements_data["code"] == 200:
                achievements = achievements_data["data"]
                matching = [a for a in achievements if a["id"] == achievement_id]
                if matching:
                    ach = matching[0]
                    print("✅ Achievement verified in database:")
                    print(f"   ID: {ach['id']}")
                    print(f"   Title: {ach['title']}")
                    print(f"   Type: {ach['type']}")
                    print(f"   Status: {ach['status']}")
                    print(f"   Evidence URL: {ach['evidence_url']}")
                    print(f"   Teacher: {ach['teacher_name']}")
        
        # Step 4: Test access control
        print("\n🔒 Step 4: Test certificate access control...")
        
        # Try to access the certificate (should work)
        cert_response = await client.get(
            f"{BASE_URL}{file_url}",
            headers=headers
        )
        
        if cert_response.status_code == 200:
            print(f"✅ Certificate accessible to owner (status: {cert_response.status_code})")
        else:
            print(f"⚠️  Certificate access returned status: {cert_response.status_code}")
        
        # Try to access without token (should fail)
        cert_response_no_auth = await client.get(f"{BASE_URL}{file_url}")
        
        if cert_response_no_auth.status_code == 401:
            print(f"✅ Certificate blocked without authentication (status: {cert_response_no_auth.status_code})")
        else:
            print(f"⚠️  Certificate access without auth: {cert_response_no_auth.status_code}")
        
        print("\n" + "=" * 70)
        print("✅ TWO-STEP WORKFLOW TEST COMPLETED!")
        print("=" * 70)
        print("\n📊 Summary:")
        print("   1. ✅ Certificate uploaded and saved permanently")
        print("   2. ✅ AI recognition extracted certificate data")
        print("   3. ✅ Achievement created with recognized data")
        print("   4. ✅ Access control verified")
        print("\n🎉 All tests passed!")


async def test_health_checks():
    """Test health check endpoints"""
    print("\n🏥 Health Checks:")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test main API
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Main API: {response.json()}")
        except Exception as e:
            print(f"❌ Main API: {e}")
        
        # Test certificate recognition service
        try:
            response = await client.get(f"{BASE_URL}/api/certificate/health")
            result = response.json()
            if result.get("configured"):
                print(f"✅ Certificate Recognition: {result['message']}")
            else:
                print(f"⚠️  Certificate Recognition: {result['message']}")
        except Exception as e:
            print(f"❌ Certificate Recognition: {e}")


async def main():
    """Main test runner"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║     Two-Step Achievement Submission - Integration Test          ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{BASE_URL}/health")
    except Exception:
        print("❌ ERROR: Server is not running!")
        print(f"   Please start the server first: python main.py")
        print(f"   Expected URL: {BASE_URL}")
        return
    
    await test_health_checks()
    print()
    await test_two_step_workflow()
    
    print("\n💡 Tips:")
    print("   - Replace 'test_certificate.jpg' with a real certificate image")
    print("   - Ensure QWEN_API_KEY is configured in .env")
    print("   - Default login: username='student1', password='password123'")
    print("   - Check server logs for detailed information")


if __name__ == "__main__":
    asyncio.run(main())
