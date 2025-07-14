from flask import Blueprint, request, jsonify
from app.database import db

event_details_bp = Blueprint('event_details', __name__)

@event_details_bp.route('/register', methods=['POST'])
def register_event_details():
    """
    興行詳細情報登録API
    イベントの詳細情報を登録する
    """
    try:
        data = request.get_json()
        
        # 入力検証
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['event_id', 'detailed_description', 'duration', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # 関連するイベントが存在するか確認
        event = db.get_event(data['event_id'])
        if not event:
            return jsonify({'error': 'Related event not found'}), 400
        
        # Saga テスト用: 失敗をシミュレートする場合
        if data.get('simulate_failure'):
            return jsonify({'error': 'Simulated failure in event details registration'}), 500
        
        # イベント詳細作成
        details_id = db.create_event_details(data['event_id'], data)
        
        return jsonify({
            'success': True,
            'details_id': details_id,
            'event_id': data['event_id'],
            'message': 'Event details registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_details_bp.route('/rollback/<details_id>', methods=['DELETE'])
def rollback_event_details(details_id):
    """
    興行詳細情報ロールバック
    Saga失敗時の補償トランザクション
    """
    try:
        success = db.delete_event_details(details_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Event details {details_id} rolled back successfully'
            }), 200
        else:
            return jsonify({'error': 'Event details not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_details_bp.route('/<details_id>', methods=['GET'])
def get_event_details(details_id):
    """
    イベント詳細情報取得
    """
    try:
        details = db.get_event_details(details_id)
        
        if details:
            return jsonify(details), 200
        else:
            return jsonify({'error': 'Event details not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_details_bp.route('/list', methods=['GET'])
def list_event_details():
    """
    全イベント詳細一覧取得
    """
    try:
        details_list = db.list_event_details()
        return jsonify({'event_details': details_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_details_bp.route('/health', methods=['GET'])
def health():
    """
    APIヘルスチェック
    """
    return jsonify({'status': 'Event Details API is healthy'}), 200