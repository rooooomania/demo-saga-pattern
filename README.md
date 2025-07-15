# Saga パターン デモ実装

このプロジェクトは、Python と Flask を使用した Saga パターンのオーケストレーター実装のデモンストレーションです。

## 概要

イベント管理システムを例に、複数のマイクロサービス API を順次実行し、失敗時には自動的にロールバック（補償トランザクション）を行う Saga パターンを実装しています。

### アーキテクチャ

```
Saga Coordinator ─┬─▶ Event API ──────────▶ Database
                  ├─▶ Event Details API ──▶ Database
                  ├─▶ Venue API ──────────▶ Database
                  └─▶ Ticket API ─────────▶ Database
                       ↓ (失敗時)
                   逆順でロールバック実行
```

## 含まれるマイクロサービス

1. **興行情報登録 API** (`/api/event`) - イベントの基本情報を登録
2. **興行詳細情報登録 API** (`/api/event-details`) - イベントの詳細情報を登録
3. **会場情報登録 API** (`/api/venue`) - 会場情報を登録
4. **チケット券面登録 API** (`/api/ticket`) - チケット情報を登録

## 主要機能

### ✅ Saga オーケストレーター

- 4 つのマイクロサービスを順次実行
- 失敗時の自動ロールバック
- トランザクション状態の追跡
- 詳細なログ出力

### ✅ 共有データベースシミュレーション

- インメモリデータベース
- スレッドセーフ操作
- 全てのデータ操作とトランザクション履歴を管理

### ✅ デモエンドポイント

- 成功シナリオのテスト
- 失敗・ロールバックシナリオのテスト
- 個別 API 動作確認
- データベース状態確認

## セットアップと実行

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. アプリケーションの起動

```bash
python main.py
```

サーバーは `http://localhost:5000` で起動します。

### 3. 動作確認

ヘルスチェック:

```bash
curl http://localhost:5000/
```

## 使用方法

### 成功シナリオのテスト

全ステップが正常に完了するケース:

```bash
curl -X POST http://localhost:5000/demo/create-event-complete
```

### 失敗・ロールバックシナリオのテスト

特定のステップで失敗させてロールバックをテスト:

```bash
# イベント詳細登録で失敗
curl -X POST http://localhost:5000/demo/simulate-failure \
  -H "Content-Type: application/json" \
  -d '{"fail_at_step": "event_details"}'

# 他の失敗ポイント: "event", "venue", "ticket"
```

### トランザクション状態の確認

```bash
# 全トランザクション一覧
curl http://localhost:5000/demo/list-transactions

# データベース状態確認
curl http://localhost:5000/demo/database-status

# 全APIヘルスチェック
curl http://localhost:5000/demo/health-check-all
```

### 個別 API 動作確認

```bash
curl -X POST http://localhost:5000/demo/test-individual-apis
```

## Saga 実行フロー

### 正常フロー

1. **Event Registration** → Event ID 取得
2. **Event Details Registration** → Details ID 取得（Event ID 使用）
3. **Venue Registration** → Venue ID 取得
4. **Ticket Registration** → Ticket ID 取得（Event ID, Venue ID 使用）

### 失敗時のロールバックフロー

1. 失敗したステップを検出
2. **Saga 状態を "COMPENSATING" に変更**
3. **完了済みステップを逆順でロールバック実行**:
   - Ticket API rollback (DELETE /api/ticket/rollback/{ticket_id})
   - Venue API rollback (DELETE /api/venue/rollback/{venue_id})
   - Event Details API rollback (DELETE /api/event-details/rollback/{details_id})
   - Event API rollback (DELETE /api/event/rollback/{event_id})
4. **Saga 状態を "COMPENSATED" に変更**

## API 仕様

### Saga オーケストレーター API

#### Saga 実行

```
POST /api/saga/execute
Content-Type: application/json

{
  "name": "イベント名",
  "description": "イベント説明",
  "date": "2024-12-31",
  "fail_at_step": "event_details"  // テスト用（オプション）
}
```

#### Saga 状態確認

```
GET /api/saga/status/{transaction_id}
```

#### 全 Saga 一覧

```
GET /api/saga/list
```

### 個別マイクロサービス API

#### イベント登録

```
POST /api/event/register
{
  "name": "イベント名",
  "description": "説明",
  "date": "2024-12-31"
}
```

#### イベント詳細登録

```
POST /api/event-details/register
{
  "event_id": "uuid",
  "detailed_description": "詳細説明",
  "duration": 120,
  "category": "カテゴリ"
}
```

#### 会場登録

```
POST /api/venue/register
{
  "name": "会場名",
  "address": "住所",
  "capacity": 1000
}
```

#### チケット登録

```
POST /api/ticket/register
{
  "event_id": "uuid",
  "venue_id": "uuid",
  "ticket_type": "一般",
  "price": 5000,
  "quantity": 500
}
```

### ロールバック API

各マイクロサービスは対応するロールバックエンドポイントを持ちます:

```
DELETE /api/event/rollback/{event_id}
DELETE /api/event-details/rollback/{details_id}
DELETE /api/venue/rollback/{venue_id}
DELETE /api/ticket/rollback/{ticket_id}
```

## ファイル構成

```
demo-saga-pattern/
├── main.py                     # アプリケーションエントリーポイント
├── requirements.txt            # Python依存関係
├── README.md                   # このファイル
└── app/
    ├── __init__.py
    ├── database.py             # 共有データベースシミュレーション
    ├── apis/                   # マイクロサービスAPI群
    │   ├── __init__.py
    │   ├── event_api.py        # 興行情報登録API
    │   ├── event_details_api.py # 興行詳細情報登録API
    │   ├── venue_api.py        # 会場情報登録API
    │   └── ticket_api.py       # チケット券面登録API
    ├── saga/                   # Sagaオーケストレーター
    │   ├── __init__.py
    │   ├── saga_models.py      # Sagaデータモデル
    │   └── saga_orchestrator.py # オーケストレーター実装
    └── demo/                   # デモエンドポイント
        ├── __init__.py
        └── demo_endpoints.py   # テスト用エンドポイント
```

## 技術仕様

- **言語**: Python 3.7+
- **フレームワーク**: Flask
- **HTTP クライアント**: requests
- **データベース**: インメモリ（本番環境では PostgreSQL/MySQL 等を使用）
- **並行制御**: threading.Lock

## 拡張可能性

この実装は以下の点で拡張可能です:

1. **実際のデータベース接続**: PostgreSQL, MySQL 等への変更
2. **非同期処理**: asyncio/aiohttp を使用した非同期 Saga 実行
3. **メッセージキュー**: RabbitMQ, Apache Kafka 等との統合
4. **監視**: Prometheus, Grafana 等でのメトリクス監視
5. **認証・認可**: JWT token, OAuth 等のセキュリティ強化
6. **コンテナ化**: Docker, Kubernetes でのデプロイメント

## トラブルシューティング

### よくある問題

1. **ポート 5000 が使用中**:

   ```bash
   # ポート使用状況確認
   lsof -i :5000

   # プロセス終了
   kill -9 <PID>
   ```

2. **依存関係エラー**:

   ```bash
   # 仮想環境を作成して実行
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **API 呼び出しエラー**:
   - サーバーが起動していることを確認
   - ヘルスチェックエンドポイントで各 API の状態を確認

## ライセンス

このプロジェクトはデモンストレーション目的です。商用利用については適切なライセンスを確認してください。
