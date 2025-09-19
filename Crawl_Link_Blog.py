from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def crawl_links():
    """
    Crawls the blog page and returns a list of article URLs,
    oldest first (from the current page).
    """
    # Khởi tạo Chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # chạy ngầm (không mở cửa sổ trình duyệt)
    driver = webdriver.Chrome(options=options)
    
    links = []
    try:
        # Truy cập trang
        url = "https://timviec365.vn/blog"
        driver.get(url)
        time.sleep(3)  # chờ load trang

        # Tìm tất cả các div.bvgd
        bv_gd_divs = driver.find_elements(By.CSS_SELECTOR, "div.bvgd")

        for bv in bv_gd_divs:
            # Trong mỗi div.bvgd, tìm tab_blog
            tab_blogs = bv.find_elements(By.CSS_SELECTOR, "div.tab_blog")

            for tab in tab_blogs:
                # Lấy link từ thẻ a
                a_tag = tab.find_element(By.TAG_NAME, "a")
                link = a_tag.get_attribute("href")
                if link:
                    links.append(link)
    finally:
        driver.quit()
    
    # Đảo ngược danh sách để xử lý link cũ trước
    links.reverse()
    return links

if __name__ == '__main__':
    crawled_links = crawl_links()
    print(f"Found {len(crawled_links)} links (oldest first):")
    for link in crawled_links:
        print(link)
