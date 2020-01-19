# -*- coding: utf-8 -*
class VariableFreq :

    '''
     @ method_str : 方法
     @ variable: 变量名
     @ freq:[(row,times, type) ]  如： [(1,1,'equal'), (2,1,'call'), (2,2,'call'), (3,1,'param') ]
         (1,1,'equal')： 第1行，调用第一次，赋值
          (2,1,'call')：  第2行，调用第一次，方法调用
          (3,1,'param')： 第3行，调用第一次，参数
          
    '''
    def __init__(self, method_str,variable,freq):
        
        self.method_str=method_str
        
        self.variable = variable

        self.freq = freq 
   
