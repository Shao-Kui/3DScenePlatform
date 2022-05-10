import os
import sys


def movebest():
    bestDir = 'best_results'
    ifLinux = 'linux' in sys.platform
    for root, dirs, files in os.walk('tmp_results', topdown=False):
        for name in files:
            if 'best' in name or 'cost' in name:
                n1 = os.path.join(root, name)
                n2 = os.path.join(bestDir, name)
                if ifLinux:
                    os.system('cp ' + n1 + ' ' + n2)
                else:
                    os.system('copy ' + n1 + ' ' + n2)


if __name__ == '__main__':
    movebest()
