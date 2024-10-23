import datetime

def vl(k: str):
    
    p1 = k.split('-')
    if len(p1) != 4:
        return False, '', 0
    p2 = p1[0]
    p3 = p1[1]
    p4 = p1[2]
    p5 = p1[3]
    
    k1 = p2[1]
    k2 = p2[4]
    k3 = p3[0]
    k4 = p3[2]
    k5 = p4[2]
    k6 = p5[1]
    
    s2 = p5[-1] + p4[-1]
    s2 = int(s2)
    
    koop = k1 + k2 + k3 + k4 + k5 + k6
    
    try:
        res = datetime.datetime.strptime(koop, '%y%m%d').date()
        return True, res, s2
    except:
        return False, '', 0