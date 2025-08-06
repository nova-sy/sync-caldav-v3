#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
负责从 .env 文件中读取和解析账号配置信息
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CalDAVAccount:
    """CalDAV 账号配置数据类"""
    account_type: str
    account_name: str
    username: str
    password: str
    url: str

    def get_formatted_url(self) -> str:
        """获取格式化后的 URL（替换用户名占位符）"""
        return self.url.format(username=self.username)

class ConfigManager:
    """配置管理器"""

    def __init__(self, env_file: str = '.env'):
        self.env_file = env_file
        self.config = {}
        self.accounts = []
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.env_file):
            raise FileNotFoundError(f"配置文件 {self.env_file} 不存在")

        # 读取 .env 文件
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    self.config[key.strip()] = value.strip()

        # 解析账号配置
        self._parse_accounts()

    def _parse_accounts(self):
        """解析账号配置"""
        # 支持的账号类型
        account_types = ['DINGTALK', 'TENCENT', 'GOOGLE', 'OUTLOOK']

        for account_type in account_types:
            account_name = self.config.get(f'{account_type}_ACCOUNT_NAME')
            username = self.config.get(f'{account_type}_USERNAME')
            password = self.config.get(f'{account_type}_PASSWORD')
            url = self.config.get(f'{account_type}_URL')

            # 只有当所有必需字段都存在时才创建账号
            if all([account_name, username, password, url]):
                account = CalDAVAccount(
                    account_type=account_type.lower(),
                    account_name=account_name,
                    username=username,
                    password=password,
                    url=url
                )
                self.accounts.append(account)

    def get_accounts(self) -> List[CalDAVAccount]:
        """获取所有配置的账号"""
        return self.accounts

    def get_account_by_type(self, account_type: str) -> Optional[CalDAVAccount]:
        """根据类型获取账号"""
        for account in self.accounts:
            if account.account_type == account_type.lower():
                return account
        return None

    def get_account_by_name(self, account_name: str) -> Optional[CalDAVAccount]:
        """根据名称获取账号"""
        for account in self.accounts:
            if account.account_name == account_name:
                return account
        return None

    def get_global_config(self, key: str, default=None):
        """获取全局配置"""
        return self.config.get(key, default)

    def list_accounts(self):
        """列出所有账号信息"""
        print("=== 已配置的 CalDAV 账号 ===")
        if not self.accounts:
            print("未找到任何配置的账号")
            return

        for i, account in enumerate(self.accounts, 1):
            print(f"{i}. {account.account_name}")
            print(f"   类型: {account.account_type.upper()}")
            print(f"   用户名: {account.username}")
            print(f"   URL: {account.get_formatted_url()}")
            print()

def main():
    """测试配置管理器"""
    try:
        config_manager = ConfigManager()
        config_manager.list_accounts()

        # 测试获取特定账号
        dingtalk_account = config_manager.get_account_by_type('dingtalk')
        if dingtalk_account:
            print(f"钉钉账号: {dingtalk_account.account_name}")
            print(f"格式化 URL: {dingtalk_account.get_formatted_url()}")

        tencent_account = config_manager.get_account_by_type('tencent')
        if tencent_account:
            print(f"腾讯会议账号: {tencent_account.account_name}")
            print(f"格式化 URL: {tencent_account.get_formatted_url()}")

    except Exception as e:
        print(f"配置加载失败: {e}")

if __name__ == "__main__":
    main()
