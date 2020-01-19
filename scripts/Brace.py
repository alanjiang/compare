# -*- coding: utf-8 -*
class Brace :
    '''
     花括号算法模型
     char: { or }
     row: line numbers
     flag:0 未match到成对的{ or }
    '''
    def __init__(self,char,row,flag):
        
        self.char=char
        self.row=row
        self.flag=flag
        
