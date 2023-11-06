import random
import os

name = ''
base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
length = len(base_str) - 1
for i in range(10):
    name += base_str[random.randint(0, length)]

print(name)
os.system('python gen.py ' + name + '.json')
os.system('python main.py ' + name + '.json')