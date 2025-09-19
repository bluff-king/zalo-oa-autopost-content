from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,os,platform
from Content_Auto_Post_OA import OriginPost, prepare_post_data, FINAL_RESULT_PATH # Import FINAL_RESULT_PATH

# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZALO_SESSION_DIR = os.path.join(BASE_DIR, "ZaloSession", "Zalo_OA")

if platform.system() == "Windows":
    DRIVER_PATH = r"C:\Zalo_OA\Chromedriver\chromedriver.exe"
else:
    # Linux / macOS (giả sử bạn cài vào /usr/local/bin/)
    DRIVER_PATH = "/usr/local/bin/chromedriver"
    
SESSION_PATH = ZALO_SESSION_DIR
ZALO_OA_URL = "https://oa.zalo.me/manage/oa"
XPATH_CHAT_TAB = '//*[@id="header_new"]/div/ul/li[2]/a'
XPATH_TAIKHOAN_OA = '//*[@id="DataTables_Table_0"]/tbody/tr/td[3]/a/strong'
CONTENT_XPATH = "//span[@class='text mt-4' and normalize-space()='Nội dung']"
DROPDOWN_BTN_XPATH = "//tbody/tr[1]//div[@class='btn_more']"
EDIT_BTN_XPATH = "//tbody/tr[1]//a[@class='maintenance']/li[normalize-space()='Sửa bài viết']"



# FILE_CONTENT= "./OutputDoc/final_result.txt"
# URL_IMG = "https://example.com/image.jpg"
# STATUS = "hide"
# ACCESS_TOKEN = "àdaf"
# URL_POST = "https://example.com/post-link"  

class AddCTA():
    """ Class for web scrapers using Selenium"""
    def __init__(self, file_content, url_img, local_image_path, status, access_token, url_post, headless=False):
        self.headless = headless
        self.driver = self.khoi_tao_driver()
        self.file_content = file_content
        self.url_img = url_img
        self.local_image_path = local_image_path # Store local image path
        self.status = status
        self.access_token = access_token
        self.url_post = url_post
        self.cover_path = local_image_path # Initialize cover_path with local_image_path
        self.combined_lines=None
        
    def get_cover_path(self):
        """Trả về đường dẫn ảnh cover nếu download thành công"""
        return self.cover_path
        
    def khoi_tao_driver(self):
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument(f"--user-data-dir={SESSION_PATH}")
        options.add_argument("--start-maximized")
        service = Service(executable_path=DRIVER_PATH)
        return webdriver.Chrome(service=service, options=options)
    
    def posting(self):
        '''Gọi tạo bài trước tiên rồi mới cập nhật CTA & img cover'''
        try:
            origin_post = OriginPost(self.file_content, self.url_img, self.local_image_path, self.status, self.access_token)
            self.combined_lines = origin_post.get_combined_lines()
            # Image is now downloaded during crawling, so no need to download here
            if not self.local_image_path and self.url_img:
                print("⚠️ Không có LOCAL_IMAGE_PATH, sẽ sử dụng URL_IMG để đăng bài.")
            elif not self.local_image_path:
                print("⚠️ Không có ảnh cover để đăng bài.")
            
            # Tạo bài viết
            status_post = origin_post.create_post()
            
            if status_post:
                print("✅ Bài viết đã được đăng thành công!")
                return True
            else:
                print(f"‼ Bài viết chưa được đăng!")
                return False
                
        except Exception as e:
            print(f"‼ Lỗi trong quá trình posting: {e}")
            return False
        
    def open_content_tab(self):
        """Đi vào tab Nội dung"""
        self.driver.get(ZALO_OA_URL)
        WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, XPATH_TAIKHOAN_OA))
        ).click()
        print("🟢 Đã chọn tài khoản OA")
        time.sleep(2)

        WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, XPATH_CHAT_TAB))
        ).click()
        print("🟢 Đã vào giao diện Chat của OA")
        time.sleep(2)

        content_btn = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, CONTENT_XPATH))
        )
        content_btn.click()
        print("🟢 Đã click tab 'Nội dung'")
        time.sleep(3)
    def edit_first_post(self):
        """Click nút ba chấm rồi chọn 'Sửa bài viết' của bài viết đầu tiên"""
        dropdown_btn = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, DROPDOWN_BTN_XPATH))
        )
        dropdown_btn.click()
        print("🟢 Đã click nút ba chấm của bài viết đầu tiên")
        time.sleep(1)

        edit_btn = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, EDIT_BTN_XPATH))
        )
        edit_btn.click()
        print("🟢 Đã chọn 'Sửa bài viết'")
        time.sleep(3)
        
    def setup_cta(self):
        # 1. Kiểm tra checkbox Call to action
        cta_input = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='squaredFour2']"))
        )

        if not cta_input.is_selected():
            # Nếu chưa tick thì click label
            cta_checkbox = self.driver.find_element(By.XPATH, "//label[@for='squaredFour2']")
            cta_checkbox.click()
            print("🟢 Đã tick 'Call to action'")
            time.sleep(1)
        else:
            print("ℹ️ 'Call to action' đã tick sẵn, bỏ qua bước này")

        # 2. Nhập nội dung CTA
        cta_textbox = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Nội dung']"))
        )
        cta_textbox.clear()
        cta_textbox.send_keys("Xem chi tiết bài viết")
        print("🟢 Đã nhập nội dung CTA")
        time.sleep(1)

        # 3. Nhập đường dẫn
        cta_linkbox = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Đường dẫn: https://...']"))
        )
        cta_linkbox.clear()
        cta_linkbox.send_keys(self.url_post)
        print(f"🟢 Đã nhập link bài viết: {self.url_post}")
        time.sleep(1)
        
    def update_cover_image(self):
        """Upload ảnh bìa từ self.cover_path lên giao diện Zalo OA"""
        cover_path = self.get_cover_path()
        
        if not cover_path:
            print("‼ Không có cover_path để upload!")
            return False

        try:
            # Bước 1: Click vào label_upload để mở modal upload (không phải imgDrop)
            label_upload = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "label_upload"))
            )

            self.driver.execute_script("arguments[0].scrollIntoView();", label_upload)
            time.sleep(1)

            label_upload.click()
            print("🟢 Đã click vào vùng label_upload (mở modal upload)")
            time.sleep(3)  # Đợi modal upload hiện ra

            # Bước 2: Tìm thẻ input file
            file_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "selectedFile"))
            )

            # Bước 3: Upload file
            absolute_path = os.path.abspath(cover_path)
            file_input.send_keys(absolute_path)
            print(f"🟢 Đã upload ảnh cover: {absolute_path}")
            time.sleep(5)

            # Bước 4: Tìm và click nút "Đồng ý"
            try:
                dong_y_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "cropImageBtn"))
                )

                if "disabled" not in dong_y_btn.get_attribute("class"):
                    dong_y_btn.click()
                    print("🟢 Đã click nút 'Đồng ý'")
                    time.sleep(3)
                else:
                    print("⚠️ Nút 'Đồng ý' bị disabled, đợi thêm...")
                    WebDriverWait(self.driver, 15).until(
                        lambda driver: "disabled" not in driver.find_element(By.ID, "cropImageBtn").get_attribute("class")
                    )
                    dong_y_btn.click()
                    print("🟢 Đã click nút 'Đồng ý' (sau khi đợi)")
                    time.sleep(3)

            except Exception as e:
                print(f"⚠️ Lỗi khi click nút 'Đồng ý': {e}")
                try:
                    dong_y_btn = self.driver.find_element(By.ID, "cropImageBtn")
                    self.driver.execute_script("arguments[0].click();", dong_y_btn)
                    print("🟢 Đã click nút 'Đồng ý' bằng JavaScript")
                    time.sleep(3)
                except:
                    print("❌ Không thể click nút 'Đồng ý'")
                    return False

            return True

        except Exception as e:
            print(f"‼ Lỗi khi upload ảnh cover: {e}")
            return False
        
    def update_editor_content(self, remained_content: str):
        """Thay nội dung bài viết trong CKEditor bằng remained_content (giữ xuống dòng)"""
        try:
            # 1. Switch vào iframe CKEditor
            editor_iframe = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.cke_wysiwyg_frame"))
            )
            self.driver.switch_to.frame(editor_iframe)

            # 2. Lấy body của editor
            editor_body = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body.cke_editable"))
            )

            # 3. Xóa nội dung cũ
            self.driver.execute_script("arguments[0].innerHTML = '';", editor_body)

            # 4. Ghi nội dung mới (chuyển \n thành <br><br> để giữ khoảng cách)
            html_content = remained_content.replace("\n", "<br><br>")
            self.driver.execute_script("arguments[0].innerHTML = arguments[1];", editor_body, html_content)

            print("🟢 Đã cập nhật nội dung bài viết trong CKEditor thành công!")
            time.sleep(5)

        except Exception as e:
            print(f"‼ Lỗi khi update content trong CKEditor: {e}")
        finally:
            # Quay về main document
            self.driver.switch_to.default_content()


    def update_post(self):
        """Cập nhật bài viết"""
        # Scroll xuống cuối trang để tìm nút "Cập nhật"
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        update_btn = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'btn-blue') and normalize-space()='Cập nhật']"))
        )
        update_btn.click()
        time.sleep(4)
    # ---------------- HÀM CHÍNH ----------------
    def add_link_cta(self):
        try:
            self.open_content_tab()
            self.edit_first_post()
            self.setup_cta()
            # Chỉ upload cover nếu có ảnh
            if self.get_cover_path():
                self.update_cover_image()
            else:
                print("⚠️ Bỏ qua bước upload cover vì không có ảnh")
            # --- Xử lý nội dung CKEditor ---
            if self.combined_lines and self.combined_lines.strip():
                content_to_update = self.combined_lines
                print("ℹ️ Sử dụng nội dung từ OriginPost để update CKEditor")
            else:
                try:
                    with open(FINAL_RESULT_PATH, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    # Bỏ 2 dòng đầu, lấy từ dòng 3 trở đi
                    content_to_update = "".join(lines[2:]).strip()
                    print("ℹ️ self.combined_lines trống → đã đọc nội dung từ final_result.txt")
                except Exception as e:
                    print(f"‼ Không thể đọc file final_result.txt: {e}")
                    content_to_update = ""

            if content_to_update:
                self.update_editor_content(content_to_update)
            else:
                print("⚠️ Không có nội dung nào để update vào CKEditor!")
                
            self.update_post()
            print("✅ Hoàn tất thêm CTA và update cover!")
            
        except Exception as e:
            print(f"‼ Lỗi trong quy trình add_link_cta: {e}")
        finally:
            # Tự động đóng trình duyệt sau khi hoàn tất
            print("ℹ️ Tự động đóng trình duyệt.")
            self.driver.quit()
    
def run_pipeline():
    URL_POST, URL_IMG, LOCAL_IMAGE_PATH, FILE_CONTENT, STATUS, ACCESS_TOKEN, scraper = prepare_post_data()
    if not URL_POST:
        print("No pending link to process.")
        return False

    do_cta = AddCTA(
        file_content=FILE_CONTENT,
        url_img=URL_IMG,
        local_image_path=LOCAL_IMAGE_PATH, # Pass local image path
        status=STATUS,
        access_token=ACCESS_TOKEN,
        url_post=URL_POST,
        headless=False
    )

    posting_status = do_cta.posting()
    
    if posting_status:
        do_cta.add_link_cta()
        scraper.mark_posted(URL_POST)
        return True
    else:
        print("Posting failed")
        # do_cta.driver.quit()
        return False
