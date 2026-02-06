# SPDX-License-Identifier: LicenseRef-SBPD-1.0
# SimpleBinaryDictionaryProtocol encoder/decoder
# Copyright (c) 2025 Hikari Satoh
"""
sbdp.py

Simple Binary Dictionary Protocol (SBDP) ライブラリ

このライブラリは、ネストを考慮しない平坦な連想配列（辞書）をシリアライズ／デシリアライズするための機能を提供します。
対応する型は以下の通りです:
  - int64   : 8バイト（符号付き64ビット整数）
  - uint64  : 8バイト（符号なし64ビット整数）
  - float64 : 8バイト（IEEE754形式の浮動小数点数）
  - string  : 先に4バイトの長さ情報、その後UTF-8エンコードされた文字列
  - binary  : 先に4バイトの長さ情報、その後バイナリデータ本体

各フィールドは以下の形式でエンコードされます:
  - キー: 2バイトの長さ情報 (unsigned short, ネットワークバイトオーダー) + キー文字列 (UTF-8)
  - 型コード: 1バイト
      1 : int64
      2 : uint64
      3 : float64
      4 : string
      5 : binary
  - 値: 型に応じたバイナリ表現

メッセージ全体は、先頭に4バイト（ネットワークバイトオーダー）のペイロード長が付加されます。

使用例:
  >>> from sbdp import send_message, recv_message
  >>> # ソケットを利用した送受信例（クライアント側など）
  >>> message = {
  ...     "age":   ("int64",   30),
  ...     "uid":   ("uint64",  1234567890123456789),
  ...     "price": ("float64", 9.99),
  ...     "name":  ("string",  "Alice")
  ... }
  >>> send_message(sock, message)
  >>> response = recv_message(sock)
"""

import struct
import socket

# 型コードの定義
TYPE_INT64   = 1
TYPE_UINT64  = 2
TYPE_FLOAT64 = 3
TYPE_STRING  = 4
TYPE_BINARY  = 5

# Protocol numeric fields are encoded in network byte order (big endian).
FMT_U8 = '!B'
FMT_U16 = '!H'
FMT_U32 = '!I'
FMT_I64 = '!q'
FMT_U64 = '!Q'
FMT_F64 = '!d'

def encode_message(data):
    """
    メッセージをエンコードする

    Args:
      data (dict): キーが文字列、値が (type_str, value) のタプルからなる辞書。
                   type_strは "int64", "uint64", "float", "string" のいずれか。

    Returns:
      bytes: エンコードされたメッセージ。先頭4バイトはペイロード長。
    """
    parts = []
    for key, (typ, value) in data.items():
        key_bytes = key.encode('utf-8')
        key_length = len(key_bytes)
        # キー長（2バイト、ネットワークバイトオーダー）
        parts.append(struct.pack(FMT_U16, key_length))
        parts.append(key_bytes)
        # 型コード（1バイト）および値
        if typ == "int64":
            parts.append(struct.pack(FMT_U8, TYPE_INT64))
            parts.append(struct.pack(FMT_I64, value))
        elif typ == "uint64":
            parts.append(struct.pack(FMT_U8, TYPE_UINT64))
            parts.append(struct.pack(FMT_U64, value))
        elif typ == "float64":
            parts.append(struct.pack(FMT_U8, TYPE_FLOAT64))
            parts.append(struct.pack(FMT_F64, value))
        elif typ == "string":
            parts.append(struct.pack(FMT_U8, TYPE_STRING))
            value_bytes = value.encode('utf-8')
            parts.append(struct.pack(FMT_U32, len(value_bytes)))  # 4バイトの文字列長
            parts.append(value_bytes)
        elif typ == "binary":
            parts.append(struct.pack(FMT_U8, TYPE_BINARY))
            parts.append(struct.pack(FMT_U32, len(value)))
            parts.append(value)
        else:
            raise ValueError(f"不明な型: {typ}")
    payload = b"".join(parts)
    header = struct.pack(FMT_U32, len(payload))
    return header + payload

def decode_message(message_bytes):
    """
    エンコードされたメッセージをデコードする

    Args:
      message_bytes (bytes): エンコードされたメッセージ。先頭4バイトはペイロード長。

    Returns:
      dict: キーが文字列、値が (type_str, value) のタプルからなる辞書。
    """
    if len(message_bytes) < 4:
        raise ValueError("メッセージが短すぎます")
    total_length = struct.unpack(FMT_U32, message_bytes[:4])[0]
    if len(message_bytes) < 4 + total_length:
        raise ValueError("不完全なメッセージです")
    payload = message_bytes[4:4+total_length]
    offset = 0
    result = {}
    while offset < len(payload):
        # キーの長さ（2バイト）
        key_length = struct.unpack(FMT_U16, payload[offset:offset+2])[0]
        offset += 2
        key = payload[offset:offset+key_length].decode('utf-8')
        offset += key_length
        # 型コード（1バイト）
        type_code = struct.unpack(FMT_U8, payload[offset:offset+1])[0]
        offset += 1
        if type_code == TYPE_INT64:
            value = struct.unpack(FMT_I64, payload[offset:offset+8])[0]
            offset += 8
            result[key] = ("int64", value)
        elif type_code == TYPE_UINT64:
            value = struct.unpack(FMT_U64, payload[offset:offset+8])[0]
            offset += 8
            result[key] = ("uint64", value)
        elif type_code == TYPE_FLOAT64:
            value = struct.unpack(FMT_F64, payload[offset:offset+8])[0]
            offset += 8
            result[key] = ("float64", value)
        elif type_code == TYPE_STRING:
            str_length = struct.unpack(FMT_U32, payload[offset:offset+4])[0]
            offset += 4
            value = payload[offset:offset+str_length].decode('utf-8')
            offset += str_length
            result[key] = ("string", value)
        elif type_code == TYPE_BINARY:
            bin_length = struct.unpack(FMT_U32, payload[offset:offset+4])[0]
            offset += 4
            value = payload[offset:offset+bin_length]
            offset += bin_length
            result[key] = ("binary", value)
        else:
            raise ValueError("不明な型コード")
    return result

def recvall(sock, n):
    """
    ソケットから指定されたバイト数を確実に受信する

    Args:
      sock (socket.socket): ソケット
      n (int): 受信したいバイト数

    Returns:
      bytes: 受信したバイト列
    """
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return data
        data += packet
    return data

def send_message(sock, data):
    """
    ソケットにメッセージを送信する

    Args:
      sock (socket.socket): 接続済みのソケット
      data (dict): エンコードするメッセージ
    """
    message = encode_message(data)
    sock.sendall(message)

def recv_message(sock):
    """
    ソケットからメッセージを受信する

    Args:
      sock (socket.socket): 接続済みのソケット

    Returns:
      dict: 受信したメッセージのデコード結果
    """
    header = recvall(sock, 4)
    if len(header) < 4:
        raise RuntimeError("ヘッダの受信に失敗しました")
    total_length = struct.unpack(FMT_U32, header)[0]
    payload = recvall(sock, total_length)
    if len(payload) < total_length:
        raise RuntimeError("ペイロードの受信に失敗しました")
    return decode_message(header + payload)

# 以下、テスト用の使用例（モジュール単体で実行した場合のみ動作）
if __name__ == '__main__':
    import threading

    def server():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(('localhost', 50007))
        srv.listen(1)
        conn, addr = srv.accept()
        print("接続:", addr)

        outer_msg = recv_message(conn)
        print("サーバーで受信（外側）:", outer_msg)

        if "payload" in outer_msg and outer_msg["payload"][0] == "binary":
            inner_bytes = outer_msg["payload"][1]
            inner_msg = decode_message(inner_bytes)
            print("サーバーで受信（内側）:", inner_msg)
        else:
            print("ネストされたメッセージが見つかりません")

        response = {"status": ("string", "OK")}
        send_message(conn, response)
        conn.close()
        srv.close()

    def client():
        cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli.connect(('localhost', 50007))

        inner_message = {
            "uid":   ("uint64", 9876543210),
            "note":  ("string", "nested payload"),
        }
        inner_bytes = encode_message(inner_message)
        outer_message = {
            "payload": ("binary", inner_bytes)
        }

        send_message(cli, outer_message)
        resp = recv_message(cli)
        print("クライアントで受信:", resp)
        cli.close()

    server_thread = threading.Thread(target=server, daemon=True)
    server_thread.start()
    client_thread = threading.Thread(target=client, daemon=True)
    client_thread.start()
    server_thread.join()
    client_thread.join()
