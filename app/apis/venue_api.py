from flask import Blueprint, request, jsonify
from app.database import db

venue_bp = Blueprint('venue', __name__)

@venue_bp.route('/register', methods=['POST'])
def register_venue():
    """
    会場情報登録API
    イベント会場の情報を登録する
    """
    try:
        data = request.get_json()
        
        # 入力検証
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['name', 'address', 'capacity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Saga テスト用: 失敗をシミュレートする場合
        if data.get('simulate_failure'):
            return jsonify({'error': 'Simulated failure in venue registration'}), 500
        
        # 会場作成
        venue_id = db.create_venue(data)
        
        return jsonify({
            'success': True,
            'venue_id': venue_id,
            'message': 'Venue registered successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@venue_bp.route('/rollback/<venue_id>', methods=['DELETE'])
def rollback_venue(venue_id):
    """
    会場情報ロールバック
    Saga失敗時の補償トランザクション
    """
    try:
        success = db.delete_venue(venue_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Venue {venue_id} rolled back successfully'
            }), 200
        else:
            return jsonify({'error': 'Venue not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@venue_bp.route('/<venue_id>', methods=['GET'])
def get_venue(venue_id):
    """
    会場情報取得
    """
    try:
        venue = db.get_venue(venue_id)
        
        if venue:
            return jsonify(venue), 200
        else:
            return jsonify({'error': 'Venue not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@venue_bp.route('/list', methods=['GET'])
def list_venues():
    """
    全会場一覧取得
    """
    try:
        venues = db.list_venues()
        return jsonify({'venues': venues}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@venue_bp.route('/health', methods=['GET'])
def health():
    """
    APIヘルスチェック
    """
    return jsonify({'status': 'Venue API is healthy'}), 200