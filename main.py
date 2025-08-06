#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CalDAV 同步工具主程序
统一进行账号信息获取与调度
"""

import sys
import argparse
from typing import List, Optional
from config_manager import ConfigManager, CalDAVAccount
from sync_dingtalk import DingTalkCalDAVSync
from sync_tencent import TencentCalDAVSync
from ics_merger import ICSMerger

class CalDAVSyncManager:
    """CalDAV 同步管理器"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.sync_handlers = {
            'dingtalk': DingTalkCalDAVSync,
            'tencent': TencentCalDAVSync
        }
        self.merger = ICSMerger()

    def list_accounts(self):
        """列出所有配置的账号"""
        self.config_manager.list_accounts()

    def sync_account(self, account: CalDAVAccount) -> bool:
        """同步指定账号"""
        print(f"\n=== 开始同步账号: {account.account_name} ===")

        # 获取对应的同步处理器
        handler_class = self.sync_handlers.get(account.account_type)
        if not handler_class:
            print(f"❌ 不支持的账号类型: {account.account_type}")
            return False

        try:
            # 准备特定于处理器的配置
            handler_config = {}
            if account.account_type == 'tencent':
                handler_config['TENCENT_SYNC_DAYS_PAST'] = self.config_manager.get_global_config('TENCENT_SYNC_DAYS_PAST')
                handler_config['TENCENT_SYNC_DAYS_FUTURE'] = self.config_manager.get_global_config('TENCENT_SYNC_DAYS_FUTURE')
            elif account.account_type == 'dingtalk':
                handler_config['DINGTALK_SYNC_DAYS_PAST'] = self.config_manager.get_global_config('DINGTALK_SYNC_DAYS_PAST')
                handler_config['DINGTALK_SYNC_DAYS_FUTURE'] = self.config_manager.get_global_config('DINGTALK_SYNC_DAYS_FUTURE')

            # 创建同步处理器实例
            sync_handler = handler_class(account, config=handler_config)

            # 执行同步
            result = sync_handler.sync()

            if result:
                print(f"✅ 账号 {account.account_name} 同步成功")
                return True
            else:
                print(f"❌ 账号 {account.account_name} 同步失败")
                return False

        except Exception as e:
            print(f"❌ 同步账号 {account.account_name} 时发生异常: {e}")
            return False

    def sync_all_accounts(self) -> int:
        """同步所有账号"""
        accounts = self.config_manager.get_accounts()

        if not accounts:
            print("❌ 未找到任何配置的账号")
            return 0

        print(f"找到 {len(accounts)} 个配置的账号")

        success_count = 0
        for account in accounts:
            if self.sync_account(account):
                success_count += 1

        print(f"\n=== 同步完成 ===")
        print(f"成功: {success_count}/{len(accounts)} 个账号")

        return success_count

    def sync_by_type(self, account_type: str) -> bool:
        """根据类型同步账号"""
        account = self.config_manager.get_account_by_type(account_type)

        if not account:
            print(f"❌ 未找到类型为 {account_type} 的账号")
            return False

        return self.sync_account(account)

    def sync_by_name(self, account_name: str) -> bool:
        """根据名称同步账号"""
        account = self.config_manager.get_account_by_name(account_name)

        if not account:
            print(f"❌ 未找到名称为 {account_name} 的账号")
            return False

        return self.sync_account(account)

    def merge_by_type(self, account_type: str) -> bool:
        """按账号类型合并ICS文件"""

        print(f"\n=== 开始按类型合并: {account_type} ===")

        try:
            # 获取自定义文件名
            custom_filename = self.config_manager.get_global_config('ICS_FILE_NAME')
            merged_file = self.merger.merge_by_account_type(account_type, custom_filename)
            if merged_file:
                print(f"✅ {account_type} 类型合并成功: {merged_file}")
                return True
            else:
                print(f"❌ {account_type} 类型合并失败")
                return False
        except Exception as e:
            print(f"❌ {account_type} 类型合并异常: {e}")
            return False

    def merge_all(self) -> bool:
        """合并所有账号的ICS文件"""

        print(f"\n=== 开始合并所有账号 ===")

        try:
            # 获取自定义文件名
            custom_filename = self.config_manager.get_global_config('ICS_FILE_NAME')
            merged_file = self.merger.merge_all_accounts(custom_filename)
            if merged_file:
                print(f"✅ 所有账号合并成功: {merged_file}")
                return True
            else:
                print(f"❌ 所有账号合并失败")
                return False
        except Exception as e:
            print(f"❌ 所有账号合并异常: {e}")
            return False

    def cleanup_temp_files(self, days: int = 7) -> bool:
        """清理临时文件"""

        print(f"\n=== 开始清理临时文件 ===")

        try:
            self.merger.cleanup_temp_files(days)
            print(f"✅ 临时文件清理完成")
            return True
        except Exception as e:
            print(f"❌ 临时文件清理异常: {e}")
            return False

    def run_full_workflow(self, cleanup_days: int = 7) -> bool:
        """运行完整工作流程：同步所有账号 -> 按类型合并 -> 全局合并 -> 清理临时文件"""

        print(f"\n🚀 === 开始完整工作流程 ===")

        workflow_success = True

        try:
            # 步骤1: 同步所有账号
            print(f"\n📥 步骤1: 同步所有账号")
            success_count = self.sync_all_accounts()
            if success_count == 0:
                print("❌ 没有账号同步成功，终止工作流程")
                return False

            print(f"✅ 步骤1完成: {success_count} 个账号同步成功")

            # 步骤2: 按类型合并ICS文件
            print(f"\n📋 步骤2: 按类型合并ICS文件")

            # 获取所有账号类型
            account_types = set()
            for account in self.config_manager.get_accounts():
                account_types.add(account.account_type)

            merged_files = []
            custom_filename = self.config_manager.get_global_config('ICS_FILE_NAME')
            for account_type in account_types:
                print(f"  合并 {account_type} 类型...")
                merged_file = self.merger.merge_by_account_type(account_type, custom_filename)
                if merged_file:
                    merged_files.append(merged_file)
                    print(f"  ✅ {account_type} 合并成功: {merged_file}")
                else:
                    print(f"  ⚠️ {account_type} 合并失败")
                    workflow_success = False

            print(f"✅ 步骤2完成: 生成了 {len(merged_files)} 个按类型合并的文件")

            # 步骤3: 全局合并
            print(f"\n🌐 步骤3: 全局合并所有账号")
            # 获取自定义文件名
            custom_filename = self.config_manager.get_global_config('ICS_FILE_NAME')
            global_merged_file = self.merger.merge_all_accounts(custom_filename)
            if global_merged_file:
                print(f"✅ 步骤3完成: 全局合并成功 -> {global_merged_file}")
            else:
                print(f"❌ 步骤3失败: 全局合并失败")
                workflow_success = False

            # 步骤4: 清理临时文件
            print(f"\n🧹 步骤4: 清理临时文件")
            self.merger.cleanup_temp_files(cleanup_days)
            print(f"✅ 步骤4完成: 清理了 {cleanup_days} 天前的临时文件")

            # 工作流程总结
            print(f"\n🎉 === 完整工作流程完成 ===")
            print(f"📊 工作流程总结:")
            print(f"  - 同步账号: {success_count} 个成功")
            print(f"  - 按类型合并: {len(merged_files)} 个文件")
            if global_merged_file:
                print(f"  - 全局合并: {global_merged_file}")
            print(f"  - 临时文件清理: 完成")

            if workflow_success:
                print(f"✅ 所有步骤执行成功！")
            else:
                print(f"⚠️ 部分步骤执行失败，请检查日志")

            return workflow_success

        except Exception as e:
            print(f"❌ 工作流程执行异常: {e}")
            return False

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='CalDAV 同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py --list                    # 列出所有配置的账号
  python main.py --sync-all                # 同步所有账号
  python main.py --sync-type dingtalk      # 同步钉钉账号
  python main.py --sync-type tencent       # 同步腾讯会议账号
  python main.py --sync-name "钉钉日历账号"  # 根据名称同步账号
  python main.py --merge-type dingtalk     # 合并钉钉类型的ICS文件
  python main.py --merge-all               # 合并所有账号的ICS文件
  python main.py --cleanup                 # 清理临时文件
  python main.py --workflow                # 运行完整工作流程（同步+合并+清理）
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='列出所有配置的账号')
    group.add_argument('--sync-all', action='store_true', help='同步所有账号')
    group.add_argument('--sync-type', metavar='TYPE', help='根据类型同步账号 (dingtalk, tencent)')
    group.add_argument('--sync-name', metavar='NAME', help='根据名称同步账号')
    group.add_argument('--merge-type', metavar='TYPE', help='按类型合并ICS文件 (dingtalk, tencent)')
    group.add_argument('--merge-all', action='store_true', help='合并所有账号的ICS文件')
    group.add_argument('--cleanup', type=int, nargs='?', const=7, metavar='DAYS', help='清理N天前的临时文件 (默认7天)')
    group.add_argument('--workflow', type=int, nargs='?', const=7, metavar='DAYS', help='运行完整工作流程：同步+合并+清理 (默认清理7天前文件)')

    parser.add_argument('--config', default='.env', help='配置文件路径 (默认: .env)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    return parser

def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # 创建同步管理器
        sync_manager = CalDAVSyncManager()

        if args.list:
            # 列出所有账号
            sync_manager.list_accounts()

        elif args.sync_all:
            # 同步所有账号
            success_count = sync_manager.sync_all_accounts()
            sys.exit(0 if success_count > 0 else 1)

        elif args.sync_type:
            # 根据类型同步
            success = sync_manager.sync_by_type(args.sync_type)
            sys.exit(0 if success else 1)

        elif args.sync_name:
            # 根据名称同步
            success = sync_manager.sync_by_name(args.sync_name)
            sys.exit(0 if success else 1)

        elif args.merge_type:
            # 按类型合并
            success = sync_manager.merge_by_type(args.merge_type)
            sys.exit(0 if success else 1)

        elif args.merge_all:
            # 合并所有账号
            success = sync_manager.merge_all()
            sys.exit(0 if success else 1)

        elif args.cleanup is not None:
            # 清理临时文件
            success = sync_manager.cleanup_temp_files(args.cleanup)
            sys.exit(0 if success else 1)

        elif args.workflow is not None:
            # 运行完整工作流程
            success = sync_manager.run_full_workflow(args.workflow)
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
