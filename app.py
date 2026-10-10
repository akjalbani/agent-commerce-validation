"""Flask JSON API plus shared web UI. Simulated payments only."""
import os
from flask import Flask, jsonify, request, send_from_directory
from simulator.core import Engine, SCENARIOS, run_suite, run_scenario, request_for

app = Flask(__name__, static_folder='docs', static_url_path='')
engine = Engine()

@app.get('/')
def index(): return send_from_directory('docs','index.html')

@app.get('/api/health')
def health(): return jsonify({'status':'ok','mode':'flask-simulation','real_payments':False})

@app.get('/api/scenarios')
def scenarios(): return jsonify(SCENARIOS)

@app.get('/api/suite')
def suite(): return jsonify(run_suite())

@app.post('/api/simulate')
def simulate():
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return jsonify({'error':'JSON object required'}),400
    case={'id':'custom','title':'Custom user scenario','expected':str(data.get('expected','')),
          'request':data.get('request',{}),'now':data.get('now',100)}
    if not isinstance(case['request'],dict): return jsonify({'error':'request must be an object'}),400
    return jsonify(run_scenario(case))

@app.post('/api/session/reset')
def reset():
    global engine
    engine = Engine()
    return jsonify(engine.snapshot())

@app.post('/api/session/authorize')
def authorize():
    payload=request.get_json(silent=True) or {}
    result=engine.authorize(payload.get('request',{}),payload.get('now',100))
    return jsonify({'result':result,'snapshot':engine.snapshot()})

@app.post('/api/session/transition')
def transition():
    payload=request.get_json(silent=True) or {}
    txn=str(payload.get('txn',''))
    action=payload.get('action')
    if action=='submit': result=engine.submit(txn)
    elif action=='uncertain': result=engine.uncertain(txn)
    elif action=='confirm': result=engine.settle(txn,'CONFIRMED')
    elif action=='fail': result=engine.settle(txn,'FAILED')
    else: return jsonify({'error':'invalid action'}),400
    return jsonify({'result':result,'snapshot':engine.snapshot()})

if __name__ == '__main__':
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5000')),debug=False)
