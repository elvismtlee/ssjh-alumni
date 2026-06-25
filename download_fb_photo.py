import os, json, base64, requests, re, sys
import win32crypt
import win32file
import win32con
import ctypes
from Crypto.Cipher import AES

def copy_locked_file(src, dst):
    """用 win32 API 在檔案被鎖定時複製"""
    handle = win32file.CreateFile(
        src,
        win32con.GENERIC_READ,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        0,
        None
    )
    data = b''
    while True:
        hr, chunk = win32file.ReadFile(handle, 1024*1024)
        if not chunk:
            break
        data += chunk
    win32file.CloseHandle(handle)
    with open(dst, 'wb') as f:
        f.write(data)

def get_edge_cookies():
    import sqlite3, tempfile
    cookies_path = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies')
    tmp = os.path.join(tempfile.gettempdir(), 'edge_cookies_tmp.db')
    copy_locked_file(cookies_path, tmp)

    local_state_path = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State')
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)

    enc_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
    key = win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)[1]

    conn = sqlite3.connect(tmp)
    cursor = conn.cursor()
    cursor.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%facebook%'")
    cookies = {}
    for name, enc_val in cursor.fetchall():
        try:
            iv = enc_val[3:15]
            payload = enc_val[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16].decode('utf-8', errors='ignore')
            cookies[name] = decrypted
        except:
            pass
    conn.close()
    os.remove(tmp)
    return cookies

def download_fb_photo(fbid, output_path):
    print(f'讀取 Edge cookies...')
    cookies = get_edge_cookies()
    print(f'取得 {len(cookies)} 個 cookie')

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-TW,zh;q=0.9',
    })
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.facebook.com')

    url = f'https://www.facebook.com/photo/?fbid={fbid}'
    print(f'抓取頁面：{url}')
    resp = session.get(url)
    print(f'回應狀態：{resp.status_code}，大小：{len(resp.text)}')

    # 多種 pattern 找圖片 CDN URL
    patterns = [
        r'"uri"\s*:\s*"(https://[^"]*scontent[^"]*\.jpg[^"]*)"',
        r'(https://scontent[^\s"\\]+\.jpg[^\s"\\]*)',
        r'"image"\s*:\s*\{[^}]*"uri"\s*:\s*"([^"]+)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, resp.text)
        if match:
            img_url = match.group(1).replace('\\u0026', '&').replace('&amp;', '&').replace('\\/', '/')
            print(f'找到圖片 URL: {img_url[:100]}...')
            img_resp = session.get(img_url, stream=True)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in img_resp.iter_content(8192):
                    f.write(chunk)
            size = os.path.getsize(output_path)
            print(f'已儲存：{output_path} ({size:,} bytes)')
            return True

    print('找不到圖片 URL，儲存頁面供除錯...')
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(resp.text[:50000])
    return False

if __name__ == '__main__':
    fbid = sys.argv[1] if len(sys.argv) > 1 else '988948227127494'
    output = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\elvis\ssjh-alumni\images\photo1.jpg'
    download_fb_photo(fbid, output)
