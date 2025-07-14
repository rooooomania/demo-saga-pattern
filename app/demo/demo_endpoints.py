from flask import Blueprint, request, jsonify
from app.database import db
from app.saga.saga_orchestrator import orchestrator
from app.saga.saga_models import create_event_management_saga
import requests

demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/create-event-complete', methods=['POST'])
def demo_create_event_complete():
    """
    デモ: 全ステップ成功シナリオ
    イベント作成から全ての関連情報登録まで成功するケース
    """
    try:
        # サンプルデータで完全な イベント作成Sagaを実行
        sample_data = {
            'name': '東京音楽祭2024',
            'description': '年次開催の大規模音楽フェスティバル',
            'date': '2024-08-15',
            'detailed_description': '国内外のアーティストが出演する3日間の音楽祭。ロック、ポップ、電子音楽など様々なジャンルを楽しめます。',
            'duration': 180,
            'category': 'Music Festival',
            'requirements': ['チケット必須', '年齢制限なし', '飲食物持込可'],
            'venue_name': '東京国際展示場',
            'venue_address': '東京都江東区有明3-11-1',
            'venue_capacity': 10000,
            'venue_facilities': ['メインステージ', '音響設備', '照明設備', '駐車場'],
            'ticket_type': '一般入場券',
            'ticket_price': 8000,
            'ticket_quantity': 5000
        }
        
        # Sagaトランザクションを作成・実行
        saga_transaction = create_event_management_saga(sample_data)
        result = orchestrator.execute_saga(saga_transaction)
        
        return jsonify({
            'demo_scenario': 'Complete Success',
            'description': '全ステップが正常に完了するシナリオ',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/simulate-failure', methods=['POST'])
def demo_simulate_failure():
    """
    デモ: 失敗・ロールバックシナリオ  
    指定されたステップで意図的に失敗させ、ロールバックを実行
    """
    try:
        data = request.get_json() or {}
        
        # 失敗させるステップを指定（デフォルトは event_details）
        fail_at_step = data.get('fail_at_step', 'event_details')
        
        sample_data = {
            'name': 'テスト失敗イベント',
            'description': 'ロールバックテスト用のイベント',
            'date': '2024-09-20',
            'detailed_description': 'このイベントは意図的に失敗させてロールバック機能をテストします',
            'duration': 120,
            'category': 'Test Event',
            'requirements': ['テスト用'],
            'venue_name': 'テスト会場',
            'venue_address': 'テスト住所',
            'venue_capacity': 100,
            'venue_facilities': ['テスト設備'],
            'ticket_type': 'テストチケット',
            'ticket_price': 1000,
            'ticket_quantity': 50,
            'fail_at_step': fail_at_step  # 失敗ポイントを指定
        }
        
        # Sagaトランザクションを作成・実行
        saga_transaction = create_event_management_saga(sample_data)
        result = orchestrator.execute_saga(saga_transaction)
        
        return jsonify({
            'demo_scenario': 'Failure and Rollback',
            'description': f'{fail_at_step}ステップで失敗し、ロールバックを実行するシナリオ',
            'failed_at_step': fail_at_step,
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/test-individual-apis', methods=['POST'])
def demo_test_individual_apis():
    """
    デモ: 個別API動作確認
    各マイクロサービスAPIを個別に呼び出してテスト
    """
    try:
        results = {}
        base_url = 'http://localhost:5000'
        
        # 1. イベント登録APIテスト
        event_data = {
            'name': 'APIテストイベント',
            'description': '個別APIテスト用',
            'date': '2024-10-01'
        }
        event_response = requests.post(f'{base_url}/api/event/register', json=event_data)
        results['event_api'] = {
            'status': event_response.status_code,
            'data': event_response.json() if event_response.status_code == 201 else None
        }
        
        if event_response.status_code == 201:
            event_id = event_response.json().get('event_id')
            
            # 2. イベント詳細登録APIテスト
            details_data = {
                'event_id': event_id,
                'detailed_description': 'APIテスト用詳細情報',
                'duration': 90,
                'category': 'Test'
            }
            details_response = requests.post(f'{base_url}/api/event-details/register', json=details_data)
            results['event_details_api'] = {
                'status': details_response.status_code,
                'data': details_response.json() if details_response.status_code == 201 else None
            }
        
        # 3. 会場登録APIテスト
        venue_data = {
            'name': 'テスト会場',
            'address': 'テスト住所 123',
            'capacity': 200
        }
        venue_response = requests.post(f'{base_url}/api/venue/register', json=venue_data)
        results['venue_api'] = {
            'status': venue_response.status_code,
            'data': venue_response.json() if venue_response.status_code == 201 else None
        }
        
        # 4. チケット登録APIテスト（イベントIDと会場IDが必要）
        if (event_response.status_code == 201 and venue_response.status_code == 201):
            ticket_data = {
                'event_id': event_response.json().get('event_id'),
                'venue_id': venue_response.json().get('venue_id'),
                'ticket_type': 'テストチケット',
                'price': 1500,
                'quantity': 100
            }
            ticket_response = requests.post(f'{base_url}/api/ticket/register', json=ticket_data)
            results['ticket_api'] = {
                'status': ticket_response.status_code,
                'data': ticket_response.json() if ticket_response.status_code == 201 else None
            }
        
        return jsonify({
            'demo_scenario': 'Individual API Testing',
            'description': '各マイクロサービスAPIの個別動作確認',
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/list-transactions', methods=['GET'])
def demo_list_transactions():
    """
    デモ: 全Sagaトランザクション一覧表示
    """
    try:
        transactions = db.list_transactions()
        
        return jsonify({
            'demo_scenario': 'Transaction List',
            'description': '実行された全Sagaトランザクションの一覧',
            'total_transactions': len(transactions),
            'transactions': transactions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/database-status', methods=['GET'])
def demo_database_status():
    """
    デモ: データベース状態確認
    各テーブルのレコード数と内容を表示
    """
    try:
        status = db.get_database_status()
        
        # 詳細データも取得
        details = {
            'events': db.list_events(),
            'event_details': db.list_event_details(),
            'venues': db.list_venues(),
            'tickets': db.list_tickets(),
            'transactions': db.list_transactions()
        }
        
        return jsonify({
            'demo_scenario': 'Database Status',
            'description': '共有データベースの現在の状態',
            'summary': status,
            'details': details
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/clear-database', methods=['DELETE'])
def demo_clear_database():
    """
    デモ: データベースクリア
    テスト用にデータベースを初期化
    """
    try:
        # データベースの各テーブルをクリア
        db.events.clear()
        db.event_details.clear()
        db.venues.clear()
        db.tickets.clear()
        db.transactions.clear()
        
        return jsonify({
            'demo_scenario': 'Database Clear',
            'description': 'データベースを初期化しました',
            'message': 'All data cleared successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/health-check-all', methods=['GET'])
def demo_health_check_all():
    """
    デモ: 全APIのヘルスチェック
    """
    try:
        base_url = 'http://localhost:5000'
        health_results = {}
        
        # 各APIのヘルスチェック
        apis = [
            ('main', '/'),
            ('event', '/api/event/health'),
            ('event_details', '/api/event-details/health'),
            ('venue', '/api/venue/health'),
            ('ticket', '/api/ticket/health'),
            ('saga', '/api/saga/health')
        ]
        
        for api_name, endpoint in apis:
            try:
                response = requests.get(f'{base_url}{endpoint}', timeout=5)
                health_results[api_name] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_code': response.status_code,
                    'data': response.json() if response.status_code == 200 else None
                }
            except requests.exceptions.RequestException as e:
                health_results[api_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        overall_health = all(result.get('status') == 'healthy' for result in health_results.values())
        
        return jsonify({
            'demo_scenario': 'Health Check All APIs',
            'description': '全てのAPIとサービスのヘルスチェック',
            'overall_status': 'healthy' if overall_health else 'unhealthy',
            'individual_results': health_results
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/', methods=['GET'])
def demo_index():
    """
    デモ: 利用可能なエンドポイント一覧
    """
    endpoints = [
        {
            'path': '/demo/create-event-complete',
            'method': 'POST',
            'description': '全ステップ成功シナリオのテスト'
        },
        {
            'path': '/demo/simulate-failure',
            'method': 'POST',
            'description': '失敗・ロールバックシナリオのテスト',
            'params': {'fail_at_step': 'event|event_details|venue|ticket'}
        },
        {
            'path': '/demo/test-individual-apis',
            'method': 'POST',
            'description': '個別API動作確認テスト'
        },
        {
            'path': '/demo/list-transactions',
            'method': 'GET',
            'description': 'Sagaトランザクション一覧表示'
        },
        {
            'path': '/demo/database-status',
            'method': 'GET',
            'description': 'データベース状態確認'
        },
        {
            'path': '/demo/clear-database',
            'method': 'DELETE',
            'description': 'データベース初期化'
        },
        {
            'path': '/demo/health-check-all',
            'method': 'GET',
            'description': '全APIヘルスチェック'
        }
    ]
    
    return jsonify({
        'title': 'Saga Pattern Demo - Available Endpoints',
        'description': 'Sagaパターンのデモンストレーション用エンドポイント一覧',
        'endpoints': endpoints
    }), 200