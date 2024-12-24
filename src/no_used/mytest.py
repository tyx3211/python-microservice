# class A(Exception):
#     def __init__(self,message):
#         super().__init__(message)
        
# class B(A):
#     def __init__(self,message):
#         super().__init__(message)

# class C(A):
#     def __init__(self,message):
#         super().__init__(message)


# def judge(e):
#     if isinstance(e,B):
#         return True
#     if isinstance(e,C):
#         return True
#     return False

# def test2(n):
#     try:
#         if n==1:
#             raise B("B")
#         elif n==2:
#             raise C("C")
#         else:
#             raise Exception("A")
#     except Exception as e:
#         if judge(e):
#             raise
#         else:
#             raise A(f"{e}")


# def test1(n):
#     try:
#         test2(n)
#     except B:
#         print("B")
#     except C:
#         print("C")
#     except A as e:
#         print(f"Origin-A {e}")
        
# test1(1)
# test1(2)
# test1(3)


# 密码相关

# import bcrypt

# pw = "hfwf82rufwhffw"

# hashed_pw = bcrypt.hashpw(pw.encode('utf-8'),bcrypt.gensalt()) #将用户密码加盐哈希

# stored_pw = hashed_pw.decode('utf-8')

# print(stored_pw)

# print(bcrypt.checkpw(pw.encode('utf-8'), stored_pw.encode('utf-8')))


# 试验传出参数,用字典

def myTest(n,result):
    if n==1:
        result["result"] = 3
        return False
    if n==2:
        result["result"] = 5
        return False
    return True

result = {} # 字典传出参数

if myTest(1,result) is False:
    print(result["result"])
    
if myTest(2,result) is False:
    print(result["result"])
    
if myTest(3,result) is False:
    print(result["result"])

myList = [2, 4, 7, 3, 7, 2, 3, 8]

print(myList)

def sort(l:list):
    for i in range(len(l)):
        for j in range(i+1,len(l)):
            if l[i] > l[j]:
                temp = l[j]
                l[j] = l[i]
                l[i] = temp

sort(myList) # 进行排序

print(myList) # 排序结果                



