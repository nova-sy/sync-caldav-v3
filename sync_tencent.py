#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
腾讯会议 CalDAV 同步模块
优化后的版本，支持从配置管理器获取账号信息
"""

import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
from config_manager import CalDAVAccount
from ics_merger import ICSMerger

class TencentCalDAVSync:
    """腾讯会议 CalDAV 同步处理器"""

    def __init__(self, account: CalDAVAccount):
        self.account = account
        self.base_url = account.get_formatted_url()
        self.username = account.username
        self.password = account.password
        self.output_dir = f"tencent_events_{self.username}"
        self.merger = ICSMerger()

    def discover_collections(self):
        """发现腾讯会议日历集合"""

        print(f"=== 发现腾讯会议日历集合 ===")
        print(f"账号: {self.account.account_name}")
        print(f"用户名: {self.username}")
        print(f"发现 URL: {self.base_url}")

        propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
    <D:prop>
        <D:displayname />
        <D:resourcetype />
        <C:calendar-description />
        <C:supported-calendar-component-set />
    </D:prop>
</D:propfind>'''

        headers = {
            'Content-Type': 'application/xml; charset=UTF-8',
            'Depth': '1'
        }

        try:
            response = requests.request(
                'PROPFIND',
                self.base_url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers=headers,
                data=propfind_body,
                timeout=10
            )

            print(f"HTTP 状态码: {response.status_code}")

            if response.status_code == 207:
                print("✅ 成功发现集合")

                # 保存响应到临时目录
                temp_file = self.merger.get_temp_xml_path('tencent', self.username, 'collections')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"集合发现响应已保存到 {temp_file}")

                # 解析集合
                collections = self.parse_collections(response.text)
                return collections
            else:
                print(f"集合发现失败: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"集合发现异常: {e}")
            return []

    def parse_collections(self, xml_data):
        """解析集合响应"""

        collections = []

        try:
            root = ET.fromstring(xml_data)
            namespaces = {
                'D': 'DAV:',
                'C': 'urn:ietf:params:xml:ns:caldav'
            }

            for response_elem in root.findall('D:response', namespaces):
                href_elem = response_elem.find('D:href', namespaces)
                if href_elem is not None:
                    href = href_elem.text

                    # 检查是否是日历资源
                    resourcetype = response_elem.find('.//D:resourcetype', namespaces)
                    if resourcetype is not None:
                        calendar_elem = resourcetype.find('C:calendar', namespaces)
                        if calendar_elem is not None:
                            # 获取显示名称
                            displayname_elem = response_elem.find('.//D:displayname', namespaces)
                            displayname = displayname_elem.text if displayname_elem is not None else "未知日历"

                            # 处理相对路径，转换为完整URL
                            if href.startswith('/'):
                                full_href = f"https://cal.meeting.tencent.com{href}"
                            else:
                                full_href = href

                            collections.append({
                                'name': displayname,
                                'href': full_href
                            })

                            print(f"找到集合: {displayname} ({full_href})")

            return collections

        except ET.ParseError as e:
            print(f"XML 解析失败: {e}")
            return []

    def get_event_list(self, collection_href):
        """获取事件列表（第一步：PROPFIND）"""

        print(f"\n=== 获取事件列表 ===")
        print(f"集合 URL: {collection_href}")

        propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
<D:propfind xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
    <D:prop>
        <D:getetag />
        <D:getcontenttype />
    </D:prop>
</D:propfind>'''

        headers = {
            'Content-Type': 'application/xml; charset=UTF-8',
            'Depth': '1'
        }

        try:
            response = requests.request(
                'PROPFIND',
                collection_href,
                auth=HTTPBasicAuth(self.username, self.password),
                headers=headers,
                data=propfind_body,
                timeout=10
            )

            print(f"HTTP 状态码: {response.status_code}")

            if response.status_code == 207:
                print("✅ 成功获取事件列表")

                # 解析事件 URL 列表
                event_urls = self.parse_event_urls(response.text)
                print(f"找到 {len(event_urls)} 个事件")
                return event_urls
            else:
                print(f"获取事件列表失败: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"获取事件列表异常: {e}")
            return []

    def parse_event_urls(self, xml_data):
        """解析事件 URL 列表"""

        event_urls = []

        try:
            root = ET.fromstring(xml_data)
            namespaces = {'D': 'DAV:'}

            for response_elem in root.findall('D:response', namespaces):
                href_elem = response_elem.find('D:href', namespaces)
                if href_elem is not None:
                    href = href_elem.text

                    # 检查是否是 .ics 文件
                    if href.endswith('.ics'):
                        event_urls.append(href)
                        print(f"  事件: {href}")

            return event_urls

        except ET.ParseError as e:
            print(f"XML 解析失败: {e}")
            return []

    def download_events(self, collection_href, event_urls, display_name):
        """下载事件内容（第二步：calendar-multiget）"""

        print(f"\n=== 下载事件内容 ===")
        print(f"准备下载 {len(event_urls)} 个事件")

        if not event_urls:
            print("没有事件需要下载")
            return []

        # 构建 calendar-multiget 请求
        href_elements = ""
        for url in event_urls:
            href_elements += f"    <D:href>{url}</D:href>\n"

        multiget_body = f'''<?xml version="1.0" encoding="utf-8" ?>
<C:calendar-multiget xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
    <D:prop>
        <D:getetag />
        <C:calendar-data />
    </D:prop>
{href_elements}</C:calendar-multiget>'''

        headers = {
            'Content-Type': 'application/xml; charset=UTF-8',
            'Depth': '1'
        }

        try:
            response = requests.request(
                'REPORT',
                collection_href,
                auth=HTTPBasicAuth(self.username, self.password),
                headers=headers,
                data=multiget_body,
                timeout=30
            )

            print(f"HTTP 状态码: {response.status_code}")

            if response.status_code == 207:
                print("✅ 成功获取事件内容")
                print(f"响应长度: {len(response.text)} 字符")

                # 保存响应到临时目录
                safe_name = "".join(c for c in display_name if c.isalnum() or c in ('-', '_'))
                temp_file = self.merger.get_temp_xml_path('tencent', self.username, f'events_{safe_name}')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"事件响应已保存到 {temp_file}")

                # 解析和保存事件
                events = self.parse_and_save_events(response.text, display_name)
                return events
            else:
                print(f"获取事件内容失败: {response.text[:200]}")
                return []

        except Exception as e:
            print(f"获取事件内容异常: {e}")
            return []

    def parse_and_save_events(self, xml_data, display_name):
        """解析事件数据并保存为 ICS 文件"""

        print(f"\n--- 解析 '{display_name}' 中的事件 ---")

        events = []

        try:
            root = ET.fromstring(xml_data)
            namespaces = {
                'D': 'DAV:',
                'C': 'urn:ietf:params:xml:ns:caldav'
            }

            event_count = 0
            for response_elem in root.findall('D:response', namespaces):
                calendar_data_elem = response_elem.find('.//C:calendar-data', namespaces)
                if calendar_data_elem is not None and calendar_data_elem.text:
                    event_count += 1
                    ics_data = calendar_data_elem.text.strip()

                    # 解析事件信息
                    event_info = self.parse_ics_content(ics_data)
                    events.append(event_info)

                    print(f"\n事件 {event_count}:")
                    print(f"  标题: {event_info.get('summary', '无标题')}")
                    print(f"  开始时间: {event_info.get('dtstart', '未知')}")
                    print(f"  结束时间: {event_info.get('dtend', '未知')}")
                    if event_info.get('location'):
                        print(f"  地点: {event_info['location']}")

                    # 创建输出目录
                    output_dir = os.path.join(self.output_dir, display_name)
                    os.makedirs(output_dir, exist_ok=True)

                    # 生成文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_summary = "".join(c for c in event_info.get('summary', 'event') if c.isalnum() or c in ('-', '_'))[:50]
                    filename = f"{timestamp}_{event_count}_{safe_summary}.ics"
                    filepath = os.path.join(output_dir, filename)

                    # 保存 ICS 文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(ics_data)
                    print(f"  已保存到: {filepath}")

            if event_count == 0:
                print("未找到任何事件")
            else:
                print(f"\n✅ 总共找到并保存了 {event_count} 个事件")

            return events

        except ET.ParseError as e:
            print(f"XML 解析失败: {e}")
            return []

    def parse_ics_content(self, ics_data):
        """解析 ICS 内容提取事件信息"""

        event_info = {}
        lines = ics_data.split('\n')

        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                if key == 'SUMMARY':
                    event_info['summary'] = value
                elif key.startswith('DTSTART'):
                    event_info['dtstart'] = value
                elif key.startswith('DTEND'):
                    event_info['dtend'] = value
                elif key == 'LOCATION':
                    event_info['location'] = value
                elif key == 'DESCRIPTION':
                    event_info['description'] = value
                elif key == 'UID':
                    event_info['uid'] = value

        return event_info

    def sync(self):
        """执行同步操作"""

        print(f"=== 开始同步腾讯会议账号: {self.account.account_name} ===")

        try:
            # 步骤1: 发现集合
            collections = self.discover_collections()

            if not collections:
                print("❌ 未发现任何日历集合")
                return False

            print(f"\n发现了 {len(collections)} 个日历集合")

            # 步骤2: 处理每个集合
            total_events = 0
            for collection in collections:
                print(f"\n处理集合: {collection['name']}")

                # 获取事件列表
                event_urls = self.get_event_list(collection['href'])

                if event_urls:
                    # 下载事件内容
                    events = self.download_events(
                        collection['href'],
                        event_urls,
                        collection['name']
                    )
                    total_events += len(events)
                else:
                    print(f"集合 '{collection['name']}' 中没有事件")

            print(f"\n🎉 腾讯会议同步完成！总共下载了 {total_events} 个事件")
            print(f"所有事件已保存到 {self.output_dir}/ 目录下")

            return total_events > 0

        except Exception as e:
            print(f"❌ 腾讯会议同步过程中发生异常: {e}")
            return False

def main():
    """独立运行测试"""
    from config_manager import ConfigManager

    try:
        config_manager = ConfigManager()
        tencent_account = config_manager.get_account_by_type('tencent')

        if not tencent_account:
            print("❌ 未找到腾讯会议账号配置")
            return

        sync_handler = TencentCalDAVSync(tencent_account)
        sync_handler.sync()

    except Exception as e:
        print(f"❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main()
