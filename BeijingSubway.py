import json
import heapq
from typing import Callable
from sys import stderr
from pypinyin import pinyin, Style

TRANSFER_TIME = 5 * 60
STATION_TIE = 1 * 60
MAX_TRANSFER_COUNT = 100
MAX_TIME = float('inf')

class StationInfo:
    def __init__(self, name: str, line: str, start: bool = True):
        self.name = name
        self.line = line
        self.start = start

    def __hash__(self) -> int:
        return hash((self.name, self.line, self.start))

    def __eq__(self, other: 'StationInfo') -> bool:
        return self.name == other.name and self.line == other.line and self.start == other.start

    def __str__(self) -> str:
        return '{} ({}, {})'.format(self.name, self.line, 'start' if self.start else 'end')
    
    def __lt__(self, other: 'StationInfo') -> bool:
        return self.name < other.name
    

class LineInfo:
    def __init__(self, name: str, stations: list[str], speed: float, loop: bool):
        self.name = name
        self.stations = stations
        self.speed = speed
        self.loop = loop

    def __str__(self) -> str:
        return self.stations.__str__()


class EdgeInfo:
    def __init__(self, time: float, transfer_count: int):
        self.time = time
        self.transfer_count = transfer_count

    def __str__(self) -> str:
        return 'Time: {:.3f} min, Transfer count: {}'.format(self.time / 60, self.transfer_count)

    def __add__(self, other) -> 'EdgeInfo':
        return EdgeInfo(self.time + other.time, self.transfer_count + other.transfer_count)


class Edge:
    def __init__(self, station_to: StationInfo, time: float, is_transfer: bool = False):
        self.station_to = station_to
        self.edge_info = EdgeInfo(time, 1 if is_transfer else 0)


class BeijingSubway:
    def __init__(self):
        self.__graph: dict[StationInfo, list[Edge]] = {}
        self.__station_start_info: dict[str, set[StationInfo]] = {}
        self.__station_end_info: dict[str, set[StationInfo]] = {}
        self.__line_info: dict[str, LineInfo] = {}

    def __add_edge(self, station1: str, station2: str, line: str, time: float) -> None:
        for station in [station1, station2]:
            if station not in self.__station_start_info:
                self.__station_start_info[station] = set()
                self.__station_end_info[station] = set()
                print('add a new station {}.'.format(station))
            this_station_start_info = StationInfo(station, line, True)
            this_station_end_info = StationInfo(station, line, False)
            if this_station_start_info not in self.__station_start_info[station]:
                self.__graph[this_station_start_info] = []
                self.__graph[this_station_end_info] = []
                for other_station_end_info in self.__station_end_info[station]:
                    self.__graph[this_station_start_info].append(Edge(other_station_end_info, TRANSFER_TIME, True))
                for other_station_start_info in self.__station_start_info[station]:
                    self.__graph[other_station_start_info].append(Edge(this_station_end_info, TRANSFER_TIME, True))
                self.__station_start_info[station].add(this_station_start_info)
                self.__station_end_info[station].add(this_station_end_info)
            self.__graph[this_station_start_info].append(Edge(this_station_end_info, STATION_TIE))

        station_start_info1 = StationInfo(station1, line, True)
        station_start_info2 = StationInfo(station2, line, True)
        station_end_info1 = StationInfo(station1, line, False)
        station_end_info2 = StationInfo(station2, line, False)

        self.__graph[station_end_info1].append(Edge(station_start_info2, time))
        self.__graph[station_end_info2].append(Edge(station_start_info1, time))
    
    def add_line(self, line: str, stations: list[str], distances: list[int], speed: float, loop: bool) -> None:
        if line in self.__line_info:
            raise Exception('不允许添加重复的线路"{}"！'.format(line))

        if len(stations) < 2:
            raise Exception('站点数量过少！')

        if len(stations) != len(distances):
            raise Exception('站点数量 {} 和距离数量 {} 不匹配!'.format(len(stations), len(distances)))

        if not loop and distances[0] != 0:
            raise Exception('非环线首站距离必须为 0！')
        
        if len(stations) != len(set(stations)):
            raise Exception('不允许经过重复的站点！')

        if any(dis <= 0 for dis in distances[0 if loop else 1:]):
            raise Exception('站点之间距离必须大于 0!')

        if speed <= 0:
            raise Exception('速度必须大于0！')
        
        avg_speed = speed * 1000 / 3600 / 2

        for i in range(0 if loop else 1, len(stations)):
            station1, station2 = stations[i], stations[(i - 1 + len(stations)) % len(stations)]
            dis = distances[i]
            self.__add_edge(station1, station2, line, dis / avg_speed)

        print('{} line information added successfully.'.format(line))
        self.__line_info[line] = LineInfo(line, stations, speed, loop)

    def remove_line(self, line: str) -> None:
        if line not in self.__line_info:
            raise Exception('the {} line does not exist!'.format(line))

        stations = self.__line_info[line].stations
        for i in range(len(stations)):
            station = stations[i]
            for station_info in [self.__station_start_info[station], self.__station_end_info[station]]:
                for connected_station in station_info:
                    for i in range(len(self.__graph[connected_station])):
                        if self.__graph[connected_station][i].station_to.line == line:
                            print('delete edge between {} and {}.'.format(connected_station, self.__graph[connected_station][i].station_to))
                            del self.__graph[connected_station][i]
                            break
            del self.__graph[StationInfo(station, line, True)]
            del self.__graph[StationInfo(station, line, False)]
            
            self.__station_start_info[station].remove(StationInfo(station, line, True))
            if len(self.__station_start_info[station]) == 0:
                del self.__station_start_info[station]
            self.__station_end_info[station].remove(StationInfo(station, line, False))
            if len(self.__station_end_info[station]) == 0:
                del self.__station_end_info[station]

        del self.__line_info[line]
        print('{} line information removed successfully.'.format(line))

    def read_info(self, info_file_path) -> bool:
        self.clear()
        try:
            with open(info_file_path) as f:
                data: list[dict] = json.load(f)
                for line in data:
                    self.add_line(line['name'], line['stations'], line['distances'], line['speed'], line['loop'])
        except Exception as e:
            print('Error:', e, file=stderr)
            self.clear()
            return False
        finally:
            return True

    def clear(self) -> None:
        self.__graph = dict()
        self.__station_start_info = dict()
        self.__station_end_info = dict()
        self.__line_info = dict()
    
    def __shortest_path_helper(self, station_from: StationInfo, station_to: StationInfo, make_key: Callable[[EdgeInfo], tuple[float, int]]) -> tuple[list[StationInfo], list[EdgeInfo]]:
        dis = {station: EdgeInfo(MAX_TIME, MAX_TRANSFER_COUNT) for station in self.__graph}
        visited = {station: False for station in self.__graph}
        pre = {station: None for station in self.__graph}
        dis[station_from] = EdgeInfo(0, 0)

        q = [(make_key(dis[station_from]), station_from)]
        heapq.heapify(q)

        while q:
            _, u = heapq.heappop(q)
            if visited[u]:
                continue
            visited[u] = True

            for edge in self.__graph[u]:
                v = edge.station_to
                if visited[v]:
                    continue
                new_dis = dis[u] + edge.edge_info
                if make_key(dis[v]) > make_key(new_dis):
                    dis[v] = new_dis
                    pre[v] = u
                    heapq.heappush(q, (make_key(dis[v]), v))
        
        path = []
        u = station_to
        while u:
            path.append(u)
            u = pre[u]
        path.reverse()
        path_dis = [dis[u] for u in path]
        return path, path_dis

    def shortest_time_path(self, station_name_from: str, station_name_to: str) -> tuple[list[StationInfo], list[EdgeInfo]]:
        def make_key(edge_info) -> tuple[float, int]:
            return (edge_info.time, edge_info.transfer_count)
        path = []
        path_info = []
        time = float('inf')
        for station_from in self.__station_start_info[station_name_from]:
            for station_to in self.__station_end_info[station_name_to]:
                new_path, new_info = self.__shortest_path_helper(station_from, station_to, make_key)
                if len(new_path) == 0:
                    continue
                if new_info[-1].time < time:
                    path = new_path
                    path_info = new_info
                    time = new_info[-1].time
        return path, path_info

    def minimum_transfer_path(self, station_name_from: str, station_name_to: str) -> tuple[list[StationInfo], list[EdgeInfo]]:
        def make_key(edge_info) -> tuple[int, float]:
            return (edge_info.transfer_count, edge_info.time)
        path = []
        path_info = []
        transfer_count = MAX_TRANSFER_COUNT
        for station_from in self.__station_start_info[station_name_from]:
            for station_to in self.__station_end_info[station_name_to]:
                new_path, new_info = self.__shortest_path_helper(station_from, station_to, make_key)
                if len(new_path) == 0:
                    continue
                if new_info[-1].transfer_count < transfer_count:
                    path = new_path
                    path_info = new_info
                    transfer_count = new_info[-1].transfer_count
        return path, path_info
    
    def get_all_stations(self) -> list[str]:
        return sorted(list(self.__station_start_info.keys()), key=lambda x: ''.join([y[0] for y in pinyin(x, style=Style.NORMAL)]))
    
    def get_all_lines(self) -> list[str]:
        return list(self.__line_info.keys())
