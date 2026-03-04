import subprocess
import os
from concurrent.futures import ProcessPoolExecutor
import glob
import re


def run_makefile(dest_dir):
    """ 在指定目录运行 Makefile """
    dest_dir = os.path.abspath(dest_dir)
    try:
        subprocess.run(["make", "spec", f"DEST_DIR={dest_dir}"], check=True)
        print(f"Makefile 执行完成，输出目录: {dest_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Makefile 执行失败: {e}")


def main():
    base_dir = "/home/damon/gem5_loop/gem5/SPEC_Results-new"
    
    # 手动定义每个 *_simpoint 目录应选用的 restore_*_* 数字
    priority_dict = {
        "500_simpoint": 3,
        "502_simpoint": 7,
        "503_simpoint": 3,
        "505_simpoint": 9,
        "507_simpoint": 3,
        "508_simpoint": 4,
        "511_simpoint": 4,
        "519_simpoint": 2,
        "520_simpoint": 3,
        "521_simpoint": 3,
        "523_simpoint": 3,
        "525_simpoint": 16,
        "526_simpoint": 2,
        "527_simpoint": 15,
        "531_simpoint": 4,
        "538_simpoint": 2,
        "541_simpoint": 10,
        "544_simpoint": 3,
        "548_simpoint": 4,
        "549_simpoint": 2,
        "554_simpoint": 15,
        "557_simpoint": 3,
    }

    # 获取所有 *_simpoint 目录
    simpoint_dirs = glob.glob(os.path.join(base_dir, "*_simpoint"))

    selected_dirs = []

    for simpoint_dir in simpoint_dirs:
        simpoint_name = os.path.basename(simpoint_dir)
        
        # 检查该 simpoint 是否在字典中
        if simpoint_name not in priority_dict:
            print(f"跳过 {simpoint_name}，未在 priority_dict 中定义")
            continue  

        selected_number = priority_dict[simpoint_name]

        # 只选择符合字典定义的 restore_*_* 目录
        selected_restore_dirs = glob.glob(os.path.join(simpoint_dir, f"restore_*_{selected_number}"))
        
        if selected_restore_dirs:
            selected_dirs.extend(selected_restore_dirs)
        else:
            print(f"警告: {simpoint_name} 未找到 restore_*_{selected_number} 目录")

    # 并行执行 Makefile
    with ProcessPoolExecutor(max_workers=8) as executor:
        executor.map(run_makefile, selected_dirs)


if __name__ == "__main__":
    main()
