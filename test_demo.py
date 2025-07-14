#!/usr/bin/env python3
"""
Saga Pattern Demo Test Script
Sagaパターンのデモンストレーション用テストスクリプト

このスクリプトは以下のテストを実行します:
1. サーバーの起動確認  
2. 各APIのヘルスチェック
3. 成功シナリオのテスト
4. 失敗・ロールバックシナリオのテスト
5. データベース状態の確認
"""

import requests
import time
import json
import sys
from typing import Dict, Any, Optional

class SagaDemoTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """テスト結果をログに記録"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        
        if details and not success:
            print(f"     詳細: {json.dumps(details, indent=2, ensure_ascii=False)}")
    
    def test_server_health(self) -> bool:
        """サーバーのヘルスチェック"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Server Health Check",
                    True,
                    f"サーバー起動確認: {data.get('status', 'Unknown')}"
                )
                return True
            else:
                self.log_test(
                    "Server Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Server Health Check",
                False,
                f"サーバーに接続できません: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_individual_api_health(self) -> bool:
        """個別APIのヘルスチェック"""
        apis = [
            ('Event API', '/api/event/health'),
            ('Event Details API', '/api/event-details/health'),
            ('Venue API', '/api/venue/health'),
            ('Ticket API', '/api/ticket/health'),
            ('Saga API', '/api/saga/health')
        ]
        
        all_healthy = True
        
        for api_name, endpoint in apis:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        f"{api_name} Health",
                        True,
                        f"{api_name} は正常です"
                    )
                else:
                    self.log_test(
                        f"{api_name} Health",
                        False,
                        f"HTTP {response.status_code}",
                        {'status_code': response.status_code}
                    )
                    all_healthy = False
                    
            except requests.exceptions.RequestException as e:
                self.log_test(
                    f"{api_name} Health",
                    False,
                    f"接続エラー: {str(e)}",
                    {'error': str(e)}
                )
                all_healthy = False
        
        return all_healthy
    
    def test_success_scenario(self) -> bool:
        """成功シナリオのテスト"""
        try:
            response = requests.post(
                f"{self.base_url}/demo/create-event-complete",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                
                if result.get('success'):
                    self.log_test(
                        "Success Scenario",
                        True,
                        f"全ステップ成功: Transaction ID {result.get('transaction_id')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Success Scenario",
                        False,
                        f"成功シナリオが失敗: {result.get('message')}",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Success Scenario",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Success Scenario",
                False,
                f"リクエストエラー: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_failure_rollback_scenario(self) -> bool:
        """失敗・ロールバックシナリオのテスト"""
        try:
            # イベント詳細で失敗させる
            payload = {'fail_at_step': 'event_details'}
            
            response = requests.post(
                f"{self.base_url}/demo/simulate-failure",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                
                # 失敗シナリオなので success は False であるべき
                if not result.get('success') and result.get('rollback_completed'):
                    self.log_test(
                        "Failure & Rollback Scenario",
                        True,
                        f"失敗・ロールバック成功: {data.get('failed_at_step')}で失敗、ロールバック完了"
                    )
                    return True
                else:
                    self.log_test(
                        "Failure & Rollback Scenario",
                        False,
                        f"ロールバックが期待通りに動作しませんでした",
                        data
                    )
                    return False
            else:
                self.log_test(
                    "Failure & Rollback Scenario",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Failure & Rollback Scenario",
                False,
                f"リクエストエラー: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_database_status(self) -> bool:
        """データベース状態の確認"""
        try:
            response = requests.get(
                f"{self.base_url}/demo/database-status",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', {})
                
                self.log_test(
                    "Database Status Check",
                    True,
                    f"データベース状態確認完了: 総レコード数 {summary.get('total_records', 0)}"
                )
                
                # 詳細をログ出力
                print(f"     Events: {summary.get('events_count', 0)}")
                print(f"     Event Details: {summary.get('event_details_count', 0)}")
                print(f"     Venues: {summary.get('venues_count', 0)}")
                print(f"     Tickets: {summary.get('tickets_count', 0)}")
                print(f"     Transactions: {summary.get('transactions_count', 0)}")
                
                return True
            else:
                self.log_test(
                    "Database Status Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Database Status Check",
                False,
                f"リクエストエラー: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_transaction_list(self) -> bool:
        """トランザクション一覧の確認"""
        try:
            response = requests.get(
                f"{self.base_url}/demo/list-transactions",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                transaction_count = data.get('total_transactions', 0)
                
                self.log_test(
                    "Transaction List Check",
                    True,
                    f"トランザクション一覧取得完了: {transaction_count}件"
                )
                return True
            else:
                self.log_test(
                    "Transaction List Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "Transaction List Check",
                False,
                f"リクエストエラー: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def run_all_tests(self) -> bool:
        """全テストを実行"""
        print("🚀 Saga Pattern Demo テスト開始\n")
        
        tests = [
            self.test_server_health,
            self.test_individual_api_health,
            self.test_success_scenario,
            self.test_failure_rollback_scenario,
            self.test_database_status,
            self.test_transaction_list
        ]
        
        all_passed = True
        
        for test in tests:
            result = test()
            all_passed = all_passed and result
            time.sleep(1)  # テスト間の間隔
            print()
        
        return all_passed
    
    def print_summary(self):
        """テスト結果サマリーを出力"""
        print("=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"総テスト数: {total}")
        print(f"成功: {passed}")
        print(f"失敗: {total - passed}")
        print(f"成功率: {(passed/total)*100:.1f}%" if total > 0 else "N/A")
        
        if total - passed > 0:
            print("\n❌ 失敗したテスト:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\n" + "=" * 60)

def main():
    """メイン実行関数"""
    print("Saga Pattern Demo - テストスクリプト")
    print("=" * 60)
    
    # コマンドライン引数でベースURLを指定可能
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    print(f"テスト対象: {base_url}")
    print()
    
    tester = SagaDemoTester(base_url)
    
    # 全テスト実行
    all_passed = tester.run_all_tests()
    
    # サマリー出力
    tester.print_summary()
    
    # 終了コード
    exit_code = 0 if all_passed else 1
    
    if all_passed:
        print("🎉 全てのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました。上記の詳細を確認してください。")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()