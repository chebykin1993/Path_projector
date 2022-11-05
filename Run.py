import main
import time
import requests

point = None
check = requests.get('')
traffic = {}

while True:
    if check == point:
        check = requests.get('')
        time.sleep(3)
    else:
        latitude, longtitude, maxrange = check
        point = main.Origin(latitude, longtitude, maxrange)
        break
traffic = point.params_calc()

while point is not None:
    time.sleep(10)
    traffic = point.params_calc()
    request = requests.get('')
    if request is not None:
        callsign, dist_diff = request
        point.path_calculation(traffic, callsign, dist_diff)


