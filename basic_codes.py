def letter_count_cs(name):
    size = len(name)
    dic = {}
    for i in range(size):
        if name[i] not in dic:
            dic[name[i]] = 1
        else:
            dic[name[i]] += 1
    return dic
    
    # // 1222233344113

def letter_count_cis(name):
    name = name.lower()
    size = len(name)
    dic = {}
    for i in range(size):
        if name[i] not in dic:
            dic[name[i]] = 1
        else:
            dic[name[i]] += 1
    return dic
    
def int_number_count():
    while True:
        num = int(input("Enter a number : "))
        if not float:
            pass
        else:
            break
    print(num)
    num_dict = {}
    while num > 0:
        one_digit = num % 10
        if one_digit not in num_dict:
            num_dict[one_digit] = 1
        else:
            num_dict[one_digit] += 1
        num //= 10
    return num_dict
    
def is_string_num_symb():
    alpha = []
    num = []
    sym = []
    alpnum = []
    
    while True:
        inp = input("Enter your input: ")
        if inp == "":
            break
        
        if inp.isdecimal():
            num.append(inp)
        elif inp.isalpha():
            alpha.append(inp)
        elif inp.isalnum():
            alpnum.append(inp)
        else:
            sym.append(inp)
    
    num.sort()
    alpha.sort()
    alpnum.sort()
    sym.sort()
    
    final_list = sym + num + alpnum + alpha
    
    print(num)
    print(alpnum)
    print(alpha)
    print(sym)
    
    
    return final_list
    
n = is_string_num_symb()
print(n)
        

# name = input("Enter your input: ")
# print("Case Sensitive : ")
# k = letter_count_cs(name)
# print(k)
# print()
# print("Case Insensitive : ")
# l = letter_count_cis(name)
# print(l)
# print()
# m = int_number_count()
# print(m)


