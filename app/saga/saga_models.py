from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid
from datetime import datetime

class SagaStepStatus(Enum):
    """Sagaステップの状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

class SagaTransactionStatus(Enum):
    """Sagaトランザクション全体の状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    """Sagaの1ステップを表すクラス"""
    step_id: str
    name: str
    url: str
    method: str = "POST"
    payload: Dict[str, Any] = None
    rollback_url: str = None
    rollback_method: str = "DELETE"
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = None
    completed_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.payload is None:
            self.payload = {}

@dataclass
class SagaTransaction:
    """Sagaトランザクション全体を表すクラス"""
    transaction_id: str
    name: str
    steps: List[SagaStep]
    status: SagaTransactionStatus = SagaTransactionStatus.PENDING
    current_step_index: int = 0
    metadata: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def get_current_step(self) -> Optional[SagaStep]:
        """現在実行中のステップを取得"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_completed_steps(self) -> List[SagaStep]:
        """完了済みのステップ一覧を取得"""
        return [step for step in self.steps if step.status == SagaStepStatus.COMPLETED]
    
    def is_completed(self) -> bool:
        """全ステップが完了したかチェック"""
        return all(step.status == SagaStepStatus.COMPLETED for step in self.steps)
    
    def has_failed_step(self) -> bool:
        """失敗したステップがあるかチェック"""
        return any(step.status == SagaStepStatus.FAILED for step in self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（シリアライゼーション用）"""
        return {
            'transaction_id': self.transaction_id,
            'name': self.name,
            'status': self.status.value,
            'current_step_index': self.current_step_index,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'steps': [
                {
                    'step_id': step.step_id,
                    'name': step.name,
                    'url': step.url,
                    'method': step.method,
                    'payload': step.payload,
                    'rollback_url': step.rollback_url,
                    'rollback_method': step.rollback_method,
                    'status': step.status.value,
                    'result': step.result,
                    'error': step.error,
                    'created_at': step.created_at,
                    'completed_at': step.completed_at
                }
                for step in self.steps
            ]
        }

def create_event_management_saga(event_data: Dict[str, Any]) -> SagaTransaction:
    """
    イベント管理システム用のSagaトランザクションを作成する
    4つのAPIを順次実行するSagaパターン
    """
    transaction_id = str(uuid.uuid4())
    
    # 各ステップのペイロードを準備
    event_payload = {
        'name': event_data.get('name', 'Sample Event'),
        'description': event_data.get('description', 'Sample event description'),
        'date': event_data.get('date', '2024-12-31'),
        'simulate_failure': event_data.get('fail_at_step') == 'event'
    }
    
    venue_payload = {
        'name': event_data.get('venue_name', 'Sample Venue'),
        'address': event_data.get('venue_address', 'Tokyo, Japan'),
        'capacity': event_data.get('venue_capacity', 1000),
        'facilities': event_data.get('venue_facilities', ['Stage', 'Sound System']),
        'simulate_failure': event_data.get('fail_at_step') == 'venue'
    }
    
    steps = [
        SagaStep(
            step_id=str(uuid.uuid4()),
            name="Event Registration",
            url="http://localhost:5000/api/event/register",
            payload=event_payload,
            rollback_url="http://localhost:5000/api/event/rollback/{event_id}",
            rollback_method="DELETE"
        ),
        SagaStep(
            step_id=str(uuid.uuid4()),
            name="Event Details Registration", 
            url="http://localhost:5000/api/event-details/register",
            payload={
                'detailed_description': event_data.get('detailed_description', 'Detailed description of the event'),
                'duration': event_data.get('duration', 120),
                'category': event_data.get('category', 'Entertainment'),
                'requirements': event_data.get('requirements', ['Tickets required', 'Age 18+']),
                'simulate_failure': event_data.get('fail_at_step') == 'event_details'
            },
            rollback_url="http://localhost:5000/api/event-details/rollback/{details_id}",
            rollback_method="DELETE"
        ),
        SagaStep(
            step_id=str(uuid.uuid4()),
            name="Venue Registration",
            url="http://localhost:5000/api/venue/register", 
            payload=venue_payload,
            rollback_url="http://localhost:5000/api/venue/rollback/{venue_id}",
            rollback_method="DELETE"
        ),
        SagaStep(
            step_id=str(uuid.uuid4()),
            name="Ticket Registration",
            url="http://localhost:5000/api/ticket/register",
            payload={
                'ticket_type': event_data.get('ticket_type', 'General Admission'),
                'price': event_data.get('ticket_price', 5000),
                'quantity': event_data.get('ticket_quantity', 500),
                'simulate_failure': event_data.get('fail_at_step') == 'ticket'
            },
            rollback_url="http://localhost:5000/api/ticket/rollback/{ticket_id}",
            rollback_method="DELETE"
        )
    ]
    
    return SagaTransaction(
        transaction_id=transaction_id,
        name="Event Management Saga",
        steps=steps,
        metadata=event_data
    )