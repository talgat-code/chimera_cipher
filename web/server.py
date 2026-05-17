import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, send_file
from core import ChimeraCipher
from core.key_scheduler import KeyScheduler
from core.cipher import _feistel_f
from analysis.security_analysis import SecurityAnalyzer

app = Flask(__name__)
_HTML = os.path.join(os.path.dirname(__file__), "index.html")


@app.route("/")
def index():
    return send_file(_HTML)


@app.route("/api/encrypt", methods=["POST"])
def api_encrypt():
    d = request.get_json(force=True) or {}
    key, text = d.get("key", ""), d.get("text", "")
    if not key:  return jsonify(error="Key required"), 400
    if not text: return jsonify(error="Text required"), 400
    try:
        return jsonify(result=ChimeraCipher(key).encrypt(text))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/api/decrypt", methods=["POST"])
def api_decrypt():
    d = request.get_json(force=True) or {}
    key, ct = d.get("key", ""), d.get("ciphertext", "")
    if not key: return jsonify(error="Key required"), 400
    if not ct:  return jsonify(error="Ciphertext required"), 400
    try:
        return jsonify(result=ChimeraCipher(key).decrypt(ct))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    d = request.get_json(force=True) or {}
    try:
        sa = SecurityAnalyzer(ChimeraCipher(d.get("key", "AnalysisKey")))
        return jsonify(
            avalanche   = sa.avalanche_test(200),
            key_space   = sa.key_space_report(),
            frequency   = sa.frequency_analysis(),
            brute_force = sa.brute_force_estimate(16),
            chaos       = sa.chaos_sensitivity(),
        )
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/api/visualize")
def api_visualize():
    msg = request.args.get("msg", "Hello, CHIMERA!")
    key = request.args.get("key", "SecretKey")
    try:
        ks   = KeyScheduler(key)
        raw  = msg.encode("utf-8")
        data = (raw + b"\x00" * 16)[:16]
        blk  = [b ^ ks.pre_wk[i] for i, b in enumerate(data)]
        L, R = list(blk[:8]), list(blk[8:])
        states = [{"label": "Pre-whitening", "L": list(L), "R": list(R)}]
        for rnd in range(8):
            f    = _feistel_f(R, ks.round_keys[rnd], ks.sbox, ks.rotations[rnd])
            L, R = R, [L[i] ^ f[i] for i in range(8)]
            states.append({"label": f"Round {rnd + 1}", "L": list(L), "R": list(R)})
        return jsonify(states=states)
    except Exception as e:
        return jsonify(error=str(e)), 500
