import requests
import time
import random
import hashlib
import zlib
import re
import tempfile
import os

class HttpGetter:
    def __init__(self):
        pass
    
    def extract_url(self, text):
        """Text içinden URL'yi çıkarır"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, text)
        
        if urls:
            url = urls[0]
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return url
        return None
    
    def generate_delta_fingerprint(self, user_id="168556275"):
        """Delta fingerprint oluşturur"""
        data = f"delta_{user_id}_{int(time.time() / 86400)}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def roblox_http_get_async(self, url, user_id="168556275"):
        """Roblox HTTP GET request atar"""
        fingerprint = self.generate_delta_fingerprint(user_id)
        
        headers = {
            "Accept": "*/*",
            "Delta-User-Identifier": fingerprint,
            "Roblox-Id": str(user_id),
            "Cache-Control": "no-cache",
            "Delta-Fingerprint": fingerprint,
            "User-Agent": "Delta Android/2.0",
            "Accept-Encoding": "gzip, deflate"
        }
        
        trace_id = ''.join(random.choices('0123456789abcdef', k=32))
        parent_id = ''.join(random.choices('0123456789abcdef', k=16))
        headers["Traceparent"] = f"00-{trace_id}-{parent_id}-00"
        
        try:
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            
            raw_content = response.content
            
            content_encoding = response.headers.get('Content-Encoding', '').lower()
            
            if content_encoding == 'gzip':
                try:
                    decoded_content = zlib.decompress(raw_content, 16 + zlib.MAX_WBITS)
                except:
                    decoded_content = raw_content
            elif content_encoding == 'deflate':
                try:
                    decoded_content = zlib.decompress(raw_content)
                except:
                    decoded_content = raw_content
            else:
                decoded_content = raw_content
            
            body_text = decoded_content.decode('utf-8', errors='ignore')
            
            return {
                "StatusCode": response.status_code,
                "Success": response.status_code == 200,
                "Body": body_text
            }
        
        except Exception as e:
            return {
                "StatusCode": 0,
                "Success": False,
                "Body": f"Error: {str(e)}"
            }
    
    def get_from_text(self, text):
        """Text içinden URL'yi çıkarır ve GET request atar"""
        url = self.extract_url(text)
        
        if not url:
            return None, "URL bulunamadı. Lütfen geçerli bir URL sağlayın."
        
        print(f"URL tespit edildi: {url}")
        result = self.roblox_http_get_async(url)
        
        if result['Success']:
            return result['Body'], None
        else:
            return None, f"Hata: Status Code: {result['StatusCode']}\n{result['Body']}"
    
    def save_to_file(self, content, filename=None):
        """İçeriği dosyaya kaydeder"""
        if filename is None:
            filename = f"response_{int(time.time())}.txt"
        
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        
        return filename