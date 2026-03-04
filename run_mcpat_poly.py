import subprocess
import os
from concurrent.futures import ProcessPoolExecutor

def run_makefile(dest_dir):
    dest_dir = os.path.abspath(dest_dir)
    try:
        subprocess.run(["make", "all", f"DEST_DIR={dest_dir}"], check=True)
        print(f"✅ Makefile 执行完成：{dest_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Makefile 执行失败：{dest_dir} - {e}")

def main():
    base_dir = "/home/damon/gem5_loop/gem5/poly_results"

    # 只选择 restore_ 开头的子文件夹
    dest_dirs = [
        os.path.join(base_dir, folder)
        for folder in os.listdir(base_dir)
        if folder.startswith("restore_") and os.path.isdir(os.path.join(base_dir, folder))
    ]

    print(f"🗂️ 共找到 {len(dest_dirs)} 个以 'restore_' 开头的目录，开始执行 make...")

    with ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(run_makefile, dest_dirs)

if __name__ == "__main__":
    main()
