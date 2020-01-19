# -*- coding: utf-8 -*-
import shutil
import re
import os

import  function_extract   as   func
import batch_decompiler as dec

from method_mark import *
import time

import UI as ui


'''
 @Author : 姜鹏 jiangpeng@126.com

 Date: 2019/12/02

 (1) 替换 this.XXX.DD 中的 this, 单个文件替换

 (2) 替换相比较的两个文件变量名修改的情况，两个文件的比较替换

 反编译之后进行重写

'''



CHARSET='utf-8'

#如果有this.XXX.XXX，返回是否降噪  
def replaceThis (lines,file):

    size =  len(lines)

    found = False
    for i in range(0,size):
       
       pattern = re.compile(r'(this\.[0-9a-zA-Z_]+\.[0-9a-zA-Z_]+)',re.I)
       
       match = pattern.search(lines[i])
       
       if match:
          found = True
          lines[i] = lines[i].replace('this.','')

    if found: #仅仅有行变动才执行重写

        with open(file,'w',encoding=CHARSET, errors = 'ignore') as f:
          f.seek(0)
          f.truncate()
          for line in lines:
              
             f.write(line+'\n')
             #f.write(line)
    
    return found

#消除噪音：1，消除多余 this.XX.XX中的this.

#代码行有差异的文件才进行降噪处理
#返回是否降噪处理
def eleminate_noisy(file1,file2):

   dic_file_methods_1={}
   dic_file_methods_2={}
   dic_file_methods_1[file1]=func.extremelyFindMethod(file1)
   dic_file_methods_2[file2]=func.extremelyFindMethod(file2)
    
   #代码行字典,可以拿到任意两个整数之间的所有行，即函数体内容
   lines1 = func.read_file(file1) #文件所有的行
   code_dic1=func.getCodeDic(lines1) #文件所有的行字典，key:行号,value:行内容

   lines2 = func.read_file(file2) 
   code_dic2=func.getCodeDic(lines2) #文件所有的行字典，key:行号,value:行内容
   #print('=>first row:{}'.format(code_dic1[1]))
   markers1=dic_file_methods_1[file1]
  
   markers2=dic_file_methods_2[file2]
   #得到新文件经过替换变量的方法标记
   tpl = eleminate_method_noisy(markers1,markers2,code_dic1,code_dic2)
   markers1 = tpl[0]
   markers2 = tpl[1]
   count = tpl[2]
   #两个文件全部重写
   #print('=>size1:{},size2:{}'.format(len(markers1),len(markers2)))
   write_lines_file(code_dic1,markers1,file1)
   write_lines_file(code_dic2,markers2,file2)
  

# 将行集合写入到文件中
# code_dic: 原有的行字典, method_markers:替换变量后的方法标记,对文件file进行修改
def write_lines_file(code_dic,method_markers,file2):

    '''
    content = ''
    with open(file2, 'r',errors='ignore') as f:
         content = f.read()
    '''
    for mk in method_markers:

        
        start =  mk.start
        end = mk.end
        lines = mk.body.splitlines()
        
        if len(lines) != (end-start+1):
            print('warning:算法不适用,lines size:{},start:{},end:{},file:{},method:{}'.format(len(lines),mk.start,mk.end,mk.file,mk.method))
            return
        row = -1
        for index in range(start,end+1): #[start-end]区间
            row+=1
            #print('=>index:{},row:{}'.format(index,row))
            try:
              code_dic[index] = lines[row]
            except Exception as e:
              print(e)
        '''
        old_body = func.getCodeByRowNumbers(code_dic,mk.start, mk.end)
        new_body = mk.body
        content =  content.replace(old_body,new_body)
        '''
     
         
    #将字典内容写入文件
    with open(file2,'w',encoding=CHARSET, errors = 'ignore') as file:
       file.seek(0)
       file.truncate()
       
       for key in code_dic:

           file.write(code_dic[key]+'\n')
       
       #file.write(content)
   
        

                   
#备份功能                  
def back_folder(dest1,dest2):
     timestr = time.strftime('%Y-%m-%d%H%M%S',time.localtime(time.time()))
     parent_path1 = os.path.dirname(dest1)

     parent_path2 = os.path.dirname(dest2)

     back1 = parent_path1+'/dest1-'+timestr

     back2 = parent_path2+'/dest2-'+timestr

     if os.path.exists(back1):
         os.remove(back1)
     if os.path.exists(back2):
         os.remove(back2)   
     shutil.copytree(dest1, back1)
     shutil.copytree(dest2, back2)

#不改变原有的文件夹，创建新的     
def new_folder(dest1,dest2):
     timestr = time.strftime('%Y-%m-%d-%H%M%S',time.localtime(time.time()))
     parent_path1 = os.path.dirname(dest1)

     parent_path2 = os.path.dirname(dest2)

     back1 = parent_path1+'/dest1-'+timestr

     back2 = parent_path2+'/dest2-'+timestr

     if os.path.exists(back1):
         os.remove(back1)
     if os.path.exists(back2):
         os.remove(back2)   
     shutil.copytree(dest1, back1)
     shutil.copytree(dest2, back2)

     return (back1,back2)
'''
method_no_param:public void addAdmin(['Admin', 'Select'])  throws Exception{,

#变量及出现的行号、次数
variables:[('m', 'Merchandise', '', [(17, 1), (18, 1), (19, 1), (20, 1), (21, 1)]),
           ('merchandises', 'List<Merchandise>', '', [(15, 1), (16, 1), (17, 1), (23, 1)]),
          ('newShop', 'Shop', '', [(6, 1), (11, 1), (20, 1), (28, 1), (30, 1)]),
          ('sdf', 'SimpleDateFormat', '', [(2, 1), (4, 1), (19, 1)]),
          ('shop', 'Shop', '', [(3, 1), (4, 1), (5, 1), (6, 1)]),
          ('sortIds', 'List<Long>', '', [(9, 1), (12, 1), (21, 1)]),
          ('sorts', 'List<Sort>', '', [(8, 1), (10, 1)]),
          ('terminals', 'List<Terminal>', '', [(26, 1), (27, 1), (36, 1)])],
#方法的参数Tuple集合
params:[('admin', 'Admin', 'final'), ('select', 'Select', '')]

'''

#markers1,markers2 来源于有代码行差异的文件，没有代码行差异的文件不作比较
#两个方法名、形参一样，才考虑替换变量降噪
#found : markers对应的文件是否降噪处理
def eleminate_method_noisy(markers1,markers2,code_dic1,code_dic2) :
     count = 0
     
     size = len(markers2)

     index1 = -1
     #print('size1:{},size2:{}'.format(len(markers1),len(markers2)))
     #*********开始外循环比较*********
     for mk1 in markers1:

       index1+=1
       replaced = False
      
       #print('******* 开始外层方法:{}'.format(mk1.method_no_param))

       index = -1
       
       for mk2 in markers2:

           index+=1
          
           #**********开始找到两方法一致后开始对比替换变量***********************
           if mk1.method_no_param != mk2.method_no_param:
              
              continue
            
           #print('=>Found,method_no_param:{},{}'.format(mk1.method_no_param,mk2.method_no_param))
           #***********开始找到匹配方法的逻辑*************
           if mk1.body != mk2.body: # 方法体不一样了，需要降噪音

                 #step1,先重置方法体null表达式
                 mk1.body = replaceNullBody(mk1.body)
                 mk2.body = replaceNullBody(mk2.body)
                 mk1=MethodMarker(mk1.method,mk1.method_str,mk1.method_str_rows,mk1.start,mk1.end,mk1.body,mk1.variables,mk1.params,mk1.method_no_param)
                 mk2=MethodMarker(mk2.method,mk2.method_str,mk2.method_str_rows,mk2.start,mk2.end,mk2.body,mk2.variables,mk2.params,mk2.method_no_param)
                 markers2[index]=mk2
                 markers1[index1]=mk1
                 #end

                 #start valueOf
                 mk1.body = replaceValueOfExpressBody(mk1.body)
                 mk2.body = replaceValueOfExpressBody(mk2.body)
                 mk1=MethodMarker(mk1.method,mk1.method_str,mk1.method_str_rows,mk1.start,mk1.end,mk1.body,mk1.variables,mk1.params,mk1.method_no_param)
                 mk2=MethodMarker(mk2.method,mk2.method_str,mk2.method_str_rows,mk2.start,mk2.end,mk2.body,mk2.variables,mk2.params,mk2.method_no_param)
                 markers2[index]=mk2
                 markers1[index1]=mk1
                 #end valueOf
                 
                 #step2,先重置子接口实现表达式
                 
                 mk1.body = replace_children_variables(mk1.body)
                 mk2.body = replace_children_variables(mk2.body)
                 mk1=MethodMarker(mk1.method,mk1.method_str,mk1.method_str_rows,mk1.start,mk1.end,mk1.body,mk1.variables,mk1.params,mk1.method_no_param)
                 mk2=MethodMarker(mk2.method,mk2.method_str,mk2.method_str_rows,mk2.start,mk2.end,mk2.body,mk2.variables,mk2.params,mk2.method_no_param)
                 markers2[index]=mk2
                 markers1[index1]=mk1

             

                 #step3,重置所有的方法体内的泛型变量

                 mmks = replace_method_variables(mk1,mk2,code_dic1,code_dic2)
                
                 mk1 =  mmks[0]
                 
                 mk2= mmks[1]

                 
                 '''
                 mk1.variables = tpl[0].variables

                 mk2.body = tpl[1].body
                 mk2.variables = tpl[1].variables
                 '''
                 markers2[index]=mk2
                 markers1[index1]=mk1
                 
                 replaced = True
                 #print('==>params:{},{}'.format(mk1.params,mk2.params))
                 #*********开始方法参数替换*************** 
                 if mk1.params != mk2.params: #方法参数变量名不一致，方法参数中变量替换的同时，替换掉方法体中的变量

                    #开始处理参数
                    params1 = mk1.params
                    params2 = mk2.params

                    size = len(params1)
                    
                    for i in range(0,size):

                        variable1 = params1[i][0]

                        variable2 = params2[i][0]

                        #print('var1:{},var2:{}'.format(variable1,variable2))

                        if variable1 != variable2: #变量名不相等

                            #index的递归调用,替换变量,依据变量的合理性来判断替换mk1还是mk2的body

                            if variable1.find('var') == 0: #以'var'开头的变量，用文件2的变量替换文件1
                            
                                body = replace_variable_body(mk1.body,variable1,variable2)
                            
                                mk1=MethodMarker(mk1.method,mk1.method_str,mk1.method_str_rows,mk1.start,mk1.end,body,mk1.variables,mk1.params,mk1.method_no_param)
                                
                            else: #不以'var'开头的变量，用文件1的变量variable1替换文件2中的变量variable2
                                   
                                body = replace_variable_body(mk2.body,variable2,variable1)
                            
                                mk2=MethodMarker(mk2.method,mk2.method_str,mk2.method_str_rows,mk2.start,mk2.end,body,mk2.variables,mk2.params,mk2.method_no_param)
                                
                            
                            count+=1
                           
                    markers1[index1]=mk1
                    markers2[index]=mk2
                 #**************结束方法参数替换*****************          
                 #开始处理内部变量
                 variables1 = mk1.variables
                 variables2 = mk2.variables

                 #************开始处理方法内部变量替换*************************    
                 if variables1 != variables2: #相等意味着变量个数、名称、代码行出现的次数均一致

                     size1 = len(variables1)
                     size2 = len(variables2)
                     
                     if size1 == size2: #两边的变量个数一样才处理

                         for x in range(0,size1):
                             
                             
                             tpl1 = variables1[x]
                             tpl2 = variables2[x]

                             variable1 = tpl1[0]
                             variable2 = tpl2[0]
                             #变量类型等价替换
                             type1 = tpl1[1].replace('HashMap','Map').replace('ArrayList','List').replace('HashSet','Set').replace('LinkedList','List')
                             type2 = tpl2[1].replace('HashMap','Map').replace('ArrayList','List').replace('HashSet','Set').replace('LinkedList','List')
                             
                             #if tpl1[1] == tpl2[1] and tpl1[3] == tpl2[3]: #变量类型和[(出现行号、次数),...]均相等执行替换
                             if type1 == type2: #变量类型相等执行替换
                                     if variable1 != variable2: #两个变量不相等才执行替换
                                        if variable1.find('var') == 0: #以'var'开头的变量，用文件2的变量替换文件1
                            
                                           body = replace_variable_body(mk1.body,variable1,variable2)
                            
                                           mk1=MethodMarker(mk1.method,mk1.method_str,mk1.method_str_rows,mk1.start,mk1.end,body,mk1.variables,mk1.params,mk1.method_no_param)
                                
                                        else: #不以'var'开头的变量，用文件1的变量variable1替换文件2中的变量variable2
                                   
                                           body = replace_variable_body(mk2.body,variable2,variable1)
                            
                                           mk2=MethodMarker(mk2.method,mk2.method_str,mk2.method_str_rows,mk2.start,mk2.end,body,mk2.variables,mk2.params,mk2.method_no_param)
                            
                                        count+=1
                         markers1[index1]=mk1
                         markers2[index]=mk2
           #************结束处理方法内部变量替换*************************   

           #***********开始找到匹配方法的逻辑*************
           #处理下一个方法
           
           #print('==>replaced:{}'.format(replaced))
           '''
           if replaced:
                  print('******降噪的方法*********')
                  print(mk2.method_str)                         
           '''
           break
                    
           #**********结束找到两方法一致后开始对比替换变量***********************
           

     #*********结束外循环比较*********
                                                
     return  (markers1,markers2,count)            



  
#将一个完整的方法体直接替换变量名，含方法参数的变量名,方法内部定义的变量名
def replace_variable_body(body,old_variable,new_variable):

    #print('old_variable:{},new_variable:{}'.format(old_variable,new_variable))
    if not body:

        print('==>body NonType<==')
        
        return body;

    str=''

    #替换时，第一行需要跳过方法名，避免变量与方法名称一致，错误替换
    count = 0
    for line in body.splitlines():

        count+=1

        if count == 1:

            index = line.find('(')
            row = func.replace_valid_varaibles(line,old_variable,new_variable,index)
        else:
            
            row = func.replace_valid_varaibles(line,old_variable,new_variable,0)
        '''
        if line != row:

            #print('old row:{},new row:{}'.format(line,row))
        '''
        str = str +row+'\n'
        
    return str   


#将方法体整体替换null表达式
def replaceNullBody(body):

    content = ''
    rows = body.splitlines()

    for row in rows:

      row = replaceNullExpress(row)

      content+=row+'\n'

    return content
    

# 替换所有的 if (*+ express !== null *+ ) 成if (*+ express !== null *+ ) if (*+ null !== express *+ ) 
#替换算法主程
def replaceNullExpress(row):

   
   # (1) 变量 != null  (2) 变量.方法(参数) != null (3) 方法(参数) != null
   pattern = re.compile(r'([0-9A-Za-z_]+)(\s*)([!=]{2})(\s*)([0-9a-zA-Z]+)|([0-9A-Za-z_\.]+\s*\([0-9A-Za-z\_\"\,]*\))(\s*)([!=]{2})(\s*)([0-9a-zA-Z]+)|([0-9A-Za-z_]+\s*\([0-9A-Za-z\_\"\,]*\))(\s*)([!=]{2})(\s*)([0-9a-zA-Z]+)')
   res = pattern.findall(row)

   if res:


      for tpl in res:
        #左边,空格,条件,空格,null
        if tpl[4] == 'null':
           old_str = tpl[0]+tpl[1]+tpl[2]+tpl[3]+tpl[4]
           new_str = tpl[4]+tpl[1]+tpl[2]+tpl[3]+tpl[0]
           row = row.replace(old_str,new_str)
           row = row.replace('this.null','null')
           #print('=>old_str:{},new_str:{},row:{}'.format(old_str,new_str,row))

   #方法调用的NULL表达式
   pattern = re.compile(r'([0-9A-Za-z_\.]+\s*\([0-9A-Za-z\_\"\,]*\))(\s*)([!=]{2})(\s*)([0-9a-zA-Z]+)')
   res = pattern.findall(row)
   if res:

      for tpl in res:
        #左边,空格,条件,空格,null
        if tpl[4] == 'null':
           old_str = tpl[0]+tpl[1]+tpl[2]+tpl[3]+tpl[4]
           new_str = tpl[4]+tpl[1]+tpl[2]+tpl[3]+tpl[0]
           row = row.replace(old_str,new_str)
           row = row.replace('this.null','null')
   
   return row

#************start 统一替换子类为父类变量 ************





# ****** start ValueOf ******************

def replaceValueOfExpressBody(body):

    content = ''

    rows = body.splitlines()

    for row in rows:

        # + 连接的StringValueOf
        row = replaceValueOfExpress(row)
        #持续替换单独的valueOf
        row = replaceStandaloneValueOfExpress(row)
        # a = a + express
        row = replaceVariableEqualExpress(row)
        #StringBuilder
        row = replaceStringBuilderExpress(row)
        #this.a = this.a + express
        row = replaceThisEqualExpress(row)
        content+=row+'\n'
       
    return content

 

# 将  s = String.valueOf(s) +abc 转换成  s += abc
def replaceValueOfExpress(row):


    pattern = re.compile(r'([0-9a-zA-Z\_]+)(\s*)([=]{1})(\s*)(String.valueOf\((.+?)\))(\s*[+]{1})')

    p = pattern.search(row)

    if p:
        
        #print('1=>{}'.format(p.group(1)))
        #print('2=>{}'.format(p.group(2)))
        #print('3=>{}'.format(p.group(3)))
        #print('4=>{}'.format(p.group(4)))
        #print('5=>{}'.format(p.group(5)))
        #print('6=>{}'.format(p.group(6)))
        #print('7=>{}'.format(p.group(7)))
        if p.group(6).strip() == p.group(1)  or p.group(6).strip() == p.group(1).replace('this.','') :

            old_str = p.group(1)+p.group(2)+p.group(3)+p.group(4)+p.group(5)+p.group(7)
            #print('=>old_str:{}'.format(old_str))
            #new_str = p.group(1)+p.group(2)+'+'+p.group(3)+p.group(4)
            new_str = p.group(1)+p.group(2)+'+'+p.group(3)
            #print('=>new_str:{}'.format(new_str))
            row = row.replace(old_str,new_str)

        else:
            old_str= p.group(5)
            new_str = p.group(6)
            #print('=>old_str:{}'.format(old_str))
            #print('=>new_str:{}'.format(new_str))
            row = row.replace(old_str,new_str)

    return row



#单独的String.valueOf(xxx)+express | express+String.valueOf(xxx) 替换成 xxx+express | express+xxx

#eg: final String operTime = String.valueOf(time.substring(0, 2)) + ":" + time.substring(2, 4) + ":" + time.substring(4, 6);
           
def replaceStandaloneValueOfExpress(row):


    pattern = re.compile(r'([+]{1}\s*)(String.valueOf\((.+?)\))') #左边有+

    p = pattern.search(row)
    
    if p:

        old_str =  p.group(2)
        new_str = p.group(2)
        row = row.replace(old_str,new_str)

    pattern = re.compile(r'(String.valueOf\((.+?)\))(\s*[+]{1})') #右边有+
    p = pattern.search(row)
    
    if p:

        #print('=>p1:{}'.format(p.group(1)))
        #print('=>p2:{}'.format(p.group(2)))
        #print('=>p3:{}'.format(p.group(3)))
        old_str =  p.group(1)
        new_str = p.group(2)
        row = row.replace(old_str,new_str)


    
    
    return row
 




# ******* end valueOf ******************



#start of a = a+express
#msg = msg + ",;" + orgNo + ",@;" + orgNo + "-" + orgName;
# 变量等号连接降噪
def replaceVariableEqualExpress(row):


    pattern = re.compile(r'([0-9a-zA-Z\_]+)(\s*)([=]{1})(\s*)([0-9a-zA-Z\_]+)(\s*)([+]{1})')

    p = pattern.search(row)

    if p:

        if p.group(1) == p.group(5):
          #print(p.group(3))
          old_str =  p.group(1)+p.group(2)+p.group(3)+p.group(4)+p.group(5)+p.group(6)+p.group(7)
          new_str =  p.group(1)+p.group(2)+'+'+p.group(3)
          #print('=>old:{},new:{}'.format(old_str,new_str))
          row = row.replace(old_str,new_str)

    
    return row
 

#end of a = a+express


#start StringBuilder降噪
#this.updateOrgOperateFHSEQ(seq, seqNo2, new StringBuilder().append(this.currentUser).toString(), this.workDate);
#this.updateOrgOperateFHSEQ(seq, seqNo2, "" + this.currentUser, this.workDate);

def replaceStringBuilderExpress(row):


    pattern = re.compile(r'(new\s*StringBuilder\(\)\.append\((.+?)\)\.toString\(\))')
    
    res = pattern.findall(row)

    if res:

        #print(res)
        for ele in res:

            old_str =  ele[0]
            new_str = '"" + '+ele[1]
            row = row.replace(old_str,new_str)

    pattern = re.compile(r'(new\s*StringBuilder\(String.valueOf\((.+?)\)\)\.toString\(\s*\))')

    res = pattern.findall(row)
    
    if res:

        #print(res)
        for ele in res:

            old_str =  ele[0]
            new_str = ele[1]+' + ""'
            row = row.replace(old_str,new_str)
    row = row.replace('"" + ','')
    row = row.replace(' + ""','')
    return row
 
#end StringBuilder降噪

#start this.XX = XX+express 降噪
#this.stopReason = this.stopReason + entry.getValue(); 转换成： this.stopReason += entry.getValue();
def replaceThisEqualExpress(row):


    pattern = re.compile(r'(this\.[0-9a-zA-Z\_]+)(\s*)([=]{1})(\s*)(this.[0-9a-zA-Z\_]+)(\s*)([+]{1})')

    p = pattern.search(row)

    if p:

        if p.group(1) == p.group(5):
          #print(p.group(3))
          old_str =  p.group(1)+p.group(2)+p.group(3)+p.group(4)+p.group(5)+p.group(6)+p.group(7)
          new_str =  p.group(1)+p.group(2)+'+'+p.group(3)
          #print('=>old:{},new:{}'.format(old_str,new_str))
          row = row.replace(old_str,new_str)

    
    return row
 

#end this.XX = XX+express 降噪

def replace_children_variables(body):

    if body == '':
        return body
    else:
      new_body = ''
      for row in body.splitlines():

          row = replace_children_varaible_by_row(row)
          new_body+=row+'\n'
          
      
      return new_body    


#任意一行，替换子接口为上层接口变量

STANDARDS = [('Map',['HashMap','TreeMap','LinkedHashMap']), ('Set',['HashSet']),('List',['ArrayList','LinkedList']),('InputStream',['FileInputStream']),('NumberFormat',['DecimalFormat'])]

def replace_children_varaible_by_row(row):

    row = row.strip()
    
    for stand in STANDARDS:

        col = stand[1]

        for var in col:

            index = row.find(var)# = 左边的变量类型
            size = len(var)
            if index == 0: #必须行首

                #print('==>变量:{}需要替换'.format(var))

                right_char = row[size]#右边必须为空

                #print('==>right_char:{},size:{}'.format(right_char,len(right_char)))
                if right_char == ' ':

                    row = stand[0]+row[size:]

                    return row
    return row          





#************end 统一替换子类为父类变量 ************



#*********************start 泛型变量统一替换 ****************************#
#mk1,mk2 ，文件1和文件2中两同名方法标记对象
#上一步骤已经将HashMap map 变成Map map
'''
variables:[
('col', 'int[]', '', [(2, 1), (5, 1)], 1), 
('i', 'int', '', [(3, 1), (5, 1), (6, 1)], 2), 
('s', 'String', '', [(5, 1)], 3), 
('dog', 'HashMap', '', [(8, 1)], 4)]

'''
def replace_method_variables(mk1,mk2,code_dic1,code_dic2):

    v1s = mk1.variables

    v2s = mk2.variables

    if len(v1s) != len(v2s): #变量长度不相等不处理

        return (mk1,mk2)
    
    size = len(v1s )
    for index in range(0,size):

        v1 = v1s[index] #第i个变量Tuple
        v2 = v2s[index]
        if v1[3] == v2[3]: #变量出现位置次数一样
            
           if v1[1] != v2[1]:#变量类型不相等
           
              v1Type = find_children_variable_type(v1[1])
              v2Type= find_children_variable_type(v2[1])

              if v1Type[0] == v2Type[0]: #类型一样
           
                  if  v1Type[1] == '' and v2Type[1] != '':  # v2变量为正则, v1不为正则，去掉泛型符号

                       v2s[index] = (v2[0],v2Type[0],v2[2],v2[3]) # 用非泛型替代变量
                       #同时获取变量所在的行
                       row2 = code_dic2[(v2[3][0][0]+mk2.start)]
                       row2_new = replace_variable_type(row2,v2[1],v2Type[0])
                       mk2.body = mk2.body.replace(row2,row2_new)
                       mk2.variables = v2s
                  elif v1Type[1] != '' and v2Type[1] == '':  # v1变量为正则, v2不为正则，去掉泛型符号
                       v1s[index] = (v1[0],v1Type[0],v1[2],v1[3]) # 用非泛型替代变量

                       row1 = code_dic1[(v1[3][0][0]+mk1.start)]
                       row1_new = replace_variable_type(row1,v1[1],v1Type[0])

                       mk1.body = mk1.body.replace(row1,row1_new)
                       mk1.variables = v1s
                      
              else:# 类型不一样
                  
                  type1 = find_parent_variable(v1Type[0])
                  type2 = find_parent_variable(v2Type[0])
                  
                  if type1[0] == type2[0]:

                    v2s[index] = (v2[0],type1[0],v2[2],v2[3]) # 用非泛型替代变量
                    v1s[index] = (v1[0],type2[0],v1[2],v1[3]) # 用非泛型替代变量
                    row2 = code_dic2[(v2[3][0][0]+mk2.start)]
                    row2_new = replace_variable_type(row2,v2[1],v2Type[0])
                    row1 = code_dic1[(v1[3][0][0]+mk1.start)]
                    row1_new = replace_variable_type(row1,v1[1],v1Type[0])

                    mk1.body = mk1.body.replace(row1,row1_new)
                    mk2.body = mk2.body.replace(row2,row2_new)
                    mk1.variables = v1s
                    mk2.variables = v2s
                  else: #类型不一致

                    print('不一致类型:{},{}'.format(type1,type2))
                
                 
        else:#变量出现位置次数不一样，不处理

           pass
    #print('==>variables1:{},variables2:{}'.format(mk1.variables,  mk2.variables))  
    return (mk1,mk2)


#将row行内空的变量类型替换
#type: 变量类型
def replace_variable_type(row,old_type,new_type):

   index =  row.find(old_type)

   if index != -1:

       if index == 0:

         return new_type+row[(index+len(old_type)):]
       else:
        if row[index-1] == ' ' and row[index+1] == ' ':
            
           return new_type+row[(index+len(old_type)):]
        
   return row

#直接返回上层父类接口
#variable:不带范型的变量部分 
def find_parent_variable(variable):

    for stand in STANDARDS:

        col = stand[1]

        for var in col:

          if variable == var:

              return (stand[0],True) #返回上层接口

            
    return (variable, False)   


# variable范型变量,返回泛型类型及<>部分
def find_children_variable_type(variable):

    regexFound = False

    if variable.find('<') != -1:
        
        p = re.compile(r'([0-9A-Za-z_]+)(<[0-9A-Za-z_,<>]+>)')

        match = p.search(variable)
                   
        if match:

           variable_left = match.group(1) # type
           variable_right = match.group(2) #<XXXX>部分
           regexFound = True
    
    if regexFound:

       return (variable_left,variable_right)
    return (variable,' ')


#*********************end 泛型变量统一替换 ****************************#


if __name__ == "__main__":


    #测试将文件替换this.后，将file移动到dest的上一级back目录，再将新的内容与入到file
    
    #降噪处理测试
    #file1 = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest1/AdminService.java'

    #file2 = '/Users/zhangxiao/agilean/valuekanban/python-anti-compile/scripts/examples/dest2/AdminService.java'

    #eleminate_noisy(file1,file2)

    #替换变量
    #row = 'HashMap dog = new HashMap();'

    #row = replace_children_varaible(row)

    #print(row)
   
    '''
    #row = "if (CapAcct != null && CapAcct.equals('abc')) {"

    #row = "if ( CapAcct.equals('abc') && CapAcct != null) {"
    
    #row = 'if (!"".equals(erroMessage) && errorMessage != null) {'
    #row = replaceNullExpress(row)

    #print(row)
    '''
   
    '''
    #测试成对出现()元组集合
    
    str='public ModelAndView browseMerchandise(@PathVariable int pageNo ,ModelMap map,HttpServletRequest request,\n'
    str+='@PathVariable Long shopid, @RequestParam(value="sort",required=false) Long sort,\n'
    str+=' @RequestParam(value="publish",required=false) Integer publish '
    str+=') {'
    print(str)
    strs = str.splitlines()
    for s in strs:
       char1='('
       char2=')'
       col = func.find_angle_barces(s,char1,char2)
       
       print('=>col:{}'.format(col))
    '''
    #valueOf测试
    #row = 'final String operTime = String.valueOf(time.substring(0, 2)) + ":" + time.substring(2, 4) + ":" + time.substring(4, 6);'
    #row='final String OPERA_TIME = String.valueOf(time.substring(0, 2)) + ":" + time.substring(2, 4) + ":" + time.substring(4, 6);'
    #row='final String time = String.valueOf(time) + ":" + time.substring(2, 4) + ":" + time.substring(4, 6);'
    #row = replaceStandaloneValueOfExpress(row)
    #row = replaceValueOfExpress(row)
    
    #print(row)
    #测试变量拼接
    #row='msg = msg + ",;" + orgNo + ",@;" + orgNo + "-" + orgName; ';
    #row = replaceVariableEqualExpress(row)
  
    #print(row)

    #row = 'this.updateOrgOperateFHSEQ(seq, seqNo2, new StringBuilder().append(this.currentUser).toString(), this.workDate);'
    #this.updateOrgOperateFHSEQ(seq, seqNo2, "" + this.currentUser, this.workDate);
    #测试StringBuilder
    #row='text_Count.setText(new StringBuilder(String.valueOf(pageMax)).toString());'
    #row = replaceStringBuilderExpress(row)

    #print(row)

    row = 'this.stopReason = this.stopReason + entry.getValue(); '
    row = replaceThisEqualExpress(row)
    
    print(row)
