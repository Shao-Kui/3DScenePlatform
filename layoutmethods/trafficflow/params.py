# params

# experiment
TRIALS = 5
PROCESS_NUM = 20
PROCESS_ITER_ROUND = 500
SET_NUMBER = 200
AVG_ITER_ROUND = 20000

RE_ITER_ROUND_LIMIT = 40
RE_ITER_COST_LIMIT = 0.5

PLOT_INTERVAL = 2000
LOG_INTERVAL = 1000
LOGGING = False

DELTA = 0.001
UCT_ARG = 100
COST_ACCEPT_PARAM = 0.2

# 'resize' action
MOVE_DISTANCE_DELTA = 1
LINE_RESIZE_DELTA = 1
WEB_RESIZE_DELTA = 1
GRID_RESIZE_DELTA = 1
ROUND_RESIZE_DELTA = 1
STAR_RESIZE_DELTA = 1
EMPTY_RESIZE_DELTA = 1

# connection
CONNECT_DISTANCE = 6
FAR_CONNECT_DISTANCE = 20
ANGLE_BIAS = 90
MERGE_THRESHOLD = 0.4

# basic
ROAD_WIDTH = 1.8
SHELF_MIN_WIDTH = 0.3
SHELF_MAX_WIDTH = 0.4
SHELF_MIN_LENGTH = 0.8
SHELF_MAX_LENGTH = 1.0
SPACE_BUFFER = ROAD_WIDTH / 2 + SHELF_MAX_WIDTH
PATTERN_LIMIT = 12

# visualization
ROAD_COLOR = (0.7, 0.7, 0.7)
BUFFER_COLOR = (0.9, 0.9, 0.9)
LINE_SHELF_COLOR = (1, 0, 0)
ROUND_SHELF_COLOR = (0.9, 0.9, 0)
GRID_SHELF_COLOR = (0.3, 0.3, 1)
WEB_SHELF_COLOR = (0, 1, 1)
STAR_SHELF_COLOR = (0, 1, 0)
EMPTY_SPACE_COLOR = (0.4, 0.4, 0.4)
ENTRANCE_COLOR = (0, 1, 0)
EXIT_COLOR = (1, 0, 0)

# defines
X_POS = 0
Y_POS = 1
X_NEG = 2
Y_NEG = 3
ROTATE = 4

LINE = 0
GRID = 1
STAR = 2
WEB = 3
ROUND = 4
EMPTY = 5

# pattern features
ROUND_IN_WIDTH = 1.5 * ROAD_WIDTH
