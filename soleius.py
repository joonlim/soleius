#!/usr/bin/env python

import csv
import datetime
import json
import os
import pprint
import requests
import statistics
import time

from multiprocessing import Process, Manager

OUTPUT = '{}/Desktop/soleius-{}.csv'.format(os.getenv('HOME'), datetime.datetime.now().replace(microsecond=0).isoformat())


start_time = time.time()

with Manager() as manager:
  opportunities = manager.list()  # Concurrent list

  def parseShoe(shoe, opportunities):
    shoe_id = shoe['traits'][0]['value']
    resp = requests.get(
      url='https://e5yn1ize54.execute-api.us-east-1.amazonaws.com/default/SoleiusMaster?productId=' + shoe_id)

    resp_json = resp.json()
    if 'sites' not in resp_json:
      return

    shoe_name = shoe['name']
    print(shoe_name)
    shoe = {
      'sizes': {},
      'means': {},
      'medians': {}
    }

    # Iterate through sites
    for site_name, site in resp.json()['sites'].iteritems():
      site_prices  = []  # Prices for this all sizes of this shoe from this site
      for size_num, size in site['sizes'].iteritems():
        if 'lowestAsk' in size and size['lowestAsk'] != 0:
          if size_num not in shoe['sizes']:
            shoe['sizes'][size_num] = {}
          price = size['lowestAsk']
          site_prices.append(price)
          shoe['sizes'][size_num][site_name] = price

      if len(site_prices) > 0:
        shoe['means'][site_name] = "%.2f" % round(statistics.mean(site_prices), 2)
        shoe['medians'][site_name] = "%.2f" % round(statistics.median(site_prices), 2)
      else:
        shoe['means'][site_name] = None
        shoe['medians'][site_name] = None

    for size_num, size in shoe['sizes'].iteritems():
      min_price = 999999999999
      min_site_name = ''
      max_price = -999999999999
      max_site_name = ''
      for site_name, site_price in size.iteritems():
        if site_price == 0:
          continue
        if site_price < min_price:
          min_price = site_price
          min_site_name = site_name
        if site_price > max_price:
          max_price = site_price
          max_site_name = site_name
      delta = max_price - min_price
      opportunities.append({
        'name': shoe_name,
        'url': 'https://soleius.com/product/' + shoe_id,
        'size': size_num,
        'delta': delta,
        'min_price': min_price,
        'min_site_name': min_site_name,
        'max_price': max_price,
        'max_site_name': max_site_name,
        'means': shoe['means'],
        'medians': shoe['medians']
      })


  resp = requests.post(
    url='https://xw7sbct9v6-dsn.algolia.net/1/indexes/*/queries?x-algolia-application-id=XW7SBCT9V6&x-algolia-api-key=6bfb5abee4dcd8cea8f0ca1ca085c2b3',
    json={'requests':[{'indexName':'products','params':'hitsPerPage=1000000&facetFilters=["product_category:sneakers"]'}]},
    headers={'content-type':'application/json','Accept-Charset':'UTF-8'})

  procs = []
  # instantiating process with arguments
  for _, shoe in enumerate(resp.json()['results'][0]['hits']):
    proc = Process(target=parseShoe, args=(shoe, opportunities))
    procs.append(proc)
    proc.start()

  # complete the processes
  for proc in procs:
    proc.join()

  print('\n' + str(len(opportunities)) + ' items')
  print("Took " + str(round(time.time() - start_time, 1)) + ' seconds')

  os = sorted(opportunities, key=lambda o: o['delta'])
  os.reverse()

  with open(OUTPUT, mode='w+') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Name','Size', 'URL', 'Cop site', 'Cop', 'Cop mean', 'Cop median', 'Sell site', 'Sell', 'Sell mean', 'Sell median', 'Delta'])
    for o in os:
      writer.writerow([o['name'], o['size'], o['url'], o['min_site_name'], o['min_price'], o['means'][o['min_site_name']],o['medians'][o['min_site_name']], o['max_site_name'],o['max_price'],o['means'][o['max_site_name']],o['medians'][o['max_site_name']], o['delta']])
