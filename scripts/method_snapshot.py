# -*- coding: utf-8 -*-
import shutil
import re
import os
import  function_extract   as   func
from method_mark import *

'''
@ 作者 ： jiangpeng@126.com
@ 2019/12/20
@ 获取java类的方法起始行
@ 返回method_marker 方法标记对象集合
'''
#***********************************************************
#************** start 获取一个类的方法快照主程 ******************
LEFT_BRACE='{'
RIGHT_BRACE='}'


def find_all_methods(file):
    method_markers = [] #方法标记集合
    lines = func.read_file(file) #文件所有的行,去掉注释后的行
    code_dic=func.getCodeDic(lines) #key:行号,value:行内容,字典
    
    col = read_line_by_line(code_dic,1,[],[])

    if len(col) == 0:
        return  method_markers
    #通过set去重
    col =list(set(col))
    #通过(x,y)的x排序
    
    col = sorted(col, key=lambda item:item[0], reverse=False)
    #print('==>所有方法1,Tuple:{}'.format(col))

    #去掉不合法的tuple
    col = validate_methods(col)

    
    #print('==>所有方法2,Tuple:{}'.format(col))
    size = len(col)
    if size == 0:
        return  method_markers
    valid_col = [] 
    for index in range(0,size):
      ele = col[index]
      start = ele[0]
      end = ele[1]
      braces = []
      x,y= read_method_start(code_dic,start,braces) 
      valid_col.append((x,end,start-x+1))

    #print(valid_col)
    
    col=[] #清空
    for ele in valid_col:

      start = ele[0]
      end = ele[1]
      method_str_rows = ele[2]
      method_str = func.getCodeByRowNumbers(code_dic,start, start+method_str_rows-1)
      #print(method_str)
      method_body = func.getCodeByRowNumbers(code_dic,start, end)
      method =' '
      pattern=re.compile(r'([a-zA-Z0-9._]+\s*\([\[\]\s\d\w,<>@\"\(\)=]*\))')
     
      res = pattern.search(method_str.strip(), re.M)

      if res:

          method =  res.group(1)

          #print('method:{}'.format(method))
      if method != ' ':
         variables = []
         params = []
         method_no_param= ' ' 
         method_markers.append(MethodMarker(method,method_str,method_str_rows,start,end,method_body,variables,params,method_no_param) )
      else:
          pass
          #print('warning:file:{},start:{},end:{} not found method'.format(file,start,end))
      
    size = len(method_markers)
    
    for i in range(0,size):
        mmk = method_markers[i]
        variables = func.findVariables(mmk)
        param = func.get_method_param(mmk.method_str)
        params = func.get_method_param_variables (mmk.method_str)
        #print('method_str:{},method:{},body:{},start:{},end:{},rows:{}'.format(mmk.method_str,mmk.method,mmk.body,mmk.start,mmk.end,mmk.method_str_rows))
        if  len(params) > 0 :
               
               variable_collection = func.reset_method_param_variables(params)
               method_no_param = mmk.method_str.replace(param,str(variable_collection)).strip()
        else:
               
               method_no_param = mmk.method_str.strip()
               
        method_markers[i]= MethodMarker(mmk.method,mmk.method_str,mmk.method_str_rows,mmk.start,mmk.end,mmk.body,variables,params,method_no_param) 

    for mmk in method_markers:
        pass
        #print('params:{},variables:{},method_no_param:{}'.format(mmk.params,mmk.variables,mmk.method_no_param))
    return method_markers

# col: 存储 [({,}) ,...] 元组信息
#start:行号
def read_line_by_line(code_dic,start,braces,col):
    
    last=False
    
    if start > len(code_dic) :
       
        return  col
    else:
       line=code_dic[start].strip()
       #print(line)
       #开始处理当前行
       for char in line: #一个字符一个字符地去读取 
                
                if char == LEFT_BRACE or char == RIGHT_BRACE  : #仅当符号为{ 或者 } 时执行花刮号配对算法

                   braces=match_brace(braces,char,start,col)
                   
                   if len(braces) == 0 : # 发现花刮号的行，处理后出现集合清空的情况，说明已找到方法的最后一行

                      #print('==>找到最后一行:{}'.format(start))
                      #排除内隐类的情况，多个类
                      if start == len(code_dic): #说明最后一行

                         return col #返回配对[({,})...]集合
                      else: # 说明还有内容，
                          braces=[]
                          return read_line_by_line(code_dic,start+1,braces,col)

                        
       start+=1
       

       return read_line_by_line(code_dic,start,braces,col)
   
         
        
# 花刮号算法主程
# 当前刮号如果是},判断集合中的未尾Tuple是否是{,若是，称为“配对成功",同时从集合中移除集合中的未尾Tuple元素;
# 当前刮号如果是{,创建一个新的Tuple对象，加到集合中。
#start: 当前行号
def  match_brace(braces,char,start,col):

     size = len(braces)
     
     if size == 0: #第一个{

         braces.append((char,start,0)) #生成一个Tuple，加入集合中
         return braces
     
     tailTuple = braces[size-1]

     if char == RIGHT_BRACE: #当前元素右刮号

        if tailTuple[0] == LEFT_BRACE: # 与未尾元素配对成功

           braces.pop(size-1) #移除未尾元素Tuple

           col.append((tailTuple[1],start)) # {,} 配对后所在的行
     
        else: #未尾元素tailTuple[0] 为 } ,与char未配对

           braces.append((char,start,0))
           
     else:#当前元素左刮号

           braces.append((char,start,0))

     return braces
          




#从集合[(x,y)....]中去掉不是方法的(x,y)
#tpls: 一个文件的[(x,y)....]列表
ENDS='{;'
def validate_methods(tpls):

    if len(tpls) == 0:
       return tpls
    
    
    #去掉第方法体tuple
    first =  tpls[0]
    tpls.remove(first) #方法体起始，需要去掉
    removed = []
    #x=y的全部去掉
    index = -1;
    for tpl in tpls:
        index+=1
        if tpl[0] == tpl[1]:
            removed.append(tpl)
    for rm in removed:
       
       tpls.remove(rm)
    #去掉边界
    removed = []
    index = -1;
    for tpl in tpls:
        index+=1
        removed = del_inner_tuple(index, tpls,removed)

    removed = list(set(removed))
    for rm in removed:
        
        tpls.remove(rm)
        
    return tpls

    
#index:当前元素索引
def del_inner_tuple(index, tpls,removed):

    tpl = tpls[index]
    size = len(tpls)
    if index == size-1:
       return removed
    for i in range(index+1, size):

        tem = tpls[i]

        if tem[0] > tpl[0] and tem[1] < tpl[1]:

            removed.append(tem)
    
    return removed


       
# *************** end 获取一个类的方法快照主程 ***************************     
#********************************************************************#  





#**********start反向查找方法起始行算法**************
LEFT_PAREN='('
RIGHT_PAREN=')'
#返回一个方法()所在的行号 (start,是否是方法)
def read_method_start(code_dic,start,braces):
    
    matched=False
    
    if start == 1: #到达第一行
       
        return  (start,matched)
    
    line=code_dic[start].strip()

    #print('当前行:{}'.format(line))

    if line.strip().find('static') == 0:

        return  (start,matched)
        
    size = len(line)
    
    #开始处理行
    for i in range(0,size): #一个字符一个字符地去读取,从后往前查找

        char = line[size-1-i]
        
        if char == LEFT_PAREN or char == RIGHT_PAREN  : #仅当符号为( 或者 ) 时执行花刮号配对算法
                   
                   braces=match_pair(braces,char,start)
                   #print('=>i={},braces={}'.format(i,braces))
                   if len(braces) == 0 : # 发现花刮号的行，处理后出现集合清空的情况，说明已找到方法的最后匹配的)
                      #print('<=matched=>')
                      matched = True
                      return (start,matched)
                  
                       
    last_line = code_dic[start-1].strip()
    #上一行
    if last_line.strip().endswith(';') or last_line.strip().endswith('{') or last_line.strip().endswith('}'): #上一行是; {结束，说明没有找到方法的特征
       return  (start,matched)
    
    start = start -1
               
    if start == 1: #第一行了 

               return (start,matched)
    else :

              return read_method_start(code_dic,start,braces)
   
#start: 当前行号
def  match_pair(braces,char,start):

     size = len(braces)
     
     if size == 0: #第一个)

         braces.append((char,start)) #生成一个Tuple，加入集合中
         return braces
     
     tailTuple = braces[size-1]

     if char == LEFT_PAREN: #当前元素(

        if tailTuple[0] == RIGHT_PAREN: # 与未尾元素配对成功

           braces.pop(size-1) #移除未尾元素Tuple
     
        else: #未尾元素tailTuple[0] 为 ( ,与char ) 未配对

           braces.append((char,start))
           
     else:#当前元素 )

           braces.append((char,start))

     return braces
          
#**********end 反向查找方法起始行算法**************




if __name__ == "__main__":

    #测试方法快照
    
    #file = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/Test/AdminService.java'
    #file='/Users/zhangxiao/agilean/valuekanban/git-adapter-server/src/main/java/cn/agilean/gitadapter/controller/GitStatController.java'
    file='/Users/source_code/dian-web/src/main/java/com/hanniu/dian/controller/adm/AdminController.java'
    find_all_methods(file)
