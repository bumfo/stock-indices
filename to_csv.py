import csv
import json


def main():
    with open('data/a_indices.csv', 'w') as fo:
        w = csv.writer(fo)
        with open('data/a_indices.json', 'r') as f:
            data = json.load(f)['data']

            for d in data:
                row = [
                    d['stockCode'],
                    d['source'],
                    d['areaCode'],
                    d['market'],
                    d['name'],
                    d['launchDate'],
                ]

                w.writerow(row)


if __name__ == '__main__':
    main()
