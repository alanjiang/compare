import difflib
import sys
import argparse
import os
import re
from method_mark import *



'''
  生成html报告
'''

#file: 处于打开状态的文件
def wrtie_header(file):

  file.write('<!DOCTYPE html>\t\n')
  file.write('<html>\t\n')
  file.write('<head>\t\n')
  file.write('<meta charset="UTF-8">\t\n')
  file.write('<meta name="viewport" content="width=device-width, initial-scale=1">\t\n')
  file.write('<title>文件比对报告</title>\t\n')
  file.write('<style type="text/css">\t\n')
  file.write('table.gridtable {')
  file.write('font-family: verdana,arial,sans-serif;')
  file.write('font-size:11px;')
  file.write('color:#333333;')
  file.write('border-width: 1px;')
  file.write('border-color: #666666;')
  file.write('border-collapse: collapse;')
  file.write('}')
  file.write('table.gridtable th {')
  file.write('border-width: 1px;')
  file.write('padding: 8px;')
  file.write('border-style: solid;')
  file.write('border-color: #666666;')
  file.write('background-color: #dedede;')
  file.write('}')
  file.write('table.gridtable td {')
  file.write('border-width: 1px;')
  file.write('padding: 8px;')
  file.write('border-style: solid;')
  file.write('border-color: #666666;')
  file.write('background-color: #ffffff;')
  file.write('}')
  file.write('</style>')
  file.write('</head>')
  file.write('<body>')

#ths:列名集合,tds:列内容字典,key:类名,value:变动行位置|相似度|函数是否变动
def write_table_th(file,title, ths):

    file.write('<h3 style="color:red;">'+title+'</h3>\t\n')

    file.write('<table class="gridtable">\t\n')

    file.write('<tr>')
    
    for th in ths:

        file.write('<th>'+th+'</th>')
      
    file.write('</tr>')    
    
   
    
def write_table_td_row(file,collection):

    file.write('<tr>')
    for cell in collection:
        file.write('<td>'+cell+'</td>')
    file.write('</tr>')   

# dic字典或者集合
def write_table_td(file,dic):

  
    if type(dic) == dict:
      
        
        for k,v in dic.items():
           file.write('<tr>')
           file.write('<td>'+k+'</td><td>'+v+'</td>')
           file.write('</tr>')
        
    elif type(dic) == list:
        
        for ele in dic:
            file.write('<tr>')
            file.write('<td>'+ele+'</td>')
            file.write('</tr>') 
    else:

       print('--Not support type --')
def write_table_tail(file):

    file.write('</table>\t\n')


def  write_table_td_ele(file,total_class_number,global_diff_class_num,total_method_number,global_diff_method_num,total_master_class_number):

       file.write('<tr>')
       file.write('<td>'+str(total_class_number)+'</td><td>'+str(global_diff_class_num)+'</td><td>'+str(total_method_number)+'</td><td>'+str(global_diff_method_num)+'</td><td>'+str(total_master_class_number)+'</td>')        
       file.write('</tr>')

#网页尾巴部分
def write_tail(file):

    file.write('</body>\t\n')
    file.write('</html>\t\n')
