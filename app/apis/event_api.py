from flask import Blueprint, request, jsonify
from app.database import db
import random

event_bp = Blueprint('event', __name__)

@event_bp.route('/register', methods=['POST'])
def register_event():
    """
    興行情報登録API
    イベントの基本情報を登録する
    """
    try:
        data = request.get_json()
        
        # 入力検証
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['name', 'description', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Saga テスト用: 失敗をシミュレートする場合
        if data.get('simulate_failure'):
            return jsonify({'error': 'Simulated failure in event registration'}), 500
        
        # イベント作成
        event_id = db.create_event(data)
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'message': 'Event registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/rollback/<event_id>', methods=['DELETE'])
def rollback_event(event_id):
    """
    興行情報ロールバック
    Saga失敗時の補償トランザクション
    """
    try:
        success = db.delete_event(event_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Event {event_id} rolled back successfully'
            }), 200
        else:
            return jsonify({'error': 'Event not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/<event_id>', methods=['GET'])
def get_event(event_id):
    """
    イベント情報取得
    """
    try:
        event = db.get_event(event_id)
        
        if event:
            return jsonify(event), 200
        else:
            return jsonify({'error': 'Event not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/list', methods=['GET'])
def list_events():
    """
    全イベント一覧取得
    """
    try:
        events = db.list_events()
        return jsonify({'events': events}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/health', methods=['GET'])
def health():
    """
    APIヘルスチェック
    """
    return jsonify({'status': 'Event API is healthy'}), 200