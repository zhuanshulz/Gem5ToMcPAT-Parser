import os
import re
import pandas as pd

def parse_mcpat_log(log_path):
    if not os.path.exists(log_path):
        print(f"警告: {log_path} 不存在，跳过解析。")
        return None
    
    data = {"File Path": log_path}
    with open(log_path, "r") as f:
        content = f.read()
        
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
            number_pattern = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
            pattern = rf"{unit_name}:\s*"
            pattern += rf"Area = ({number_pattern}) mm\^2\s*"
            pattern += rf"Peak Dynamic = ({number_pattern}) W\s*"
            pattern += rf"Subthreshold Leakage = ({number_pattern}) W\s*"
            pattern += rf"(?:Gate Leakage = ({number_pattern}) W\s*)?"
            pattern += rf"Runtime Dynamic = ({number_pattern}) W"
            match = re.search(pattern, content, re.S)
            
            if match:
                return {
                    f"{prefix}_Area (mm^2)": float(match.group(1)),
                    f"{prefix}_Peak Dynamic (W)": float(match.group(2)),
                    f"{prefix}_Subthreshold Leakage (W)": float(match.group(3)),
                    f"{prefix}_Gate Leakage (W)": float(match.group(4)) if match.group(4) else 0,
                    f"{prefix}_Runtime Dynamic (W)": float(match.group(5)),
                }
            return {}
        
        data.update(extract_unit_data("Instruction Fetch Unit", "IFU"))
        data.update(extract_unit_data("Renaming Unit", "RU"))
        data.update(extract_unit_data("Execution Unit", "EU"))
        data.update(extract_unit_data("Register Files", "RF"))
        data.update(extract_unit_data("Instruction Scheduler", "IS"))
        data.update(extract_unit_data("Integer ALUs \(Count: 6 \)", "INTALU"))
        data.update(extract_unit_data("Int Front End RAT with 1 internal checkpoints", "INTRAT"))
    
    return data if len(data) > 1 else None

def parse_stats_txt(stats_path):
    if not os.path.exists(stats_path):
        print(f"警告: {stats_path} 不存在，跳过解析。")
        return None

    with open(stats_path, "r") as f:
        for line in f:
            match = re.search(r"simSeconds\s+(\d+\.\d+)\s+", line)
            if match:
                return {"Time (sec)": float(match.group(1))}
    
    return {"Time (sec)": 0}

def extract_directory_info(directory):
    match = re.search(r"../(\d+)_simpoint/restore_(\w+)_(\d+)", directory)
    if match:
        return int(match.group(1)), int(match.group(3)), (match.group(2))
    return None, None, None

def process_all_logs(base_path, priority_dict, output_file="spec_mcpat_results.xlsx"):
    results = []
    
    for root, _, files in os.walk(base_path):
        if "mcpat.log" in files:
            print(f"正在处理: {root}")
            spec_index, restore_index, second_priority = extract_directory_info(root)
            if not spec_index or not restore_index:
                continue
            expected_points = priority_dict.get(f"{spec_index}_simpoint", None)
            if expected_points is not None and int(restore_index) != expected_points:
                continue
            log_path = os.path.join(root, "mcpat.log")
            stats_path = os.path.join(root, "stats.txt")
            
            data = parse_mcpat_log(log_path) or {}
            time_data = parse_stats_txt(stats_path) or {}
            
            data.update(time_data)
            data["SPEC Index"] = spec_index
            data["Second Priority"] = second_priority
            data["Restore Index"] = restore_index
            
            results.append(data)
    
    if results:
        df = pd.DataFrame(results)
        df.sort_values(
            by=["SPEC Index", "Restore Index", "Second Priority"],
            key=lambda x: x if x.dtype == "int64" else x.astype(str).str.lower(),  # 统一字符串排序
            inplace=True
        )
        df.to_excel(output_file, index=False)
        print(f"统计结果已保存到 {output_file}")
    else:
        print("未找到任何有效的数据。")

if __name__ == "__main__":
    priority_dict = {
        "500_simpoint": 3, "502_simpoint": 7, "503_simpoint": 3,
        "505_simpoint": 9, "507_simpoint": 3, "508_simpoint": 4,
        "511_simpoint": 4,
        "519_simpoint": 2, "520_simpoint": 3, "521_simpoint": 3,
        "523_simpoint": 3, "525_simpoint": 16, "526_simpoint": 2,
        "527_simpoint": 15, "531_simpoint": 4, 
        "538_simpoint": 2,
        "541_simpoint": 10,
        "544_simpoint": 3, "548_simpoint": 4, "549_simpoint": 2,
        "554_simpoint": 15, "557_simpoint": 3,
    }
    
    base_path = "../SPEC_Results"
    process_all_logs(base_path, priority_dict)
