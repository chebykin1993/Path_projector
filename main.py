from matplotlib import pyplot as plt
import numpy as np
import math
import json
import requests
from geographiclib.geodesic import Geodesic

class Origin:
    def __init__(self, latitude, longtitude, maxrange=300):
        self.latitude = latitude
        self.longtitude = longtitude
        self.maxrange = maxrange
        self.boundaries = [
            self.latitude - self.maxrange / 111,
            self.longtitude - self.maxrange / (111.320 * math.cos(math.radians(self.latitude))),
            self.latitude + self.maxrange / 111,
            self.longtitude + self.maxrange / (111.320 * math.cos(math.radians(self.latitude)))
        ]
    def params_calc(self):
        request = requests.get("https://opensky-network.org/api/states/all", headers={'Artem': 'Cheba1111'}, params={
            'lamin': self.boundaries[0],
            'lomin': self.boundaries[1],
            'lamax': self.boundaries[2],
            'lomax': self.boundaries[3]})
        info = request.text
        planes = json.loads(info)
        if planes['states'] is not None:
            air_traffic = {}
            for i in planes['states']:
                plane_latitude, plane_longtitude = i[6], i[5]
                g = Geodesic.WGS84.Inverse(float(self.latitude),
                                           float(self.longtitude),
                                           plane_latitude,
                                           plane_longtitude,
                                           )
                if g['s12'] / 1000 > self.maxrange:
                    continue
                if g['azi1'] < 0:
                    g['azi1'] = g['azi1'] + 360
                kur = g['azi1'] - i[10] # Kur - курсовой угол РНТ
                if kur < 0:
                    kur = kur + 360
                plane_coords = g['s12'] / 1000, i[10], kur, plane_latitude, plane_longtitude, g['azi1']
                air_traffic.setdefault(i[1].rstrip(), plane_coords)
            return air_traffic

    def angle_measure(self):
        pass

    def geom(self, traffic, callsign):
        kur = traffic[callsign][2]
        dist_escape = 0
        rectang_side = 0
        opposite_angle = 0
        supp_angle = 0
        main_angle = 0
        true_distance = 0
        if kur < 90:
            rectang_side = traffic[callsign][0] * math.sin(math.radians(kur))
            opposite_angle = math.degrees(math.asin(rectang_side / self.maxrange))
            dist_escape = traffic[callsign][0] * math.cos(math.radians(kur)) + self.maxrange * math.cos(math.radians(opposite_angle))
            true_distance = 2 * self.maxrange * math.cos(math.radians(opposite_angle)) - dist_escape
            return true_distance
        if 90 < kur < 180:
            supp_angle = 180 - kur
            rectang_side = traffic[callsign][0] * math.sin(math.radians(supp_angle))
            opposite_angle = math.degrees(math.asin(rectang_side / self.maxrange))
            dist_escape = self.maxrange * math.cos(math.radians(opposite_angle)) - traffic[callsign][0] * math.cos(math.radians(supp_angle))
            true_distance = 2 * self.maxrange * math.cos(math.radians(opposite_angle)) - dist_escape
            return true_distance
        if kur > 180:
            supp_angle = 360 - kur
            opposite_angle = math.degrees(math.asin(math.sin(math.radians(supp_angle)) * traffic[callsign][0] / self.maxrange))
            main_angle = (180 - supp_angle) - opposite_angle
            dist_escape = math.sin(math.radians(main_angle)) * self.maxrange / math.sin(math.radians(supp_angle))
            true_distance = 2 * self.maxrange * math.cos(math.radians(opposite_angle)) - dist_escape
            return true_distance

    def direct_path(self, traffic, callsign):
        heading = traffic[callsign][1]
        distance_to_exit = self.geom(traffic, callsign)
        coords_exit = Geodesic.WGS84.Direct(traffic[callsign][3],
                                            traffic[callsign][4],
                                            heading,
                                            distance_to_exit * 1000)
        return coords_exit['lat2'], coords_exit['lon2'], heading

    def path_calculation(self, traffic, callsign, dist_diff=10):
        heading = traffic[callsign][1]
        kur = traffic[callsign][2]
        distance_to_exit = self.geom(traffic, callsign)
        coords_exit = Geodesic.WGS84.Direct(traffic[callsign][3],
                                            traffic[callsign][4],
                                            heading,
                                            distance_to_exit * 1000)
        if kur > 90:
            return coords_exit['lat2'], coords_exit['lon2']
        distance_corr = (distance_to_exit // 10) * 10
        obj = str(int(distance_corr))
        angle_path = 0
        distance_to_origin = 0
        angle_diff = 0
        with open('base.json') as data:
            base = json.load(data)
        for angle in base[obj]:
            if base[obj][angle] >= distance_to_exit + dist_diff:
                angle_path = int(angle) + kur
                distance_to_origin = base[obj][angle] - self.maxrange
                angle_diff = int(angle)
                break
        turn_position = Geodesic.WGS84.Direct(float(self.latitude),
                                            float(self.longtitude),
                                            traffic[callsign][5] + angle_diff,
                                            distance_to_origin * 1000)
        return angle_path, coords_exit['lat2'], coords_exit['lon2'], turn_position['lat2'], turn_position['lon2']

    def make_plot(self):
        p = plt.figure(figsize=(20, 20))
        angles = np.arange(0, 95, 5)
        intervals = np.arange(0, 310, 10)
        fig = plt.subplot(projection='polar')
        fig.set_theta_zero_location("N")
        fig.set_thetamin(0)
        fig.set_thetamax(90)
        fig.set_theta_direction(-1)
        fig.tick_params(axis='y', which='major', labelsize=5)
        plt.yticks(intervals)
        plt.grid(axis='y')
        fig.set_thetagrids(angles)
        for i in intervals:
            fi = 0
            dist = 0
            for f in angles:
                relation = i * (2 / (1 + math.cos(math.radians(f))))
                fig.plot([0, math.radians(f)], [0, relation], '.', color='black', markersize='2')
                fig.plot([math.radians(fi), math.radians(f)], [dist, relation], color='black', linewidth=1)
                fig.annotate(int(relation), (math.radians(f), int(relation)), fontsize=5)
                fi = f
                dist = relation
        plt.savefig('plot.jpg')
        plt.show()

    def make_json(self):
        angles = np.arange(5, 95, 5)
        intervals = np.arange(10, 610, 10)
        base = {}
        for i in intervals:
            temp = {}
            for f in angles:
                relation = i * (2 / (1 + math.cos(math.radians(f))))
                temp.setdefault(str(f), int(relation))
            base.setdefault(str(i), temp)
        with open('../../../../../PycharmProjects/pythonProject/base.json', 'w') as b:
            json.dump(base, b, indent=4)
