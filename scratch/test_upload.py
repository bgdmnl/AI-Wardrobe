import time
import httpx
import json
from io import BytesIO
from PIL import Image

def main():
    backend_url = "http://localhost:8000"
    print("Creating mock image...")
    
    # Create 100x100 white square image
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    print("Uploading image to backend...")
    files = {
        'file': ('red_tshirt.jpg', img_byte_arr, 'image/jpeg')
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(f"{backend_url}/api/items/upload", files=files)
            response.raise_for_status()
            data = response.json()
            print("Upload Response:")
            print(json.dumps(data, indent=2))
            
            item = data.get("item", {})
            item_id = item.get("id")
            status = item.get("status")
            print(f"Uploaded successfully. Item ID: {item_id}, Initial Status: {status}")
            
            print("\nWaiting for background processing (simulated local worker)...")
            for i in range(5):
                time.sleep(1.0)
                status_resp = client.get(f"{backend_url}/api/items/{item_id}")
                status_resp.raise_for_status()
                item_data = status_resp.json()
                current_status = item_data.get("status")
                print(f"Check {i+1}: Status = {current_status}")
                if current_status in ["completed", "error"]:
                    print("Processing finished!")
                    print(json.dumps(item_data, indent=2))
                    break
                
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
