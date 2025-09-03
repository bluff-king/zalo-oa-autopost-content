import time
import os
import glob
from Add_Link_Output_Post_OA import run_pipeline

def cleanup_files():
    output_dir = os.path.join(".", "OutputDoc")

    # Danh sách file .txt cần xoá
    files_to_delete = [
        os.path.join(output_dir, "t_sum.txt"),
        os.path.join(output_dir, "t_long_document.txt"),
        os.path.join(output_dir, "final_result.txt")
    ]

    # Xoá cover.* với nhiều loại extension (ảnh)
    cover_patterns = ["cover*", "cover*.jpg", "cover*.jpeg", "cover*.png", "cover*.gif", "cover*.webp"]
    for pattern in cover_patterns:
        files_to_delete.extend(glob.glob(os.path.join(output_dir, pattern)))

    # Tiến hành xoá
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"🗑️ Đã xoá: {file}")
            except Exception as e:
                print(f"⚠️ Không xoá được {file}: {e}")
        else:
            print(f"⏩ File không tồn tại, bỏ qua: {file}")

while True:
    cleanup_files()   # ⬅️ xoá file trước mỗi vòng lặp
    run_pipeline()
    print("⏳ Chờ 1 tiếng trước khi chạy link tiếp theo...")
    time.sleep(3600)
