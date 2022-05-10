import json
from pattern import *
from params import *

sys.path.append('E:/3DScenePlatformDev')
os.chdir('../../')
import pathTracing as pt
os.chdir('layoutmethods/trafficflow/')

TARGET_NUMBER = SET_NUMBER
HEIGHT_RATIO = 0.76
CANVAS_WIDTH = 1000


class Model:
    def __init__(self, name: str, length: float, width: float, height: float, xcenter: float, zcenter: float,
                 ybase: float):
        self.name = name
        self.length = length
        self.width = width
        self.height = height
        self.xcenter = xcenter
        self.zcenter = zcenter
        self.ybase = ybase
        self.id = None


snack01 = Model('snack01', 1.3316129, 0.7173202999999999, 1.829805, 0.0008064499999999586, 0.0006601499999999982, 0.0)
snack02 = Model('snack02', 1.3404921, 0.7173201, 1.829805, 0.005246050000000002, 0.0006600499999999954, 0.0)
snack03 = Model('snack03', 1.3981936, 0.7173202999999999, 1.897382, 0.0, -1.5000000000431335e-07, 0.0)
snack04 = Model('snack04', 1.3316129, 0.7173213, 1.829805, 0.0008064499999999586, 0.0006599499999999925, 0.0)
snacks01 = Model('snacks01', 1.2000004, 0.600404, 2.0, 0.07, 0.0807982, -6.123234e-17)
snacks02 = Model('snacks02', 1.2000004, 0.6000004, 2.0, 0.07, 0.081, -6.123234e-17)
snacks03 = Model('snacks03', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
snacks04 = Model('snacks04', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
snacks05 = Model('snacks05', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
snacks06 = Model('snacks06', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
cake02 = Model('cake02', 1.1738208, 0.6270083, 1.811193, -0.08308960000000004, 0.007904149999999999, -0.01)
cake03 = Model('cake03', 1.3981936, 0.7173201, 1.897382, 0.0, -3.499999999823089e-07, 0.0)
sandwich01 = Model('sandwich01', 1.3981936, 0.7173201, 1.897382, 0.0, -2.500000000071889e-07, 0.0)
sandwich02 = Model('sandwich02', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
burger01 = Model('burger01', 1.2000007, 0.63828341, 2.00000003824747, -2.4999999997943334e-07, 0.33614169499999996,
                 -3.824747e-08)
cake04 = Model('cake04', 1.2000001, 0.60000001, 2.00000003824747, 5.000000002919336e-08, 0.316999995, -3.824747e-08)
cake05 = Model('cake05', 1.2000007, 0.63828341, 2.00000003824747, -2.4999999997943334e-07, 0.33614169499999996,
               -3.824747e-08)
friescounter01 = Model('friescounter01', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                       0.00029993)
cake06 = Model('cake06', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
cake07 = Model('cake07', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
tacocounter01 = Model('tacocounter01', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                      0.00029993)
fruit01 = Model('fruit01', 1.3316129, 0.7173201, 1.829805, 0.0008064499999999586, 0.0006599499999999925, 0.0)
fruit02 = Model('fruit02', 1.3981936, 0.7173213, 1.897382, 0.0, -3.500000000100645e-07, 0.0)
fruit03 = Model('fruit03', 1.1512904000000002, 0.837247, 2.037087, 0.014835199999999993, 0.0234935, 0.0)
fruit04 = Model('fruit04', 1.1512904000000002, 0.8395967, 2.037087, 0.014835199999999993, 0.024668350000000006, 0.0)
fruit05 = Model('fruit05', 1.1512904000000002, 0.837247, 2.037087, 0.014835199999999993, 0.0234935, 0.0)
fruit06 = Model('fruit06', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998, 0.00029993)
fruit07 = Model('fruit07', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
fruit08 = Model('fruit08', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
fruit09 = Model('fruit09', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
fruit10 = Model('fruit10', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
fruit11 = Model('fruit11', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
vegetable01 = Model('vegetable01', 1.3981937, 0.7173201, 1.897382, -0.006903149999999969, 0.003660049999999998, 0.0)
vegetable02 = Model('vegetable02', 1.3981937, 0.7173204, 1.897382, -0.0009031499999999637, 0.018660099999999985, 0.0)
vegetable03 = Model('vegetable03', 1.3981937, 0.7173201, 1.897382, -0.0009031499999999637, 0.01865994999999998, 0.0)
vegetable04 = Model('vegetable04', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
vegetable05 = Model('vegetable05', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
vegetable06 = Model('vegetable06', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
vegetable07 = Model('vegetable07', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable08 = Model('vegetable08', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable09 = Model('vegetable09', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable10 = Model('vegetable10', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable11 = Model('vegetable11', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable12 = Model('vegetable12', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable13 = Model('vegetable13', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable14 = Model('vegetable14', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable15 = Model('vegetable15', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable16 = Model('vegetable16', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
vegetable17 = Model('vegetable17', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998,
                    0.00029993)
meat01 = Model('meat01', 1.2000007, 0.6382834, 2.0300000480000002, -2.4999999997943334e-07, 0.01914170000000001,
               0.009999952)
meat02 = Model('meat02', 1.2000007, 0.6382834, 2.0300000480000002, -2.4999999997943334e-07, 0.01914170000000001,
               0.009999952)
meat03 = Model('meat03', 1.2000007, 0.6382834, 2.0300000480000002, -2.4999999997943334e-07, 0.01914170000000001,
               0.009999952)
meat04 = Model('meat04', 1.2000007, 0.6382834, 2.0300000480000002, -2.4999999997943334e-07, 0.01914170000000001,
               0.009999952)
grain01 = Model('grain01', 1.51, 0.676294, 0.8628171091, 0.0, -0.0052197000000000215, -0.0007844091)
grain02 = Model('grain02', 1.51, 0.6752941, 0.8538579091, 0.0, -0.0047197500000000225, -0.0007844091)
staplefood01 = Model('staplefood01', 1.331613, 0.7173203, 1.829805, -0.002193500000000015, 0.35866015, 0.0)
staplefood02 = Model('staplefood02', 1.331613, 0.7173203, 1.937031, -0.002193500000000015, 0.35866015, 0.0)
staplefood03 = Model('staplefood03', 1.331613, 0.7173203, 1.829805, -0.002193500000000015, 0.35866015, 0.0)
oil01 = Model('oil01', 0.993132, 0.493132, 1.797499, 0.0, 0.0, 0.0025)
oil02 = Model('oil02', 0.993132, 0.493132, 1.797499, 0.0, 0.0, 0.0025)
eggscounter03 = Model('eggscounter03', 1.1512904000000002, 0.837247, 2.037087, 0.014835199999999993, 0.0234935, 0.0)
flavoring01 = Model('flavoring01', 1.3981936, 0.7173201, 1.897382, 0.0, -2.500000000071889e-07, 0.0)
container02 = Model('container02', 1.1512904000000002, 0.837247, 2.037087, 0.014835199999999993, 0.0234935, 0.0)
container03 = Model('container03', 1.1512904000000002, 0.837247, 2.037087, 0.014835199999999993, 0.0234935, 0.0)
container04 = Model('container04', 1.1512904000000002, 0.837247, 2.037087, 0.014835199999999993, 0.0234935, 0.0)
coffee02 = Model('coffee02', 1.3981936, 0.7173202, 1.897382, 0.0, -3.000000000086267e-07, 0.0)
drinks01 = Model('drinks01', 1.3316129, 0.7173202332266, 1.829805, -0.013193549999999998, 0.3586599833867, 0.0)
drinks02 = Model('drinks02', 1.3316129, 0.7173202999999999, 1.829805, 0.0008064499999999586, 0.0006601499999999982, 0.0)
drinks03 = Model('drinks03', 1.3316307, 0.7173204, 1.829805, 0.0008153499999999925, 0.0006600999999999968, 0.0)
drinks04 = Model('drinks04', 1.3316129, 0.7173201, 1.829805, 0.0008064499999999586, 0.0006599499999999925, 0.0)
drinks05 = Model('drinks05', 1.3316129, 0.7173201, 1.82980407, 0.0038064499999999613, -0.08093994999999998, 0.00029993)
wine01 = Model('wine01', 1.3981936, 0.7173204, 1.897382, 0.0, -2.0000000000575113e-07, 0.0)
milk01 = Model('milk01', 1.3981936, 0.7173202999999999, 1.897382, 0.0, -1.5000000000431335e-07, 0.0)
drinks06 = Model('drinks06', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks07 = Model('drinks07', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks08 = Model('drinks08', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks09 = Model('drinks09', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks10 = Model('drinks10', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks11 = Model('drinks11', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks12 = Model('drinks12', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
drinks13 = Model('drinks13', 1.331613, 0.7173200631032599, 1.829805, -0.002193500000000015, 0.35865996844837, 0.0)
vendor01 = Model('vendor01', 1.381504, 0.582592, 2.022163, 0.0, 0.0, 0.0)
vendor02 = Model('vendor02', 1.381504, 0.582592, 2.022163, 1.0000000000287557e-07, 0.0, 0.0)
housekeeping01 = Model('housekeeping01', 1.3316129, 0.7173202332266, 1.829805, -0.013193549999999998, 0.3586599833867,
                       0.0)
housekeeping02 = Model('housekeeping02', 1.3316129, 0.7173202332266, 1.829805, -0.013193549999999998, 0.3586599833867,
                       0.0)
housekeeping03 = Model('housekeeping03', 1.3316129, 0.7173202332266, 1.829805, -0.013193549999999998, 0.3586599833867,
                       0.0)
housekeeping = Model('housekeeping', 1.2000004, 0.6000004, 2.0, 0.07, 0.081, -6.123234e-17)
petfood01 = Model('petfood01', 1.331613, 0.7173203, 2.054899, -0.002193500000000015, 0.35866015, 0.0)
freezer01 = Model('freezer01', 1.2011454, 0.5999998, 0.862507, 0.0, 0.2862956, -1.416515e-17)
freezer02 = Model('freezer02', 1.2011454, 0.5999998, 0.862507, 0.0, 0.2862956, -1.416515e-17)
freezer03 = Model('freezer03', 1.2011454, 0.5999998, 0.862507, 0.0, 0.2862956, -1.416515e-17)
shirt01 = Model('shirt01', 0.710213, 0.9840002, 1.0149998807907, 0.0, 0.0, 1.192093e-07)
shirt02 = Model('shirt02', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
shirt03 = Model('shirt03', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
shirt04 = Model('shirt04', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
shirt05 = Model('shirt05', 1.1707278, 0.7102132, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
shirt06 = Model('shirt06', 1.1707278, 0.7102132, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
shirt07 = Model('shirt07', 1.1707278, 0.7102132, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
shorts01 = Model('shorts01', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
pants01 = Model('pants01', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
pants02 = Model('pants02', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
pants03 = Model('pants03', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
pants04 = Model('pants04', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
pants05 = Model('pants05', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
skirt01 = Model('skirt01', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
skirt02 = Model('skirt02', 1.1707278, 0.5457376, 1.01499997019768, 0.0, 0.0, 2.980232e-08)
allModels = [
    snack01, snack02, snack03, snack04, snacks01, snacks02, snacks03, snacks04, snacks05, snacks06, cake02, cake03,
    sandwich01, sandwich02, burger01, cake04, cake05, friescounter01, cake06, cake07, tacocounter01, fruit01, fruit02,
    fruit03, fruit04, fruit05, fruit06, fruit07, fruit08, fruit09, fruit10, fruit11, vegetable01, vegetable02,
    vegetable03, vegetable04, vegetable05, vegetable06, vegetable07, vegetable08, vegetable09, vegetable10, vegetable11,
    vegetable12, vegetable13, vegetable14, vegetable15, vegetable16, vegetable17, meat01, meat02, meat03, meat04,
    grain01, grain02, staplefood01, staplefood02, staplefood03, oil01, oil02, eggscounter03, flavoring01, container02,
    container03, container04, coffee02, drinks01, drinks02, drinks03, drinks04, drinks05, wine01, milk01, drinks06,
    drinks07, drinks08, drinks09, drinks10, drinks11, drinks12, drinks13, vendor01, vendor02, housekeeping01,
    housekeeping02, housekeeping03, housekeeping, petfood01, freezer01, freezer02, freezer03, shirt01, shirt02, shirt03,
    shirt04, shirt05, shirt06, shirt07, shorts01, pants01, pants02, pants03, pants04, pants05, skirt01, skirt02
]
snacks = [snack01, snack02, snack03, snack04, snacks01, snacks02, snacks03, snacks04, snacks05, snacks06]
cakes = [
    cake02, cake03, sandwich01, sandwich02, burger01, cake04, cake05, friescounter01, cake06, cake07, tacocounter01
]
fruits = [fruit01, fruit02, fruit03, fruit04, fruit05, fruit06, fruit07, fruit08, fruit09, fruit10, fruit11]
vegetables = [
    vegetable01, vegetable02, vegetable03, vegetable04, vegetable05, vegetable06, vegetable07, vegetable08, vegetable09,
    vegetable10, vegetable11, vegetable12, vegetable13, vegetable14, vegetable15, vegetable16, vegetable17
]
meats = [meat01, meat02, meat03, meat04]
grains = [
    grain01, grain02, staplefood01, staplefood02, staplefood03, oil01, oil02, eggscounter03, flavoring01, petfood01
]
containers = [container02, container03, container04]
drinks = [
    coffee02, drinks01, drinks02, drinks03, drinks04, drinks05, wine01, milk01, drinks06, drinks07, drinks08, drinks09,
    drinks10, drinks11, drinks12, drinks13
]
vendors = [vendor01, vendor02, freezer01, freezer02, freezer03]
housekeepings = [housekeeping01, housekeeping02, housekeeping03, housekeeping]
shirts = [
    shirt01, shirt02, shirt03, shirt04, shirt05, shirt06, shirt07, shorts01, pants01, pants02, pants03, pants04,
    pants05, skirt01, skirt02
]

lessChoices = [vendors, meats, containers, housekeepings]
moreChoices = [snacks, cakes, fruits, vegetables, grains, drinks, shirts]

door = Model('cgaxis_models_32_24', 2.535636, 0.620525, 2.499879, 0.0, 5.000000000143778e-07, 5.5e-05)


def transform(trial: int, dummy: int):
    random.seed()
    origin = 'result'
    id = "10000"

    for i in range(len(allModels)):
        allModels[i].id = i
    if os.path.exists('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy'):
        model = np.load('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy', allow_pickle=True).tolist()
        space = TwoDimSpace(model[0][0], model[0][1], model[0][2], model[0][3], model[0][4])
        context = model[
            1]  # net[0],bestNet[1],patternList[2],bestList[3],totalcost[4],bestCost[5],totalCostList[6],nowIterRound[7],bestIterRound[8],ctionProbabilities[9],sinceLastBest[10],wallPatterns[11]
        xlow = space.boundbox.bounds[0]
        xhigh = space.boundbox.bounds[2]
        zlow = space.boundbox.bounds[1]
        zhigh = space.boundbox.bounds[3]
        xlen = xhigh - xlow
        zlen = zhigh - zlow
        scenes = []
        for i in range(TARGET_NUMBER):
            bestList = context[i][3]
            bestWallList = context[i][11]
            modelChoices = []

            # set basic contents
            out = {}
            out['origin'] = origin
            out['id'] = id
            out['islod'] = True
            out['bbox'] = {"min": [xlow, 0, zlow], "max": [xhigh, 3, zhigh]}
            out['up'] = [0, 1, 0]
            out['front'] = [0, 0, 1]

            # configure the room
            room = {}
            room['id'] = id + '_0'
            room['modelId'] = "Bathroom-6473"
            room['roomTypes'] = ["Bathroom"]
            room['bbox'] = {"min": [xlow, 0, zlow], "max": [xhigh, 3, zhigh]}
            room['origin'] = origin
            room['roomId'] = 0

            room['roomShape'] = [[(float)(point[0]), (float)(point[1])] for point in space.pointList]
            room['roomNorm'] = []
            for k in range(len(space.pointList)):
                n = norm(rot(space.pointList[(k + 1) % len(space.pointList)] - space.pointList[k], pi / 2))
                room['roomNorm'].append([(float)(n[0]), (float)(n[1])])
            room['roomOrient'] = [
                pi / 2 - atan2(room['roomNorm'][k][1], room['roomNorm'][k][0]) for k in range(len(room['roomNorm']))
            ]
            room['roomShapeBBox'] = {"max": [xhigh, zhigh], "min": [xlow, zlow]}
            shelfs = []
            objList = []
            key = 0
            for pattern in bestList:
                if pattern.type == EMPTY:
                    modelChoices.append(None)
                    continue
                groups = [[] for k in range(100)]
                for shelf in pattern.shelfs:
                    groups[shelf.group].append(shelf)
                groupCount = 0
                for group in groups:
                    if len(group) > 0:
                        groupCount += 1
                modelGroup = None
                if groupCount <= 5:
                    modelGroup = lessChoices[random.randint(0, len(lessChoices) - 1)]
                else:
                    modelGroup = moreChoices[random.randint(0, len(moreChoices) - 1)]
                modelChoices.append(modelGroup)
                modelGroupLen = len(modelGroup)
                random.shuffle(modelGroup)
                for k in range(len(groups)):
                    if len(groups[k]) > 0:
                        for shelf in groups[k]:
                            shelf.model = modelGroup[k % modelGroupLen].id
                            shelfs.append(shelf)

            for wpattern in bestWallList:
                modelGroup = modelChoices[wpattern.follow]
                modelGroupLen = len(modelGroup)
                random.shuffle(modelGroup)
                for shelf in wpattern.shelfs:
                    shelf.model = modelGroup[k % modelGroupLen].id
                    shelfs.append(shelf)

            for shelf in shelfs:
                width, length = 0.0, 0.0
                xtrans, ztrans = 0.0, 0.0
                model = allModels[shelf.model]
                obj = {}
                obj['modelId'] = model.name
                obj['roomId'] = 0
                if shelf.towards == X_POS:
                    width = shelf.xl
                    length = shelf.yl
                    obj['orient'] = pi / 2
                elif shelf.towards == Y_POS:
                    width = shelf.yl
                    length = shelf.xl
                    obj['orient'] = 0
                elif shelf.towards == X_NEG:
                    width = shelf.xl
                    length = shelf.yl
                    obj['orient'] = -pi / 2
                elif shelf.towards == Y_NEG:
                    width = shelf.yl
                    length = shelf.xl
                    obj['orient'] = pi
                else:
                    length = shelf.xl
                    width = shelf.yl
                    obj['orient'] = -shelf.rotate + pi / 2

                obj['rotate'] = [0, obj['orient'], 0]
                obj['scale'] = [length / model.length, length / model.length, width / model.width]
                xtrans = -cos(obj['orient']) * model.xcenter * obj['scale'][0] - sin(
                    obj['orient']) * model.zcenter * obj['scale'][2]
                ztrans = sin(obj['orient']) * model.xcenter * obj['scale'][0] - cos(
                    obj['orient']) * model.zcenter * obj['scale'][2]
                key += 1
                obj['key'] = (str)(key)
                obj['translate'] = [shelf.x + xtrans, 0, shelf.y + ztrans]
                objList.append(obj)

            # entrance and exit doors
            entrance = space.entranceNorm * door.width / 2 + space.entrancePoint
            ent = {}
            ent['modelId'] = door.name
            ent['roomId'] = 0
            ent['scale'] = [ROAD_WIDTH / door.length, 0.8, 1]
            ent['orient'] = -atan2(space.entranceNorm[1], space.entranceNorm[0]) + pi / 2
            ent['rotate'] = [0, ent['orient'], 0]
            ent['key'] = 'entrance'
            ent['translate'] = [entrance[0], 0, entrance[1]]
            exit = space.exitNorm * door.width / 2 + space.exitPoint
            ex = {}
            ex['modelId'] = door.name
            ex['roomId'] = 0
            ex['scale'] = [ROAD_WIDTH / door.length, 0.8, 1]
            ex['orient'] = -atan2(space.exitNorm[1], space.exitNorm[0]) + pi / 2
            ex['rotate'] = [0, ex['orient'], 0]
            ex['key'] = 'exit'
            ex['translate'] = [exit[0], 0, exit[1]]
            objList.append(ent)
            objList.append(ex)

            # entrance and exit holes
            entHole = {}
            entHole['modelId'] = 'noUse'
            entHole['roomId'] = 0
            entHole['scale'] = [1, 1, 1]
            entHole['orient'] = 0
            entHole['rotate'] = [0, 0, 0]
            entHole['key'] = 'entranceHole'
            entHole['translate'] = [0, 0, 0]
            entHole['bbox'] = {
                "min": [space.entrancePoint[0] - ROAD_WIDTH / 2, 0, space.entrancePoint[1] - ROAD_WIDTH / 2],
                "max": [space.entrancePoint[0] + ROAD_WIDTH / 2, 2, space.entrancePoint[1] + ROAD_WIDTH / 2]
            }
            entHole['coarseSemantic'] = 'Door'
            exHole = {}
            exHole['modelId'] = 'noUse'
            exHole['roomId'] = 0
            exHole['scale'] = [1, 1, 1]
            exHole['orient'] = 0
            exHole['rotate'] = [0, 0, 0]
            exHole['key'] = 'exitHole'
            exHole['translate'] = [0, 0, 0]
            exHole['bbox'] = {
                "min": [space.exitPoint[0] - ROAD_WIDTH / 2, 0, space.exitPoint[1] - ROAD_WIDTH / 2],
                "max": [space.exitPoint[0] + ROAD_WIDTH / 2, 2, space.exitPoint[1] + ROAD_WIDTH / 2]
            }
            exHole['coarseSemantic'] = 'Door'
            objList.append(entHole)
            objList.append(exHole)

            room['objList'] = objList
            room['blockList'] = []
            rooms = [room]
            out['rooms'] = rooms

            # configure the cameras
            camera = {}
            camera['fov'] = 75
            camera['focalLength'] = 35
            camera['rotate'] = [-pi / 2, 0, 0]
            camera['up'] = [0, 0, -1]
            camera['roomId'] = 0
            camera['target'] = [(xlow + xhigh) / 2, 0, (zlow + zhigh) / 2]
            camHeight = min(xlen, zlen) * HEIGHT_RATIO
            camera['origin'] = [(xlow + xhigh) / 2, camHeight, (zlow + zhigh) / 2]
            out['PerspectiveCamera'] = camera
            orthCamera = {}
            orthCamera['x'] = (max(xlen, zlen) + 0.8) / 2
            orthCamera['y'] = orthCamera['x']
            out["OrthCamera"] = orthCamera
            # configure the canvas
            canvas = {'width': CANVAS_WIDTH, 'height': (int)(CANVAS_WIDTH / xlen * zlen)}
            out['canvas'] = canvas

            # dump to file
            outf = open('scenes/' + origin + (str)(trial * TARGET_NUMBER + i) + '.json', 'w')
            json.dump(out, outf)
            outf.close()
            scenes.append(out)

        os.chdir('../../')
        for i in range(TARGET_NUMBER):
            pt.SAVECONFIG = False
            pt.USENEWWALL = True
            pt.cameraType = 'perspective'
            pt.pathTracing(scenes[i], 4,
                           'layoutmethods/trafficflow/images/images_' + (str)(trial * TARGET_NUMBER + i) + '.png')
            pt.cameraType = 'orthographic'
            pt.pathTracing(scenes[i], 4,
                           'layoutmethods/trafficflow/images/images_' + (str)(trial * TARGET_NUMBER + i) + '_orth.png')
            print('pt ' + (str)(trial * TARGET_NUMBER + i))
        os.chdir('layoutmethods/trafficflow/')
    else:
        print("no model available")


if __name__ == '__main__':
    transform(0, 0)
