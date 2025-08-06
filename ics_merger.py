#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ICS 文件合并工具
支持按账号类型合并和多账号合并功能
"""

import os
import glob
from datetime import datetime
from typing import List, Dict, Set
import re

class ICSMerger:
    """ICS 文件合并处理器"""

    def __init__(self, temp_dir: str = "temp", merged_dir: str = "merged", public_dir: str = "public"):
        self.temp_dir = temp_dir
        self.merged_dir = merged_dir
        self.public_dir = public_dir

        # 创建目录
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.merged_dir, exist_ok=True)
        os.makedirs(self.public_dir, exist_ok=True)

    def parse_ics_file(self, filepath: str) -> Dict:
        """解析单个ICS文件"""

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取VEVENT部分
            vevent_pattern = r'BEGIN:VEVENT.*?END:VEVENT'
            vevents = re.findall(vevent_pattern, content, re.DOTALL)

            # 提取VTIMEZONE部分（如果存在）
            vtimezone_pattern = r'BEGIN:VTIMEZONE.*?END:VTIMEZONE'
            vtimezones = re.findall(vtimezone_pattern, content, re.DOTALL)

            return {
                'vevents': vevents,
                'vtimezones': vtimezones,
                'filepath': filepath
            }

        except Exception as e:
            print(f"解析ICS文件失败 {filepath}: {e}")
            return {'vevents': [], 'vtimezones': [], 'filepath': filepath}

    def collect_ics_files_by_type(self, account_type: str) -> List[str]:
        """收集指定账号类型的所有ICS文件"""

        ics_files = []

        # 根据账号类型查找对应的目录
        if account_type.lower() == 'dingtalk':
            pattern = "dingtalk_events_*/*/*.ics"
        elif account_type.lower() == 'tencent':
            pattern = "tencent_events_*/*/*.ics"
        else:
            print(f"不支持的账号类型: {account_type}")
            return []

        ics_files = glob.glob(pattern)
        print(f"找到 {len(ics_files)} 个 {account_type} ICS 文件")

        return ics_files

    def collect_all_ics_files(self) -> List[str]:
        """收集所有ICS文件"""

        ics_files = []

        # 收集钉钉文件
        dingtalk_files = glob.glob("dingtalk_events_*/*/*.ics")
        ics_files.extend(dingtalk_files)

        # 收集腾讯会议文件
        tencent_files = glob.glob("tencent_events_*/*/*.ics")
        ics_files.extend(tencent_files)

        print(f"总共找到 {len(ics_files)} 个 ICS 文件")
        print(f"  - 钉钉: {len(dingtalk_files)} 个")
        print(f"  - 腾讯会议: {len(tencent_files)} 个")

        return ics_files

    def merge_ics_files(self, ics_files: List[str], output_filename: str, calendar_name: str = "合并日历") -> str:
        """合并多个ICS文件为一个"""

        if not ics_files:
            print("没有ICS文件需要合并")
            return ""

        print(f"开始合并 {len(ics_files)} 个ICS文件...")

        all_vevents = []
        all_vtimezones = set()  # 使用set避免重复

        # 解析所有ICS文件
        for ics_file in ics_files:
            parsed = self.parse_ics_file(ics_file)
            all_vevents.extend(parsed['vevents'])
            all_vtimezones.update(parsed['vtimezones'])

        # 生成合并后的ICS内容
        merged_content = self.generate_merged_ics(
            list(all_vtimezones),
            all_vevents,
            calendar_name
        )

        # 保存合并文件
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(merged_content)

        print(f"✅ 合并完成: {output_filename}")
        print(f"   - 事件数量: {len(all_vevents)}")
        print(f"   - 时区数量: {len(all_vtimezones)}")

        return output_filename

    def generate_merged_ics(self, vtimezones: List[str], vevents: List[str], calendar_name: str) -> str:
        """生成合并后的ICS文件内容"""

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

        # ICS文件头部
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//CalDAV Sync Tool//CalDAV Sync Tool v3//CN",
            f"X-WR-CALNAME:{calendar_name}",
            f"X-WR-CALDESC:由 CalDAV 同步工具合并生成",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]

        # 添加时区信息
        for vtimezone in vtimezones:
            ics_content.append(vtimezone)

        # 添加事件
        for vevent in vevents:
            ics_content.append(vevent)

        # ICS文件尾部
        ics_content.append("END:VCALENDAR")

        return "\n".join(ics_content)

    def merge_by_account_type(self, account_type: str) -> str:
        """按账号类型合并ICS文件"""

        print(f"\n=== 按账号类型合并: {account_type} ===")

        # 收集指定类型的ICS文件
        ics_files = self.collect_ics_files_by_type(account_type)

        if not ics_files:
            print(f"未找到 {account_type} 类型的ICS文件")
            return ""

        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(self.merged_dir, f"{account_type}_merged_{timestamp}.ics")

        # 合并文件
        return self.merge_ics_files(
            ics_files,
            output_filename,
            f"{account_type.upper()} 合并日历"
        )

    def merge_all_accounts(self, custom_filename: str = None) -> str:
        """合并所有账号的ICS文件"""

        print(f"\n=== 合并所有账号 ===")

        # 收集所有ICS文件
        ics_files = self.collect_all_ics_files()

        if not ics_files:
            print("未找到任何ICS文件")
            return ""

        # 清理 public 目录中的旧文件（只保留一个文件）
        self.cleanup_public_files()

        # 生成输出文件名
        if custom_filename:
            output_filename = os.path.join(self.public_dir, f"all_calendars_{custom_filename}.ics")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(self.public_dir, f"all_calendars_{timestamp}.ics")

        # 合并文件
        return self.merge_ics_files(
            ics_files,
            output_filename,
            "所有日历合并"
        )

    def cleanup_public_files(self):
        """清理 public 目录中的旧 ICS 文件，只保留最新的一个"""

        print("=== 清理 public 目录中的旧文件 ===")

        # 查找所有 all_calendars_*.ics 文件
        pattern = os.path.join(self.public_dir, "all_calendars_*.ics")
        existing_files = glob.glob(pattern)

        if existing_files:
            print(f"找到 {len(existing_files)} 个现有文件，准备清理...")
            for file_path in existing_files:
                try:
                    os.remove(file_path)
                    print(f"删除旧文件: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
        else:
            print("未找到需要清理的文件")

    def get_temp_xml_path(self, service: str, username: str, file_type: str) -> str:
        """获取临时XML文件路径"""

        filename = f"{service}_{file_type}_{username}.xml"
        return os.path.join(self.temp_dir, filename)

    def cleanup_temp_files(self, older_than_days: int = 7):
        """清理临时文件和事件下载目录"""

        import time
        import shutil

        print(f"\n=== 清理 {older_than_days} 天前的临时文件和事件目录 ===")

        current_time = time.time()
        cleaned_files = 0
        cleaned_dirs = 0

        # 清理XML临时文件
        temp_files = glob.glob(os.path.join(self.temp_dir, "*.xml"))
        for temp_file in temp_files:
            file_age = current_time - os.path.getmtime(temp_file)
            if file_age > (older_than_days * 24 * 3600):
                try:
                    os.remove(temp_file)
                    cleaned_files += 1
                    print(f"删除临时文件: {temp_file}")
                except Exception as e:
                    print(f"删除文件失败 {temp_file}: {e}")

        # 清理事件下载目录
        event_dirs = glob.glob("dingtalk_events_*") + glob.glob("tencent_events_*")
        for event_dir in event_dirs:
            if os.path.isdir(event_dir):
                dir_age = current_time - os.path.getmtime(event_dir)
                if dir_age > (older_than_days * 24 * 3600):
                    try:
                        shutil.rmtree(event_dir)
                        cleaned_dirs += 1
                        print(f"删除事件目录: {event_dir}")
                    except Exception as e:
                        print(f"删除目录失败 {event_dir}: {e}")

        print(f"清理完成，删除了 {cleaned_files} 个临时文件，{cleaned_dirs} 个事件目录")

def main():
    """独立运行测试"""

    merger = ICSMerger()

    print("=== ICS 文件合并工具测试 ===")

    # 按类型合并
    dingtalk_merged = merger.merge_by_account_type("dingtalk")
    tencent_merged = merger.merge_by_account_type("tencent")

    # 合并所有账号
    all_merged = merger.merge_all_accounts()

    # 清理临时文件
    merger.cleanup_temp_files()

    print("\n=== 合并完成 ===")
    if dingtalk_merged:
        print(f"钉钉合并文件: {dingtalk_merged}")
    if tencent_merged:
        print(f"腾讯会议合并文件: {tencent_merged}")
    if all_merged:
        print(f"全部合并文件: {all_merged}")

if __name__ == "__main__":
    main()
