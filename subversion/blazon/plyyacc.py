#!/usr/bin/python

import blazon
import sys
import yacc
import treatment
import copy

from plylex import tokens,lookup

class Globals:
    colorless=[]
    colors=[]
    shield=None

def fillin(col):
    for obj in Globals.colorless:
        obj.tincture=col
    Globals.colorless=[]

start='blazon'

#def p_blazon_1(p):
#    'blazon : fulltreatment'
#    shield=blazon.Field()
#    shield.tincture=p[1]
#    Globals.shield=shield
#    p[0]=shield
#    return shield

def p_blazon_2(p):
    "blazon : fulltreatment optcharges bordure chief"
#    sys.stderr.write("top: %s %s %s %s\n"%
#                     tuple(map(str,p[1:])))
    shield=blazon.Field()
    shield.tincture=p[1]
    if p[2]:
        shield.extendCharges(p[2])
    if p[3]:
        shield.addBordure(p[3])
    if p[4]:
        shield.addChief(p[4])
    p[0]=shield
    Globals.shield=shield
    return shield

def p_optcharges(p):
    """optcharges : charges
                  | empty"""
    p[0]=p[1]

def p_fulltreatment_1(p):
    "fulltreatment : treatment"
    p[0]=p[1]
    fillin(p[0])
    
def p_fulltreatment_2(p):
    "fulltreatment : PARTYPER ORDINARY optinverted optlinetype fulltreatment AND fulltreatment"
    p[0]=lookup("per "+p[2])(p[5],p[7],linetype=p[4])
    p[3](p[0])
    fillin(p[0])

def p_fulltreatment_2_1(p):
    "fulltreatment : PARTYPER PALL optinverted optlinetype fulltreatment fulltreatment AND fulltreatment"
    p[0]=lookup("per "+p[2])(p[5],p[6],p[8],linetype=p[4])
    p[3](p[0])
    fillin(p[0])

def p_treatment_1(p):
    "treatment : COLOR"
    p[0]=treatment.Treatment(p[1])
    Globals.colors.append(p[0])
    fillin(p[0])

def p_treatment_1_b(p):
    "treatment : LP fulltreatment RP"
    # for debugging and creating really weird treatments
    p[0]=p[2]

def p_fulltreatment_3(p):
    "fulltreatment : LINEY optlinetype optamt treatment AND treatment"
    p[0]=lookup(p[1])(p[3],p[4],p[6],linetype=p[2])
    fillin(p[0])

def p_fulltreatment_4(p):
    "fulltreatment : LINEY LINEY treatment AND treatment"
    # special case for barrypily:
    check=lookup(p[1]+p[2])
    try:
        test=issubclass(check,treatment.Treatment)
    except:
        test=False
    if test:
        p[0]=check(0,p[3],p[5])
    else:
        p[0]=lookup(p[1])(0,lookup(p[2])(0,p[3],p[5]),lookup(p[2])(0,p[5],p[3]))
    fillin(p[0])

def p_treatment_4(p):
    """treatment : FUR
                 | COUNTERCHARGED"""
    p[0]=lookup(p[1])()
    fillin(p[0])

def p_treatment_5(p):
    "treatment : FURRY treatment AND treatment"
    p[0]=lookup(p[1])(p[2],p[4])
    fillin(p[0])

def p_treatment_6(p):
    "treatment : treatment ALTERED treatment"
    p[0]=lookup(p[2])(p[1],p[3])
    fillin(p[0])

def p_treatment_7(p):
    "treatment : QUARTERLY fulltreatment AND fulltreatment"
    p[0]=lookup(p[1])(p[2],p[4])
    fillin(p[0])

def p_treatment_8(p):
    "treatment : OF THE CARDINAL"
    # Not sure we can assume field is in colors[0], but maybe okay.
    d={"field":1, "first":1, "second":2, "third":3, "fourth":4, "fifth":5,
       "sixth":6, "seventh":7, "eighth":8, "ninth":9, "tenth":10, "last":0}
    n=d[p[3]]
    p[0]=Globals.colors[n-1]
    fillin(p[0])

def p_treatment_9(p):
    """treatment : COLOR SEMY OF charge
                 | COLOR SEMYDELIS treatment
                 | COLOR BEZANTY"""
    # The second is actually syntactically like ALTERED
    if len(p)==5:
        p[0]=treatment.Semy(treatment.Treatment(p[1]),p[4])
    elif len(p)==4:
        f=lookup(p[2])()
        f.tincture=p[3]
        p[0]=treatment.Semy(treatment.Treatment(p[1]),f)
    else:                               # len(p)==3
        p[0]=treatment.Semy(treatment.Treatment(p[1]),lookup(p[2])())
    fillin(p[0])

def p_opttreatment(p):
    """opttreatment : fulltreatment
                    | empty"""
    p[0]=p[1]

def p_optlinetype(p):
    """optlinetype : LINETYPE
                   | empty"""
    p[0]=p[1]

def p_charges(p):
    """charges : grouporcharge
               | charges optand grouporcharge"""
    if len(p)==2:
        p[0]=[p[1]]
    else:
        p[0]=p[1]+[p[3]]

def p_grouporcharge_a(p):
    """grouporcharge : group"""
    p[0]=p[1]

def p_grouporcharge_b(p):
    """grouporcharge : charge"""
    p[0]=blazon.ChargeGroup(1,p[1])
    if not p[1].tincture:
        Globals.colorless.append(p[0].charges[0])

def p_group(p):
    """group : amount charge
             | amount charge EACH CHARGED WITH charges"""
    p[0]=blazon.ChargeGroup(p[1],p[2])
    if len(p)>3:
        for elt in p[0].charges:
            elt.extendCharges(copy.deepcopy(p[6]))
    if not p[2].tincture:
        Globals.colorless.extend(p[0].charges)
            

def p_ordinary(p):
    """ordinary : ORDINARY
                | PALL
                | CHARGE
                | CHIEF
                | CHARGE OF amount WORD"""
    if len(p)>2:
        p[0]=lookup(p[1])(p[3])
    else:
        p[0]=lookup(p[1])()

def p_charge_1(p):
    "charge : optA ordinary optinverted optlinetype opttreatment optfimbriation"
    res=p[2]
    p[3](res)
    res.lineType=p[4]
    if not p[5]:
        if not res.tincture or not res.tincture.color or res.tincture.color == "none":
            Globals.colorless.append(res)
            res.tincture=None
    else:
        res.tincture=p[5]
    p[6](res)
    p[0]=res

def p_charge_2(p):
    "charge : ON A charge optA grouporcharge"
    p[3].addCharge(p[5])
    p[0]=p[3]

def p_bordure(p):
    """bordure : empty
               | WITHIN A BORDURE optlinetype opttreatment
               | WITHIN A BORDURE optlinetype opttreatment CHARGED WITH charges"""
    if len(p)<=2:
        p[0]=None
    else:
        p[0]=blazon.Bordure()
        if not(p[5]):
            Globals.colorless.append(p[0])
        else:
            p[0].tincture=p[5]
        if len(p)>=9 and p[8]:
            p[0].extendCharges(p[8])
        p[0].lineType=p[4]

def p_chief(p):
    """chief : empty
             | optand A CHIEF optlinetype opttreatment
             | optand ON A CHIEF optlinetype opttreatment charges"""
    if len(p)<=2:
        p[0]=None
    elif len(p)==6:
        p[0]=blazon.Chief()
        if not p[5]:
            Globals.colorless.append(p[0])
        else:
            # sys.stderr.write("Coloring a chief: (%s)\n"%p[5])
            p[0].tincture=p[5]
        p[0].lineType=p[4]
    elif len(p)==8:
        p[0]=blazon.Chief()
        if not p[6]:
            Globals.colorless.append(p[0])
        else:
            p[0].tincture=p[6]
        p[0].extendCharges(p[7])
        p[0].lineType=p[5]
    else:
        # Drop back ten and punt
        p[0]=None
    
def p_amount(p):
    """amount : NUM
              | NUMWORD"""
    p[0]=p[1]

def p_optamt(p):
    """optamt : OF amount
              | empty"""
    if len(p) == 3:
        p[0]=p[2]
    else:
        p[0]=8

def p_optinverted(p):
    """optinverted : INVERTED
                   | empty"""
    if p[1]=="inverted":
        p[0]=lambda x:x.invert()
    else:
        p[0]=lambda x:x
        
def p_optfimbriation(p):
    """optfimbriation : FIMBRIATED COLOR
                      | empty"""
    if len(p)<=2:
        p[0]=lambda x:x
    else:
        col=p[2]
        if p[1]=="voided":
            p[0]=lambda x:x.void(col)
        else:
            p[0]=lambda x:x.fimbriate(col)

def p_optand(p):
    """optand : AND
              | empty"""
    pass

def p_optA(p):
    """optA : A
            | empty"""
    pass

def p_empty(p):
    "empty :"
    pass

def p_error(p):
    ""
    sys.stderr.write("Something unexpected: %s\n"%p)
    pass

yacc.yacc(method="LALR")

if __name__=="__main__":
#    line=sys.stdin.readline()
#    while line:
#        sh=yacc.parse(line)
#        print sh
#        line=sys.stdin.readline()
   sh=yacc.parse(" ".join(sys.argv[1:]))
   print sh
    
