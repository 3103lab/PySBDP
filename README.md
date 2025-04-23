# PySBDP

**PySBDP** は、[Simple Binary Dictionary Protocol (SBDP)](https://github.com/3103lab/SBDP/) に準拠した Python 実装です。  
C++のバインディングではなく、**完全に Python で実装された独立バージョン**です。

---

## プロトコル仕様（SBDP）

メッセージ構造など、プロトコル仕様は C++版の [SBDP README](https://github.com/3103lab/SBDP/blob/main/README.md) を参照してください。

---

## 対応データ型

| 型       | 説明                                       |
|----------|--------------------------------------------|
| `int64`  | 8バイトの符号付き整数（big endian）         |
| `uint64` | 8バイトの符号なし整数（big endian）         |
| `float`  | 4バイト、IEEE754形式（big endian）         |
| `string` | UTF-8文字列（4バイト長付き）               |
| `binary` | バイナリデータ（4バイト長付き）            |

---

## ️ 使用例

```python
from sbdp import send_message, recv_message

message = {
    "age":   ("int64", 30),
    "uid":   ("uint64", 1234567890123456789),
    "price": ("float", 9.99),
    "name":  ("string", "Alice")
}
send_message(sock, message)
response = recv_message(sock)
```

ネストしたメッセージを `binary` フィールドとして含めることも可能です。

---

## テスト実行例

`sbdp.py` を直接実行すると、以下のようなクライアント／サーバ間の通信デモが実行されます。

```bash
$ python sbdp.py
接続: ('127.0.0.1', 50007)
サーバーで受信（外側）: ...
クライアントで受信: ...
```

---

## インストール

標準ライブラリのみで動作します。追加のパッケージは不要です。

```bash
git clone https://github.com/3103lab/PySBDP/PySBDP.git
cd PySBDP
python sbdp.py
```

---

## ライセンス

このプロジェクトは **SimpleBinaryDictionaryProtocol License v1.0** に基づいています。  

---

## 関連リポジトリ

- C++実装：[SBDP (C++)](https://github.com/3103lab/SBDP/)
