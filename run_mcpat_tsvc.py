import subprocess
import os
from concurrent.futures import ProcessPoolExecutor

def run_makefile(dest_dir):
    dest_dir = os.path.abspath(dest_dir)
    try:
        subprocess.run(["make", "all", f"DEST_DIR={dest_dir}"], check=True)
        print(f"Makefile 执行完成，输出目录: {dest_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Makefile 执行失败: {e}")

def main():
    base_dirs = [
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_novp_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loop_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loopu_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loope_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loops_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_origin_se_{}",
    ]
    
    dest_dirs = [base_dir.format(i) for i in range(1, 152) for base_dir in base_dirs]
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(run_makefile, dest_dirs)

if __name__ == "__main__":
    main()