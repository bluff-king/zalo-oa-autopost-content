import google.generativeai as genai
from typing import List
from dotenv import load_dotenv
import os, math
import warnings
from typing import Tuple
warnings.filterwarnings("ignore")

# --- Path Configurations ---
# Base directory for environment variables and output documents
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_ENV_PATH = os.path.join(BASE_DIR, "key.env")
OUTPUT_DOC_DIR = os.path.join(BASE_DIR, "OutputDoc")

# Ensure OutputDoc directory exists
os.makedirs(OUTPUT_DOC_DIR, exist_ok=True)

# Specific file paths
T_LONG_DOCUMENT_PATH = os.path.join(OUTPUT_DOC_DIR, "t_long_document.txt")
T_SUM_PATH = os.path.join(OUTPUT_DOC_DIR, "t_sum.txt")
T_SAMPLE_PATH = os.path.join(OUTPUT_DOC_DIR, "t_sample.txt")
FINAL_RESULT_PATH = os.path.join(OUTPUT_DOC_DIR, "final_result.txt")

# --- API Key and Site Name ---
load_dotenv(KEY_ENV_PATH)
API_KEY=os.getenv("GEMINI_API_KEY")
SITE_NAME = "timviec365.vn"

class GeminiSummarizer:
    def __init__(self, api_key=API_KEY, model_name: str = 'gemini-2.0-flash', site_name: str = "timviec365.vn"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.site_name = site_name
        
    def post_process(self, text):
        return text.replace("**", "").replace("\n\n", "\n")
    
    def read_input_file(self, file_path: str = T_LONG_DOCUMENT_PATH) -> Tuple[str, str]:
        """
        Đọc file input và tách title và content
        Args:
            file_path: Đường dẫn đến file input
        Returns:
            Tuple (title, content)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines:
                return "", ""
                
            title = lines[0].strip()
            content = "".join(lines[1:]).strip()
            
            return title, content
        except Exception as e:
            print(f"Lỗi khi đọc file: {e}")
            return "", ""
    
    def chunk_text(self, text: str, num_chunks: int = 4, buffer_ratio: float = 0.05) -> List[str]:
        """
        Chia văn bản thành các chunk theo tỉ lệ (mỗi chunk ~25% độ dài)
        Args:
            text: Văn bản đầu vào
            num_chunks: Số chunk muốn chia (mặc định 4)
            buffer_ratio: Tỉ lệ buffer so với kích thước mỗi chunk (mặc định 5%)
        """
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        # Nếu văn bản quá ngắn (< 1000 từ), giảm số chunk để tránh tóm tắt vụn vặt
        if total_words < 1000:
            num_chunks = max(1, math.ceil(total_words / 300))  # chunk >= 300 từ
        
        chunk_size = math.ceil(total_words / num_chunks)
        buffer = max(20, int(chunk_size * buffer_ratio))  # buffer tối thiểu 20
        
        chunks = []
        step = chunk_size - buffer  # bước nhảy (có overlap để tránh cắt câu)
        
        for i in range(0, total_words, step):
            chunk_words = words[i:i + chunk_size]
            if not chunk_words:
                break
            chunks.append(" ".join(chunk_words))
        
        return chunks

    def summarize_chunk(self, chunk: str, max_output_tokens: int = 300, max_input_words: int = 1500) -> str:
        """
        Tóm tắt một chunk văn bản sử dụng Gemini
        Args:
            chunk: Đoạn văn bản cần tóm tắt
            max_output_tokens: Số token tối đa đầu ra
            max_input_words: Giới hạn số từ tối đa đưa vào prompt
        """
        words = chunk.split()

        # Nếu chunk quá dài thì cắt còn max_input_words từ đầu
        if len(words) > max_input_words:
            chunk = " ".join(words[:max_input_words])
            print(f"⚠️ Chunk quá dài ({len(words)} từ), cắt xuống {max_input_words} từ trước khi gửi cho Gemini")

        prompt = f"Hãy tóm tắt ngắn gọn đoạn văn sau đây còn khoảng 200-250 từ:\n{chunk}"

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_output_tokens,
                    temperature=0.3
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"‼️ Lỗi khi tóm tắt chunk: {e}")
            # Fallback: lấy ~200 từ đầu chunk nếu lỗi
            return " ".join(chunk.split()[:200])


    def summarize_long_text(self, title: str, text: str, max_output_tokens: int = 200) -> str:
        """
        Tóm tắt văn bản dài bằng cách chia thành các chunk và tóm tắt từng chunk
        Args:
            title: Tiêu đề văn bản
            text: Nội dung văn bản
            max_output_tokens: Số token tối đa cho mỗi chunk summary
        Returns:
            Văn bản đã được tóm tắt
        """
        # Chia văn bản thành các chunk
        chunks = self.chunk_text(text)
        summaries = []
        
        # Tóm tắt từng chunk
        for i, chunk in enumerate(chunks, 1):
            print(f"Đang xử lý chunk {i}/{len(chunks)}...")
            summary = self.summarize_chunk(chunk, max_output_tokens)
            summaries.append(summary)
        
        # Kết hợp các bản tóm tắt
        combined_summary = " ".join(summaries)
            
        with open(T_SUM_PATH, "w", encoding="utf-8") as f:
            f.write(f"title:{title}\n")
            f.write(combined_summary)
            
        return combined_summary, title

    def rewrite_with_title(self, title: str, summary: str, max_output_tokens: int = 2048, max_input_words: int = 1500) -> str:
        """
        Viết lại bản tóm tắt cuối cùng với sự tham chiếu đến title gốc
        Args:
            title: Tiêu đề gốc của bài viết
            summary: Bản tóm tắt đã được tạo
            max_output_tokens: Số token tối đa đầu ra
            max_input_words: Giới hạn số từ truyền vào prompt cho phần summary
        Returns:
            Bản viết lại cuối cùng
        """
        # Đọc sample text để tham khảo style viết
        try:
            with open(T_SAMPLE_PATH, "r", encoding="utf-8") as f:
                sample_text = f.read()
        except:
            sample_text = ""

        # Cắt summary nếu quá dài
        words = summary.split()
        if len(words) > max_input_words:
            print(f"⚠️ Summary quá dài ({len(words)} từ) → cắt còn {max_input_words} từ đầu để đưa vào prompt")
            summary = " ".join(words[:max_input_words])

        prompt = f"""Bạn là một biên tập viên tiếng Việt giỏi của {self.site_name}, chuyên viết bài đăng ngắn, có độ kết nối, giọng văn nghiêm túc. Mục tiêu Call To Action.
Dựa trên tiêu đề gốc: "{title}"
Hãy viết lại đoạn tóm tắt sau đây thành một bài viết YÊU CẦU DÀI 400-500 từ, yêu cầu kết nối, tự nhiên, dễ đọc hơn đối với người dùng mạng xã hội:

{summary}

Yêu cầu đầu ra: Không sử dụng markdown
Dòng 1: title: <1 câu> KHÔNG quá 45 ký tự, giữ keyword quan trọng từ tiêu đề gốc.
Dòng 2: article_summary: <đoạn văn>
<Phần nội dung còn lại (có thể chia 2-4 đoạn, cố gắng lồng ghép thương hiệu {self.site_name})> 
Format đầu ra: KHÔNG Sử dụng markdown, bullets, chỉ các đoạn văn thuần
"""

        if sample_text:
            prompt += f"\nDưới đây là một bài viết mẫu đạt yêu cầu về độ dài và style viết:\n{sample_text}\nHãy tham khảo cách viết và điều chỉnh đoạn văn trên:"

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_output_tokens
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"Lỗi khi viết lại với title: {e}")
            return summary


    def process_document(self, input_path: str = T_LONG_DOCUMENT_PATH) -> Tuple[str, str]:
        """
        Xử lý toàn bộ quy trình từ đọc file đến tạo bản tóm tắt cuối cùng
        Args:
            input_path: Đường dẫn đến file input
        Returns:
            Tuple (final_title, final_content)
        """
        # Bước 1: Đọc file và tách title, content
        title, content = self.read_input_file(input_path)
        if not title or not content:
            print("Không thể đọc được nội dung từ file")
            return "", ""
        
        print(f"Đã đọc bài viết với tiêu đề: {title}")
        
        # Bước 2: Tóm tắt nội dung dài
        summary, original_title = self.summarize_long_text(title, content)
        
        # Bước 3: Viết lại với tham chiếu đến title gốc
        final_content = self.rewrite_with_title(original_title, summary)
        final_content = self.post_process(final_content)
        
        # Tách title từ nội dung cuối cùng
        lines = final_content.split('\n')
        final_title = lines[0].replace("title:", "").strip() if lines and "title:" in lines[0] else original_title
        
        # Lưu kết quả cuối cùng
        with open(FINAL_RESULT_PATH, "w", encoding="utf-8") as f:
            f.write(final_content)
            
        return final_title, final_content

# # Example usage
# if __name__ == "__main__":
    
#     # Khởi tạo summarizer
#     summarizer = GeminiSummarizer(API_KEY, site_name=SITE_NAME)
    
#     # Xử lý toàn bộ tài liệu
#     final_title, final_content = summarizer.process_document()
#     print("=" * 50)
#     print(final_content)
