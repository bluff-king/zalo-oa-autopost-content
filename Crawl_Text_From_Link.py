# Crawl_Text_From_Link.py
from abc import ABC, abstractmethod
import time, logging, random, re, json, os
import cloudscraper
from fake_useragent import UserAgent
from filelock import FileLock
import requests # Added for image downloading

# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_LINKS_DIR = os.path.join(BASE_DIR, "InputLinks")
OUTPUT_DOC_DIR = os.path.join(BASE_DIR, "OutputDoc")

# Ensure directories exist
os.makedirs(INPUT_LINKS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DOC_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseScraperEle(ABC):
    """
    Base abstract class cho tất cả web scrapers.
    """

    def __init__(self, links_file=os.path.join(INPUT_LINKS_DIR, "links.json")):
        self.links_file = links_file
        self.scraped_urls = set()

        # Khởi tạo cloudscraper
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

        # User agent rotator
        self.ua = UserAgent()
        self.update_headers()

    def update_headers(self):
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'
        }
        self.session.headers.update(headers)

    def smart_delay(self, min_delay=0.5, max_delay=1.5):
        """Delay nhẹ để tránh request quá nhanh"""
        time.sleep(random.uniform(min_delay, max_delay))

    def get_page(self, url, retries=3):
        for attempt in range(retries):
            try:
                self.smart_delay()
                self.update_headers()

                if hasattr(self, 'last_url') and self.last_url:
                    self.session.headers['Referer'] = self.last_url

                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    logger.info(f"✓ Successfully fetched: {url}")
                    self.last_url = url
                    return response
                elif response.status_code in (403, 429):
                    if attempt < retries - 1:
                        time.sleep(random.uniform(5, 15))
                else:
                    logger.warning(f"Status code: {response.status_code}")

            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(5, 10))

        logger.error(f"Link {url} lỗi, đã thử {retries} lần")
        return None

    def extract_clean_text(self, element):
        if not element:
            return ""
        text = element.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    def download_image(self, url_image, save_dir=OUTPUT_DOC_DIR):
        try:
            os.makedirs(save_dir, exist_ok=True)
            headers = {"User-Agent": "Mozilla/5.0"}  # giả lập browser
            resp = requests.get(url_image, headers=headers, stream=True, timeout=20)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type:
                logger.warning(f"‼ URL không trả về ảnh: {content_type}")
                logger.warning(f"Nội dung: {resp.text[:200]}")
                return False, None

            ext = "." + content_type.split("/")[-1]  # ví dụ image/jpeg → .jpeg
            local_path = os.path.join(save_dir, f"cover{ext}")

            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)

            logger.info(f"✅ Đã tải ảnh: {local_path}")
            return True, os.path.abspath(local_path)
        except Exception as e:
            logger.error(f"‼ Lỗi khi tải ảnh: {e}")
            return False, None

    # ---------------------------
    # JSON links handling
    # ---------------------------
    def load_links(self):
        """Lấy link đầu tiên pending và chuyển thành in_progress"""
        if not os.path.exists(self.links_file):
            logger.error(f"File not found: {self.links_file}")
            return []

        with FileLock(self.links_file + ".lock"):
            with open(self.links_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("status") == "pending":
                    logger.info(f"Found pending link: {entry['url']}")
                    entry["status"] = "in_progress"
                    with open(self.links_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    return [entry["url"]]
        logger.info("No pending links found.")
        return []

    def mark_posted(self, url):
        """Sau khi đăng bài thành công thì đổi status -> posted"""
        with FileLock(self.links_file + ".lock"):
            with open(self.links_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data:
                if entry["url"] == url:
                    entry["status"] = "posted"
                    entry["posted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    break

            with open(self.links_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Marked as posted: {url}")

    def mark_failed(self, url):
        """Đánh dấu link bị lỗi"""
        with FileLock(self.links_file + ".lock"):
            with open(self.links_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for entry in data:
                if entry["url"] == url:
                    entry["status"] = "failed"
                    entry["failed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    break

            with open(self.links_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Marked as failed: {url}")

    @abstractmethod
    def parse_post(self, url):
        pass

    @abstractmethod
    def get_title_selectors(self):
        pass

    @abstractmethod
    def get_sapo_selectors(self):
        pass

    @abstractmethod
    def get_content_selectors(self):
        pass

    # ---------------------------
    # Main scrape one link
    # ---------------------------
    
    def scrape_one(self):
        """
        Scrape 1 link đầu tiên có status pending (đã được set in_progress).
        Trả về tuple (url, dữ liệu scrape) hoặc (None, None) nếu không có link.
        """
        self.links = self.load_links()
        if not self.links:
            logger.error("No pending links found!")
            return None, None

        url = self.links[0]
        logger.info(f"Scraping link: {url}")

        post_data = self.parse_post(url)
        if not post_data:
            logger.warning(f"Failed to scrape: {url}, đánh dấu failed")
            self.mark_failed(url)
            return url, None

        logger.info(f"Scraping completed for: {url}")
        return url, post_data
    
    def extract_by_selectors(self, soup, selectors):
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    return elem.get('content', '').strip()
                elif elem.name == 'title':
                    return elem.get_text(strip=True)
                else:
                    return self.extract_clean_text(elem)
        return ""
    
    def extract_metadata(self, soup):
        """
        Template method để extract metadata
        """
        metadata = {
            'title': self.extract_by_selectors(soup, self.get_title_selectors()),
            'sapo': self.extract_by_selectors(soup, self.get_sapo_selectors()),
            'content': self.extract_by_selectors(soup, self.get_content_selectors())
        }
        return metadata
    

    
class TimViec365ELe(BaseScraperEle):
    def __init__(self):
        """
        Khởi tạo scraper với file links và cấu hình chung từ BaseScraperBS4.
        """
        super().__init__()
        
    def get_title_selectors(self):
        # Lấy từ thẻ <title> trong <head>
        return ['title']
    
    def get_sapo_selectors(self):
        return ['div.summary']
    
    def get_content_selectors(self):
        return ['div#footerNew']
    
    def parse_post(self, url):
        response = self.get_page(url)
        if not response:
            return None

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        metadata = self.extract_metadata(soup)

        # Lấy content riêng
        content = self.extract_by_selectors(soup, self.get_content_selectors())
        # Lấy ảnh đầu tiên trong figure.image
        first_img = ""
        img_elem = soup.select_one("figure.image img")
        local_image_path = None
        if img_elem and img_elem.get("src"):
            first_img = img_elem["src"].strip()
            success, path = self.download_image(first_img)
            if success:
                local_image_path = path
                logger.info(f"📸 Đã tải ảnh cover trong quá trình crawl: {local_image_path}")
            else:
                logger.warning(f"‼ Không thể tải ảnh cover từ URL: {first_img}")

        return {
            "url": url,
            "title": metadata.get("title", ""),
            "sapo": metadata.get("sapo", ""),
            "content": content,
            "image": first_img,
            "local_image_path": local_image_path # Add local image path to returned data
        }
        
    def write_to_txt(self, dic, output_file=os.path.join(OUTPUT_DOC_DIR, "t_long_document.txt")):
        """
        Ghi dữ liệu scrape được vào file txt.
        """
        if not dic:
            logger.warning("Không có dữ liệu để ghi file.")
            return

        # Đảm bảo thư mục OutputDoc tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"{dic.get('title', '')}\n")
            f.write(f"{dic.get('sapo', '')}\n")
            f.write(dic.get("content", "") + "\n")

        logger.info(f"Đã ghi dữ liệu vào file: {output_file}")

# scraper = TimViec365ELe()
# url, data = scraper.scrape_one()
# print(data)
# if data:
#     scraper.write_to_txt(data)
    # scraper.mark_posted(url)
