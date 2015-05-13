import argparse

import requests

parser = argparse.ArgumentParser(description='Process device url')
parser.add_argument('--host', type=str, dest='host', help='device host')
parser.add_argument('--load', default=100 , type=int, dest='load', help='number of processus to be spawned')

if __name__ == '__main__':

    args = parser.parse_args()
    if not args.host:
        raise Exception('You should provide a device host')

    for i in range(0, args.load):
        url = "%s/trigger" % args.host
        print url
        r = requests.get(url)
        print "Got status code: %s" % r.status_code
        print "Got message: %s" % r.text
