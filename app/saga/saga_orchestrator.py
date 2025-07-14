from flask import Blueprint, request, jsonify
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.database import db
from app.saga.saga_models import (
    SagaTransaction, SagaStep, SagaStepStatus, SagaTransactionStatus,
    create_event_management_saga
)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

saga_bp = Blueprint('saga', __name__)

class SagaOrchestrator:
    """
    Sagaオーケストレーター
    複数のマイクロサービスAPIを順次実行し、失敗時にはロールバックを行う
    """
    
    def __init__(self):
        self.active_transactions: Dict[str, SagaTransaction] = {}
    
    def execute_saga(self, saga_transaction: SagaTransaction) -> Dict[str, Any]:
        """
        Sagaトランザクションを実行する
        """
        logger.info(f"Starting saga execution: {saga_transaction.transaction_id}")
        
        # トランザクションをアクティブリストに追加
        self.active_transactions[saga_transaction.transaction_id] = saga_transaction
        
        # データベースにトランザクション情報を保存
        db.create_transaction({
            'id': saga_transaction.transaction_id,
            'status': saga_transaction.status.value,
            'steps': [step.name for step in saga_transaction.steps],
            'metadata': saga_transaction.metadata
        })
        
        saga_transaction.status = SagaTransactionStatus.IN_PROGRESS
        saga_transaction.updated_at = datetime.now().isoformat()
        
        try:
            # 各ステップを順次実行
            for i, step in enumerate(saga_transaction.steps):
                saga_transaction.current_step_index = i
                
                logger.info(f"Executing step {i+1}/{len(saga_transaction.steps)}: {step.name}")
                
                success = self._execute_step(step, saga_transaction)
                
                if not success:
                    logger.error(f"Step {step.name} failed. Starting rollback...")
                    
                    # 失敗時はロールバックを実行
                    saga_transaction.status = SagaTransactionStatus.COMPENSATING
                    self._execute_rollback(saga_transaction, i)
                    
                    saga_transaction.status = SagaTransactionStatus.COMPENSATED
                    
                    # データベース更新
                    db.update_transaction(saga_transaction.transaction_id, {
                        'status': saga_transaction.status.value,
                        'steps': saga_transaction.to_dict()['steps']
                    })
                    
                    return {
                        'success': False,
                        'transaction_id': saga_transaction.transaction_id,
                        'status': saga_transaction.status.value,
                        'message': f'Saga failed at step: {step.name}',
                        'failed_step': step.name,
                        'rollback_completed': True
                    }
            
            # 全ステップ成功
            saga_transaction.status = SagaTransactionStatus.COMPLETED
            saga_transaction.updated_at = datetime.now().isoformat()
            
            # データベース更新
            db.update_transaction(saga_transaction.transaction_id, {
                'status': saga_transaction.status.value,
                'steps': saga_transaction.to_dict()['steps']
            })
            
            logger.info(f"Saga completed successfully: {saga_transaction.transaction_id}")
            
            return {
                'success': True,
                'transaction_id': saga_transaction.transaction_id,
                'status': saga_transaction.status.value,
                'message': 'All steps completed successfully',
                'completed_steps': len(saga_transaction.steps)
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in saga execution: {str(e)}")
            saga_transaction.status = SagaTransactionStatus.FAILED
            
            # データベース更新
            db.update_transaction(saga_transaction.transaction_id, {
                'status': saga_transaction.status.value,
                'error': str(e)
            })
            
            return {
                'success': False,
                'transaction_id': saga_transaction.transaction_id,
                'status': saga_transaction.status.value,
                'message': f'Saga execution failed: {str(e)}'
            }
    
    def _execute_step(self, step: SagaStep, saga_transaction: SagaTransaction) -> bool:
        """
        個別ステップを実行する
        """
        step.status = SagaStepStatus.IN_PROGRESS
        
        try:
            # 前のステップの結果を使用してペイロードを更新
            payload = self._prepare_step_payload(step, saga_transaction)
            
            # HTTP APIを呼び出し
            response = requests.request(
                method=step.method,
                url=step.url,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                step.status = SagaStepStatus.COMPLETED
                step.result = response.json()
                step.completed_at = datetime.now().isoformat()
                
                logger.info(f"Step {step.name} completed successfully")
                return True
            else:
                step.status = SagaStepStatus.FAILED
                step.error = f"HTTP {response.status_code}: {response.text}"
                step.completed_at = datetime.now().isoformat()
                
                logger.error(f"Step {step.name} failed: {step.error}")
                return False
                
        except requests.exceptions.RequestException as e:
            step.status = SagaStepStatus.FAILED
            step.error = f"Request failed: {str(e)}"
            step.completed_at = datetime.now().isoformat()
            
            logger.error(f"Step {step.name} failed: {step.error}")
            return False
    
    def _prepare_step_payload(self, step: SagaStep, saga_transaction: SagaTransaction) -> Dict[str, Any]:
        """
        前のステップの結果を使用してペイロードを準備する
        """
        payload = step.payload.copy()
        
        # 前のステップの結果からIDを取得
        for completed_step in saga_transaction.get_completed_steps():
            if completed_step.result:
                if 'event_id' in completed_step.result:
                    payload['event_id'] = completed_step.result['event_id']
                if 'venue_id' in completed_step.result:
                    payload['venue_id'] = completed_step.result['venue_id']
                if 'details_id' in completed_step.result:
                    payload['details_id'] = completed_step.result['details_id']
        
        return payload
    
    def _execute_rollback(self, saga_transaction: SagaTransaction, failed_step_index: int):
        """
        失敗したステップより前の完了済みステップをロールバックする
        """
        logger.info(f"Starting rollback for transaction: {saga_transaction.transaction_id}")
        
        # 完了済みステップを逆順でロールバック
        completed_steps = saga_transaction.get_completed_steps()
        
        for step in reversed(completed_steps):
            if step.rollback_url and step.result:
                self._execute_rollback_step(step)
    
    def _execute_rollback_step(self, step: SagaStep):
        """
        個別ステップのロールバックを実行する
        """
        logger.info(f"Rolling back step: {step.name}")
        
        try:
            # ロールバックURLにIDを埋め込み
            rollback_url = step.rollback_url
            if step.result:
                for key, value in step.result.items():
                    if key.endswith('_id'):
                        rollback_url = rollback_url.replace(f"{{{key}}}", str(value))
            
            # ロールバックAPIを呼び出し
            response = requests.request(
                method=step.rollback_method,
                url=rollback_url,
                timeout=30
            )
            
            if response.status_code in [200, 204]:
                step.status = SagaStepStatus.COMPENSATED
                logger.info(f"Step {step.name} rolled back successfully")
            else:
                logger.error(f"Rollback failed for step {step.name}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Rollback request failed for step {step.name}: {str(e)}")
    
    def get_transaction_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        トランザクションの状態を取得する
        """
        if transaction_id in self.active_transactions:
            transaction = self.active_transactions[transaction_id]
            return transaction.to_dict()
        
        # データベースから取得
        db_transaction = db.get_transaction(transaction_id)
        return db_transaction

# グローバルオーケストレーターインスタンス
orchestrator = SagaOrchestrator()

@saga_bp.route('/execute', methods=['POST'])
def execute_saga():
    """
    Sagaトランザクションを実行するエンドポイント
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Sagaトランザクションを作成
        saga_transaction = create_event_management_saga(data)
        
        # Sagaを実行
        result = orchestrator.execute_saga(saga_transaction)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@saga_bp.route('/status/<transaction_id>', methods=['GET'])
def get_saga_status(transaction_id):
    """
    Sagaトランザクションの状態を取得する
    """
    try:
        status = orchestrator.get_transaction_status(transaction_id)
        
        if status:
            return jsonify(status), 200
        else:
            return jsonify({'error': 'Transaction not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@saga_bp.route('/list', methods=['GET'])
def list_saga_transactions():
    """
    全Sagaトランザクションの一覧を取得する
    """
    try:
        transactions = db.list_transactions()
        return jsonify({'transactions': transactions}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@saga_bp.route('/health', methods=['GET'])
def health():
    """
    Sagaオーケストレーターのヘルスチェック
    """
    return jsonify({
        'status': 'Saga Orchestrator is healthy',
        'active_transactions': len(orchestrator.active_transactions)
    }), 200