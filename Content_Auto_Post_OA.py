import os
import requests
from Crawl_Text_From_Link import TimViec365ELe
from Create_Summarization import GeminiSummarizer, API_KEY, SITE_NAME
# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCESS_TOKEN_PATH = os.path.join(BASE_DIR, "access_token.txt")
OUTPUT_DOC_DIR = os.path.join(BASE_DIR, "OutputDoc")
FINAL_RESULT_PATH = os.path.join(OUTPUT_DOC_DIR, "final_result.txt")

# Ensure OutputDoc directory exists
os.makedirs(OUTPUT_DOC_DIR, exist_ok=True)

# Load ACCESS_TOKEN from access_token.txt
try:
    with open(ACCESS_TOKEN_PATH, "r", encoding="utf-8") as f:
        ACCESS_TOKEN = f.read().strip()
except FileNotFoundError:
    raise ValueError(f"Không tìm thấy file access_token.txt tại {ACCESS_TOKEN_PATH}")
if not ACCESS_TOKEN:
    raise ValueError("ACCESS_TOKEN không được tìm thấy trong access_token.txt")

URL = "https://openapi.zalo.me/v2.0/article/create"
URL_IMG = ""
STATUS = "hide"

FILE_CONTENT = FINAL_RESULT_PATH


def prepare_post_data():
    # 1. Crawl link pending
    scraper = TimViec365ELe()
    URL_POST, data = scraper.scrape_one()
    if not URL_POST or not data:
        return None, None, None, None, None, None

    URL_IMG = data.get('image', '')
    LOCAL_IMAGE_PATH = data.get('local_image_path', None) # Get local image path
    scraper.write_to_txt(data)

    # 2. Summarize
    summarizer = GeminiSummarizer(API_KEY, site_name=SITE_NAME)
    final_title, final_content = summarizer.process_document()
    print(f"link ảnh:{URL_IMG}, local path: {LOCAL_IMAGE_PATH}")
    return URL_POST, URL_IMG, LOCAL_IMAGE_PATH, FILE_CONTENT, STATUS, ACCESS_TOKEN, scraper # Return local image path


class OriginPost:
    def __init__(self, FILE_CONTENT, URL_IMG, LOCAL_IMAGE_PATH, STATUS, ACCESS_TOKEN):
        self.FILE_CONTENT = FILE_CONTENT
        self.URL_IMG = URL_IMG
        self.LOCAL_IMAGE_PATH = LOCAL_IMAGE_PATH # Store local image path
        self.STATUS = STATUS
        self.ACCESS_TOKEN = ACCESS_TOKEN
        self.combined_lines = None
    
    def get_combined_lines(self):
        return self.combined_lines
    
    def create_post(self):
        # Đọc file và xử lý nội dung
        with open(self.FILE_CONTENT, "r", encoding='utf-8') as file:
            lines = file.readlines()
        
        # Xử lý title
        title = "Default Title"
        article_summary = "Default Summary"
        content_start_index = 2
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.lower().startswith("title:"):
                title = line[len("title:"):].strip()
            elif line.lower().startswith("article_summary:"):
                article_summary = line[len("article_summary:"):].strip()
                break
        
        remaining_lines = lines[content_start_index:]

        combined_lines = "\n".join(
            remaining_lines
        )
        self.combined_lines = combined_lines
        with open (os.path.join(OUTPUT_DOC_DIR, "test_n.txt"), "w", encoding="utf-8") as f:
            f.write(combined_lines)
        body_blocks = [
            {
                "type": "text",
                "content": combined_lines
            }
        ]

        payload = {
            "type": "normal",
            "title": title,
            "author": "",
            "cover": {
                "cover_type": "photo",
                "photo_url": "https://cdn.pixabay.com/photo/2017/08/30/17/26/please-2697951_1280.jpg",
                "status": "show"
            },
            "description": article_summary,
            "body": body_blocks,
            "related_medias": [],
            "tracking_link": "https://example.com/tracking",
            "status": self.STATUS,
            "comment": "hide"
        }
        
        headers = {
            "access_token": self.ACCESS_TOKEN
        }

        try:
            response = requests.post(URL, headers=headers, json=payload, timeout=20)
        except requests.RequestException as e:
            print("‼ Lỗi kết nối:", e)
            return False

        # ✅ Chỉ coi 200 là hợp lệ
        if response.status_code == 200:
            try:
                resp = response.json()
            except ValueError:
                print("‼ Phản hồi không phải JSON:", response.text)
                return False

            print("Full response:", resp)
            if resp.get("error") == 0:
                token = resp.get("data", {}).get("token")
                if self.STATUS == "hide":
                    print("Tạo bài viết thành công (ẩn). Token:", token)
                else:
                    print("Tạo bài viết thành công (đã xuất bản). Token:", token)
                return True
            else:
                print("‼ API báo lỗi:", resp)
                return False

        # ❌ Bất kỳ status code nào khác 200 thì bỏ
        print(f"‼ Status code {response.status_code} không hợp lệ, bỏ qua.")
        return False
