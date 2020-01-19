# -*- coding: utf-8 -*
import difflib
import sys
import argparse
import os
import re
from function_extract import *
#统计类的内容获取
#插入新的统计结果
def rewriteReport(fileName):
    #lines = read_file(fileName) #文件所有的行
    #code_dic=getCodeDic(lines) #文件所有的行字典，key:行号,value:行内容

    file= open(fileName, 'r')
    #text = file.read().splitlines()
    text = file.read()
    file.close()
    
    pattern='<tr><th>类名</th><th>行改动位置</th></tr>(?P<body>.*)</table>'

    res=re.search(pattern,text,re.M)

    collection = [] 
    if res:
           body=res.group('body')
     
           print(len(body))

           list = re.findall(r'<tr><td>([0-9A-Za-z.\-\/]+?)</td><td>([0-9,]+?)</td></tr>',body,re.S)

           for item in list:

               tpl = (item[0],item[1],len(item[1]))
               #print(tpl)
               collection.append(tpl)
          
    if len(collection) > 0:

        #lambda函数排序
        collection  = sorted(collection,key=lambda x: (x[2]))      

    insertTable = '<p style="color:red">java文件比较行改动行数统计</p><table class="gridtable"><tr><th>java文件</th><th>更新行数</th></tr>'

    level1 = 0

    level2 = 0

    level3 = 0

    total = len(collection)

    if total == 0:

        return 'EXIT'
    
    for tp in collection:


        if len(tp[1]) <= 10:
            
            insertTable+='<tr><td>'+tp[0]+'</td><td style="background:green;">'+str(len(tp[1]))+'</td></tr>'
            level1+=1
        elif len(tp[1]) > 10 and len(tp[1]) < 30:
            insertTable+='<tr><td>'+tp[0]+'</td><td style="background:yellow;">'+str(len(tp[1]))+'</td></tr>'
            level2+=1
        else:    
            insertTable+='<tr><td>'+tp[0]+'</td><td style="background:red;">'+str(len(tp[1]))+'</td></tr>'
            level3+=1


    ratio1 = '{:.2%}'.format(level1/total )

    ratio2 = '{:.2%}'.format(level2/total )

    ratio3 = '{:.2%}'.format(level3/total )
    
          
    insertTable+='</table>'

    insertTable+= '<p style="color:red">java文件比较改动级别统计</p><table class="gridtable"><tr><th>改动级别</th><th>文件个数</th><th>占比</th></tr>'
    insertTable+='<tr><td>改动10行以下</td><td style="background:green;">'+str(level1)+'</td><td style="background:green;">'+ratio1+'</td></tr>'
    insertTable+='<tr><td>改动30行以下</td><td style="background:yellow;">'+str(level2)+'</td><td style="background:yellow;">'+ratio2+'</td></tr>'

    insertTable+='<tr><td>改动30行以上</td><td style="background:red;">'+str(level3)+'</td><td style="background:red;">'+ratio3+'</td></tr>'

    insertTable+='</table>'
    
    #print('=>insertTable:{}'.format(insertTable))
    pos = text.find('</body>')

    
    
    insertText(fileName,pos,insertTable,text)


    



#插入文本text
def insertText(fileName,pos,text,fileContent):


   with open(fileName,"wt") as file:
       
        content=fileContent[:pos]+text+fileContent[pos:]
        
        file.writelines(content)
    
        
if __name__ == "__main__":

    fileName = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/report/report.html'

    rewriteReport(fileName)
    
