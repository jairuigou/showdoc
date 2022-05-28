import requests
import os
import zipfile
import json
import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description='auto export showdoc document to markdown file with hierarchy')
parser.add_argument('url',help='showdoc server domain')
parser.add_argument('-f',dest='cookies_file',default='showdoc_cookies.json',
                    help='cookies file in json format, default is \'showdoc_cookies.json\'')
args = parser.parse_args()
url = args.url + 'server/index.php'
cookies = json.load(open(args.cookies_file))
backup_dir = 'showdoc_backup_' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
print("create backup directory: {}.".format(backup_dir))

try:
  os.mkdir(backup_dir)
except FileExistsError:
  print(backup_dir,"already exists.")
  exit(0)
os.chdir(backup_dir)
backup_dir_cwd = os.getcwd()

r = requests.post(url,params={'s':'/api/item/myList'},data={'item_group_id': '0'},cookies=cookies)
for item in r.json()['data']:
  id = item['item_id']
  subdir_name = item['item_name']
  # no whitespace
  subdir_name = subdir_name.replace(" ","-")
  os.mkdir(subdir_name)
  os.chdir(subdir_name)
  print('get item {} {}'.format(id,subdir_name))
  rr = requests.get(url,params={'s':'/api/export/markdown','item_id':item['item_id']},cookies=cookies,stream=True)
  with open('tmp.zip','wb') as fd:
    for chunk in rr.iter_content(chunk_size=128):
      fd.write(chunk)
  with zipfile.ZipFile('tmp.zip','r') as zip_file:
    zip_file.extractall('./')
  
  # rename file
  with open('prefix_readme.md','r') as fd:
    fd.readline()
    fd.readline()
    for line in fd.readlines():
      title = line.split(chr(8212))[0].strip()
      md5_filename = line.split(chr(8212))[-1].strip()
      title = title.replace(' ','-')
      os.rename(md5_filename,title+'.md')

  # create directory hierarchy
  info = json.load(open('prefix_info.json'))
  toplevel_dir = os.getcwd()
  def search_catalogs(info,path):
    if 'pages' not in info:
      return
    # move file belonging to this catalog
    for page in info['pages']:
      title = page['page_title'].replace(' ','-')
      src_filepath = os.path.join(toplevel_dir,title+'.md')
      dis_filepath = os.path.join(path,title+'.md')
      os.rename(src_filepath,dis_filepath)

    if 'catalogs' not in info:
      return
    for catalog in info['catalogs']:
      cat_name = catalog['cat_name'].replace(' ','-')
      subpath = os.path.join(path,cat_name)
      os.mkdir(subpath)
      search_catalogs(catalog,subpath)

  search_catalogs(info['pages'],toplevel_dir)
  os.remove('prefix_info.json')
  os.remove('prefix_readme.md')
  os.remove('tmp.zip')
  os.chdir(backup_dir_cwd)