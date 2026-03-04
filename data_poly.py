import os
import re
import pandas as pd
from collections import defaultdict

def parse_mcpat_log(dest_dir):
    log_file = os.path.join(dest_dir, "mcpat.log")
    if not os.path.exists(log_file):
        return None
    
    data = {"Directory": dest_dir}
    with open(log_file, "r") as f:
        content = f.read()

        processor_match = re.search(
            r"Processor:\s+\n  Area = ([\d\.eE+-]+) mm\^2\n  Peak Power = ([\d\.eE+-]+) W\n  Total Leakage = ([\d\.eE+-]+) W\n  Peak Dynamic = ([\d\.eE+-]+) W\n  Subthreshold Leakage = ([\d\.eE+-]+) W\n  Gate Leakage = ([\d\.eE+-]+) W\n  Runtime Dynamic = ([\d\.eE+-]+) W",
            content, re.S
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
            pattern = rf"{unit_name}:\s*Area = ({number_pattern}) mm\^2\s*Peak Dynamic = ({number_pattern}) W\s*Subthreshold Leakage = ({number_pattern}) W\s*(?:Gate Leakage = ({number_pattern}) W\s*)?Runtime Dynamic = ({number_pattern}) W"
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
        data.update(extract_unit_data("Integer ALUs \\(Count: 6 \\)", "INTALU"))
        data.update(extract_unit_data("Int Front End RAT with 1 internal checkpoints", "INTRAT"))

    return data if len(data) > 1 else None

def parse_output_txt(dest_dir):
    output_file = os.path.join(dest_dir, "stats.txt")
    if not os.path.exists(output_file):
        return None

    with open(output_file, "r") as f:
        for line in f:
            match = re.search(r"simSeconds\s+(\d+\.\d+)", line)
            if match:
                return {"Time (sec)": float(match.group(1))}

    return {"Time (sec)": 0}

def extract_directory_info(directory):
    match = re.search(r"restore_([a-z]+)_([a-zA-Z0-9_]+)", os.path.basename(directory))
    if match:
        return match.group(1), match.group(2)
    return None, None

def sort_key(directory):
    key_order = {
        "novp": 0,
        "loop": 1,
        "loopu": 2,
        "loope": 3,
        "loops": 4,
        "origin": 5
    }
    key, suffix = extract_directory_info(directory)
    return (key_order.get(key, 99), suffix)

def process_all_logs_by_sheet(base_dir, output_file="mcpat_poly_results.xlsx"):
    grouped_results = defaultdict(list)

    all_dirs = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if d.startswith("restore_") and os.path.isdir(os.path.join(base_dir, d))
    ]

    for dest_dir in all_dirs:
        type_key, suffix = extract_directory_info(dest_dir)
        if not type_key:
            continue

        data = parse_mcpat_log(dest_dir) or {}
        time_data = parse_output_txt(dest_dir) or {}
        if data or time_data:
            data.update(time_data)
            grouped_results[type_key].append(data)

    if grouped_results:
        with pd.ExcelWriter(output_file) as writer:
            for type_key in sorted(grouped_results.keys()):
                group = grouped_results[type_key]
                group = sorted(group, key=lambda x: x.get("Directory", ""))
                df = pd.DataFrame(group)
                df.to_excel(writer, sheet_name=type_key, index=False)
        print(f"✅ 统计完成，结果写入多页 Excel：{output_file}")
    else:
        print("⚠️ 没有找到任何有效数据。")

if __name__ == "__main__":
    base_dir = "/home/damon/gem5_loop/gem5/poly_results"
    process_all_logs_by_sheet(base_dir)
