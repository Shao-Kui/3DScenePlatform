from math import pi
HEIGHT_RATIO = 1.3
CANVAS_WIDTH = 1000

w, h = 10, 10
out = {}
camera = {}
camera['fov'] = 75
camera['focalLength'] = 35
camera['rotate'] = [-pi / 2, 0, 0]
camera['up'] = [0, 0, -1]
camera['roomId'] = 0
camera['target'] = [w / 2, 0, h / 2]
camHeight = min(w, h) * HEIGHT_RATIO
camera['origin'] = [w / 2, camHeight, h / 2]
out['PerspectiveCamera'] = camera
canvas = {'width': CANVAS_WIDTH, 'height': (int)(CANVAS_WIDTH / w * h)}
out['canvas'] = canvas