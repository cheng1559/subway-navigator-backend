from BeijingSubway import BeijingSubway
from sys import stderr
from flask import Flask, jsonify, request
from flask_cors import CORS

PORT = 8080

app = Flask(__name__)
CORS(app)

subway = BeijingSubway()
if not subway.read_info('subway_data.json'):
    print('Error: read lines information failed!', file=stderr)
    exit(1)


@app.route('/fetch', methods=['GET'])
def get_stations():
    return jsonify(subway.get_all_stations())


@app.route('/fetchLine', methods=['GET'])
def get_lines():
    return jsonify(subway.get_all_lines())


@app.route('/query', methods=['GET'])
def query():
    type = request.args.get('type')
    station_from = request.args.get('station_from')
    station_to = request.args.get('station_to')
    try:
        print('type', type)
        if type == 'transfer':
            path, info = subway.minimum_transfer_path(station_from, station_to)
        elif type == 'time':
            path, info = subway.shortest_time_path(station_from, station_to)
        else:
            raise Exception('Invalid type')
        path_list = []
        for i in range(0, len(path)):
            if i == 0:
                path_list.append({'name': '乘坐地铁{}'.format(path[i].line), 'time': None, 'transfer': None, 'isTransfer': True})
            if i > 0 and path[i].line != path[i - 1].line:
                path_list.append({'name': '换乘地铁{}'.format(path[i].line), 'time': info[i].time, 'transfer': info[i].transfer_count, 'isTransfer': True})
            if i % 2 == 0:
                path_list.append({'name': path[i].name, 'time': info[i].time, 'transfer': info[i].transfer_count, 'isTransfer': False})
        if len(path_list) == 0:
            path_list.append({'name': '无法到达', 'time': None, 'transfer': None, 'isTransfer': True})
    except Exception as e:
        print('Error:', e, file=stderr)
        path_list = []
    finally:
        return jsonify(path_list)
    

@app.route('/addLine', methods=['POST'])
def add_line():
    line = request.json['name']
    distances = request.json['distances']
    speed = request.json['speed']
    loop = request.json['loop']
    stations = request.json['stations']
    try:
        subway.add_line(line, stations, distances, speed, loop)
        print('Added successfully')
        return jsonify({'status': 200})
    except Exception as e:
        print('Error:', e, file=stderr)
        return jsonify({'status': 400, 'error': str(e)})


@app.route('/deleteLine', methods=['POST'])
def delete_line():
    line = request.json['line']
    try:
        subway.remove_line(line)
        return jsonify({'msg': 'ok'})
    except Exception as e:
        print('Error:', e, file=stderr)
        return jsonify({'msg': 'error', 'error': str(e)})
    

@app.route('/reload', methods=['GET'])
def reload():
    try:
        if subway.read_info('subway_data.json'):
            print('Reloaded successfully')
        else:
            print('Error: file not found', file=stderr)
        return jsonify({'msg': 'ok'})
    except Exception as e:
        print('Error:', e, file=stderr)
        return jsonify({'msg': 'error', 'error': str(e)})


if __name__ == '__main__':
    app.run(port=PORT)
