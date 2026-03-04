import os
import re
import pandas as pd

def parse_mcpat_log(dest_dir):
    log_file = os.path.join(dest_dir, "mcpat.log")
    if not os.path.exists(log_file):
        print(f"警告: {log_file} 不存在，跳过解析。")
        return None
    
    data = {"Directory": dest_dir}
    with open(log_file, "r") as f:
        content = f.read()
        
        # 仅解析Processor的主数据，避免被Total Cores和Total L2s影响
        processor_match = re.search(
            r"Processor:\s+\n  Area = (\d+\.\d+|\d+) mm\^2\n  Peak Power = (\d+\.\d+|\d+) W\n  Total Leakage = (\d+\.\d+|\d+) W\n  Peak Dynamic = (\d+\.\d+|\d+) W\n  Subthreshold Leakage = (\d+\.\d+|\d+) W\n  Gate Leakage = (\d+\.\d+|\d+) W\n  Runtime Dynamic = (\d+\.\d+|\d+) W",
            content,
            re.S
        )
        
        if processor_match:
            data.update({
                "Area (mm^2)": float(processor_match.group(1)),
                "Peak Power (W)": float(processor_match.group(2)),
                "Total Leakage (W)": float(processor_match.group(3)),
                "Peak Dynamic (W)": float(processor_match.group(4)),
                "Subthreshold Leakage (W)": float(processor_match.group(5)),
                "Gate Leakage (W)": float(processor_match.group(6)),
                "Runtime Dynamic (W)": float(processor_match.group(7)),
            })

        def extract_unit_data(unit_name, prefix):
            # 修改正则表达式以支持科学计数法
            number_pattern = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
            
            pattern = rf"{unit_name}:\s*"
            pattern += rf"Area = ({number_pattern}) mm\^2\s*"
            pattern += rf"Peak Dynamic = ({number_pattern}) W\s*"
            pattern += rf"Subthreshold Leakage = ({number_pattern}) W\s*"
            pattern += rf"(?:Gate Leakage = ({number_pattern}) W\s*)?"  # Gate Leakage 可能缺失
            pattern += rf"Runtime Dynamic = ({number_pattern}) W"

            match = re.search(pattern, content, re.S)

            if match:
                unit_data = {
                    f"{prefix}_Area (mm^2)": float(match.group(1)),
                    f"{prefix}_Peak Dynamic (W)": float(match.group(2)),
                    f"{prefix}_Subthreshold Leakage (W)": float(match.group(3)),
                    f"{prefix}_Gate Leakage (W)": float(match.group(4)) if match.group(4) else 0,  # 处理 Gate Leakage 缺失
                    f"{prefix}_Runtime Dynamic (W)": float(match.group(5)),  
                }
                return unit_data

            print(f"未找到 {unit_name} 数据: {dest_dir}")
            return {}

        # def extract_unit_data(unit_name, prefix):
        #     pattern = rf"{unit_name}:\s*Area = (\d+\.\d+|\d+) mm\^2\s*Peak Dynamic = (\d+\.\d+|\d+) W\s*Subthreshold Leakage = (\d+\.\d+|\d+) W\s*(?:Gate Leakage = (\d+\.\d+|\d+) W\s*)?Runtime Dynamic = (\d+\.\d+|\d+) W"
        #     match = re.search(pattern, content, re.S)
        #     if match:
        #         unit_data = {
        #             f"{prefix}_Area (mm^2)": float(match.group(1)),
        #             f"{prefix}_Peak Dynamic (W)": float(match.group(2)),
        #             f"{prefix}_Subthreshold Leakage (W)": float(match.group(3)),
        #             f"{prefix}_Gate Leakage (W)" : float(match.group(4)) if match.group(4) else 0,
        #             f"{prefix}_Runtime Dynamic (W)": float(match.group(5)),  # 处理 Runtime Dynamic 索引
        #         }
        #         return unit_data
            
        #     print(f"未找到 {unit_name} 数据: {dest_dir}")
        #     return {}

        data.update(extract_unit_data("Instruction Fetch Unit", "IFU"))
        data.update(extract_unit_data("Renaming Unit", "RU"))
        data.update(extract_unit_data("Execution Unit", "EU"))
        data.update(extract_unit_data("Register Files", "RF"))
        data.update(extract_unit_data("Instruction Scheduler", "IS"))
        data.update(extract_unit_data("Integer ALUs \(Count: 6 \)", "INTALU"))
        data.update(extract_unit_data("Int Front End RAT with 1 internal checkpoints", "INTRAT"))

        # for unit in ["Instruction Fetch Unit", "Renaming Unit", "Execution Unit"]:
        #     data.update(extract_unit_data(unit))

    return data if len(data) > 1 else None

def parse_output_txt(dest_dir):
    output_file = os.path.join(dest_dir, "stats.txt")
    if not os.path.exists(output_file):
        print(f"警告: {output_file} 不存在，跳过解析。")
        return None

    time_sec_list = []  # 存储所有匹配的 simSeconds
    with open(output_file, "r") as f:
        # content = f.read()
        for line in f:
            match = re.search(r"simSeconds\s+(\d+\.\d+)\s+", line)
            if match:
                time_sec_list.append(float(match.group(1)))
                break

    if len(time_sec_list) > 1:
        print(f"警告: {output_file} 发现多个 simSeconds: {time_sec_list}")

    return {"Time (sec)": time_sec_list[0] if time_sec_list else 0}

def extract_directory_info(directory):
    """
    提取目录信息:去掉路径前缀,并提取关键字novp, loop, loopu, loope, loops和数字部分
    """
    # 去掉路径前缀，只保留 run_TSVC_* 部分
    match = re.search(r"run_TSVC_(novp|loop|loopu|loope|loops|origin)_se_(\d+)", directory)
    if match:
        key = match.group(1)  # 获取关键字部分
        number = int(match.group(2))  # 获取数字部分
        return key, number
    return None, None

def sort_key(directory):
    """
    根据目录中的关键字novp, loop, loopu, loope, loops和数字部分生成排序键。
    """
    key_order = {
        "novp": 0,
        "loop": 1,
        "loopu": 2,
        "loope": 3,
        "loops": 4,
        "origin": 5
    }

    key, number = extract_directory_info(directory)
    if key and number is not None:
        # 返回一个包含两个优先级的元组 (关键字的优先级, 数字部分)
        return (key_order.get(key, 5), number)
    return (5, float('inf'))  # 如果提取失败，返回最大值

def process_all_logs(base_dirs, start=1, end=151, output_file="mcpat_results.xlsx"):
    results = []
    for i in range(start, end + 1):
        for base_dir in base_dirs:
            dest_dir = base_dir.format(i)
            data = parse_mcpat_log(dest_dir) or {}
            time_data = parse_output_txt(dest_dir) or {}
            # print(dest_dir, time_data)
            if "Directory" not in data:
                print(f"⚠️ 发现 NaN Directory 数据: {dest_dir, time_data}")
            if data or time_data:
                data.update(time_data)
                results.append(data)
                # print(f"当前存入的数据: {data}")

    
    # 保存结果到 Excel
    if results:
        results = sorted(results, key=lambda x: sort_key(x.get("Directory", "")))

        df = pd.DataFrame(results)
        # print("最终 DataFrame 内容:")
        # print(df)
        df.to_excel(output_file, index=False)
        print(f"统计结果已保存到 {output_file}")
    else:
        print("未找到任何有效的 mcpat.log 或 output.txt 解析数据。")

if __name__ == "__main__":
    base_dirs = [
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_novp_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loop_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loopu_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loope_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_loops_se_{}",
        "/home/damon/gem5_loop/gem5/se_results/run_TSVC_origin_se_{}",
    ]
    
    process_all_logs(base_dirs)