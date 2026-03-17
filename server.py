#!/usr/bin/env python3
"""Four.meme 新外盘监控 - Web Server"""
import json, os, sys

try:
    from flask import Flask, jsonify, request, send_from_directory
except ImportError:
    print("安装 Flask 中...")
    os.system(f"{sys.executable} -m pip install flask requests -q")
    from flask import Flask, jsonify, request, send_from_directory

import requests as req

app = Flask(__name__, static_folder=".", static_url_path="")

API_URL = "https://four.meme/meme-api/v1/public/token/ranking"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://four.meme",
    "Referer": "https://four.meme/",
}

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/tokens")
def get_tokens():
    try:
        r = req.post(API_URL, headers=HEADERS, json={"type": "DEX"}, timeout=15)
        data = r.json()
        tokens = []
        if isinstance(data, dict):
            d = data.get("data")
            if isinstance(d, dict):
                tokens = d.get("tokens") or d.get("list") or d.get("records") or []
            elif isinstance(d, list):
                tokens = d
        elif isinstance(data, list):
            tokens = data
        if not isinstance(tokens, list):
            tokens = []
        return jsonify({"ok": True, "tokens": tokens})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "tokens": []})

@app.route("/api/dex-info")
def dex_info():
    """Query DexScreener for launch time, liquidity etc."""
    addrs = request.args.get("addrs", "")
    if not addrs:
        return jsonify({"ok": False, "data": {}})
    try:
        r = req.get(f"https://api.dexscreener.com/latest/dex/tokens/{addrs}", timeout=15)
        pairs = r.json().get("pairs") or []
        result = {}
        for p in pairs:
            base = p.get("baseToken", {}).get("address", "").lower()
            if base and base not in result:
                result[base] = {
                    "launchTime": p.get("pairCreatedAt"),
                    "liquidity": (p.get("liquidity") or {}).get("usd"),
                    "dexId": p.get("dexId"),
                    "pairAddress": p.get("pairAddress"),
                }
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "data": {}})

@app.route("/api/push", methods=["POST"])
def push_wechat():
    try:
        body = request.json
        token = body.get("pushplus_token", "")
        title = body.get("title", "")
        content = body.get("content", "")
        if not token:
            return jsonify({"ok": False, "msg": "未设置Token"})
        r = req.post("http://www.pushplus.plus/send", json={
            "token": token, "title": title, "content": content, "template": "html"
        }, timeout=10)
        return jsonify({"ok": True, "result": r.json()})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n  Four.meme 新外盘监控")
    print(f"  ====================")
    print(f"  端口: {port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
