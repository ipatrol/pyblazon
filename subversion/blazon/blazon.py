#!/usr/bin/python
# -*- coding: latin-1 -*-
import SVGdraw
import math
import sys
import copy
import re

from pathstuff import partLine
from tinctures import *

# For the sake of argument, let's assume the base background SVG is 100x125
# in user-units, starting from 0,0 at top left.  Most ordinaries will also
# be the same size and same location--only they'll have clipping paths,
# which may also be stroked.  Then we can just fill the whole ordinary (or
# a rectangle filling it).

class Ordinary:
   id=0
   FESSPTX=50
   FESSPTY=50
   HEIGHT=110
   WIDTH=100

   CHIEFPTY=-FESSPTY+15
   DEXCHIEFX=-FESSPTX+15
   SINCHIEFX=FESSPTX-15
   
   DEXCHIEF=(DEXCHIEFX,CHIEFPTY)
   SINCHIEF=(SINCHIEFX,CHIEFPTY)
   CHIEFPT=(0,CHIEFPTY)

   FESSEPT=(0,0)
   
   BASEPT=(0,FESSPTY-6)

   DEXSIDE=(DEXCHIEFX+15,0)
   SINSIDE=(SINCHIEFX-15,0)

   def __init__(self,*args,**kwargs):
      self.setup(*args,**kwargs)

   def setup(self,tincture="argent",linetype="plain"):
      self.done=False
      self.tincture=Tincture(tincture)
      self.lineType=linetype
      self.charges=[]
      self.fimbriation_width=4          # default
      if not hasattr(self,"svg"):
         self.svg=SVGdraw.svg(x=-Ordinary.FESSPTX,
                              y=-Ordinary.FESSPTY,
                              width=Ordinary.WIDTH,
                              height=Ordinary.HEIGHT,
                              viewBox=(-Ordinary.FESSPTX,
                                       -Ordinary.FESSPTY,
                                       Ordinary.WIDTH,
                                       Ordinary.HEIGHT))
      self.clipPathElt=SVGdraw.SVGelement('clipPath',
                                          id=('Clip%04d'%Ordinary.id))
      Ordinary.id=Ordinary.id+1
      self.svg.addElement(self.clipPathElt)
      self.svg.attributes["xmlns:xlink"]="http://www.w3.org/1999/xlink"
      self.maingroup=SVGdraw.group()
      self.maingroup.attributes["clip-path"]="url(#%s)"%self.clipPathElt.attributes["id"]
      self.baseRect=SVGdraw.rect(x=-Ordinary.FESSPTX,
                                 y=-Ordinary.FESSPTY,
                                 width=Ordinary.WIDTH,
                                 height=Ordinary.HEIGHT)
      # Not the best solution...
      self.baseRect.charge=self

   def fimbriate(self,color):
      # Only plain colors ATM
      # sys.stderr.write("fimbriating with %s\n"%color)
      self.fimbriation=Tincture.lookup[color]

   # Is this too brittle a way to do it?
   def do_fimbriation(self):
      self.maingroup.addElement(SVGdraw.SVGelement('use',
                                                   attributes={"xlink:href":"#%s"%self.clipPath.attributes["id"],
                                                               "stroke":self.fimbriation,
                                                               "stroke-width":self.fimbriation_width,
                                                               "fill":"none",
                                                               "transform":self.clipPathElt.attributes.get("transform")}))

   def process(self): pass

   def addCharge(self,charge):
      charge.parent=self
      self.charges.append(charge)
      # This'll be useful down the road.
      if not charge.maingroup.attributes.has_key("transform"):
         charge.maingroup.attributes["transform"]=""

   def extendCharges(self,charges):
      for elt in charges:
         self.addCharge(elt)

   def invert(self):
      if not hasattr(self,"clipTransforms"):
         self.clipTransforms=""
      self.clipTransforms += " rotate(180)"

   def finalizeSVG(self):
      # we really should only ever do this once.
      # if self.done:
      #   return self.svg
      self.process()
      # Keep the "defs" property around for general use, but fill it
      # automatically if possible.
      if not hasattr(self,"mydefs"):
         self.mydefs=[]
      #if hasattr(self.tincture,"id"):
      #   self.defs.append(self.tincture.elt)
      defs=SVGdraw.defs()
      self.svg.addElement(defs)
      self.defsElt=defs
      if hasattr(self,"clipPath"): 
         # For fimbriation (at least one way to do it), need an id on the actual
         # path, not just the group:
         self.clipPath.attributes["id"]="ClipPath%04d"%Ordinary.id
         Ordinary.id+=1
         if hasattr(self,"clipTransforms"):
            if not self.clipPath.attributes.has_key("transform"):
               self.clipPath.attributes["transform"]=""
            self.clipPath.attributes["transform"] += self.clipTransforms
      self.baseRect=self.tincture.fill(self.baseRect)
      self.maingroup.addElement(self.baseRect)
      if hasattr(self,"fimbriation"):
           self.do_fimbriation()
      if hasattr(self,"charges"):
         for charge in self.charges:
            self.maingroup.addElement(charge.finalizeSVG())
      if hasattr(self,"newmaingroup"):
         self.maingroup=self.newmaingroup
      self.svg.addElement(self.maingroup)
      # Add in all the defs...
      for i in self.mydefs:
         defs.addElement(i)
      # self.done=True
      return self.svg


class Field(Ordinary):
   def __init__(self,tincture="argent"):
      self.svg=SVGdraw.svg(x=0,y=0,width="10cm",height="12.5cm",
                           viewBox=(-Ordinary.FESSPTX-3,
                                    -Ordinary.FESSPTY-3,
                                    Ordinary.WIDTH+6,
                                    Ordinary.HEIGHT+6))
      #        self.svg.attributes["transform"]="scale(1,-1)"
      self.pdata=SVGdraw.pathdata()
      self.pdata.move(-Ordinary.FESSPTX,-Ordinary.FESSPTY)
      self.pdata.vline(Ordinary.HEIGHT/3-Ordinary.FESSPTY)
      self.pdata.bezier(-Ordinary.FESSPTX,
                        Ordinary.HEIGHT*7/8-Ordinary.FESSPTY,
                        0,Ordinary.HEIGHT-Ordinary.FESSPTY,
                        0,Ordinary.HEIGHT-Ordinary.FESSPTY)
      self.pdata.bezier(0,Ordinary.HEIGHT-Ordinary.FESSPTY,
                        Ordinary.FESSPTX,
                        Ordinary.HEIGHT*7/8-Ordinary.FESSPTY,
                        #Ordinary.FESSPTX,-Ordinary.FESSPTY)
                        Ordinary.FESSPTX,Ordinary.HEIGHT/3-Ordinary.FESSPTY)
      self.pdata.vline(-Ordinary.FESSPTY)
      self.pdata.closepath()
      self.charges=[]
      self.setup(tincture)
      self.clipPath=SVGdraw.path(self.pdata)
      self.clipPathElt.addElement(self.clipPath)
      self.svg.addElement(SVGdraw.path(self.pdata,stroke="black",
                                       stroke_width=1,fill="none"))
      Ordinary.defs=[]                  # This is a hack.
      # self.maingroup.addElement(SVGdraw.circle(cx=0,cy=0,r=20,fill="red"))

   # A chief is different.  Adding one depresses the rest of the field.
   def addChief(self, chief):
      """Add a chief, depressing the rest of the field"""
      self.chief=chief                  # Have to handle this later.

   def addBordure(self,bordure):
      self.addCharge(bordure)      # But maybe in the future be clever with
                                        # scaling?
      
   def __repr__(self):
      if not self.maingroup.attributes.has_key("transform"):
         self.maingroup.attributes["transform"]=""
      if hasattr(self,"chief"):
         # Hm.  Somehow I need add something outside the main group
         # AFTER things have happened...
         g=SVGdraw.group()
         g.attributes["clip-path"]=self.maingroup.attributes["clip-path"]
         g.addElement(self.maingroup)
         self.maingroup.attributes["transform"]+=" scale(1,.8) translate(0,15)"
         self.newmaingroup=g
         g2=SVGdraw.group()
         g2.attributes["clip-path"]=self.maingroup.attributes["clip-path"]
         g2.addElement(self.chief.finalizeSVG())
         #self.svg.addElement(g)
      self.finalizeSVG()
      if hasattr(self,"chief"):
         self.svg.addElement(g2)        # ugh.
      drawing=SVGdraw.drawing()
      drawing.setSVG(self.svg)
      for thing in Ordinary.defs:
         self.defsElt.addElement(thing)
      return drawing.toXml()



class Cross(Ordinary):
    def process(self):
        p=partLine()
        p.lineType=self.lineType
        p.move(-10,-Ordinary.HEIGHT)
        p.makeline(-10,-10,align=1)
        p.makeline(-Ordinary.WIDTH,-10)
        p.line(-Ordinary.WIDTH,10)
        p.makeline(-10,10,align=1)
        p.makeline(-10,Ordinary.HEIGHT)
        p.line(10,Ordinary.HEIGHT)
        p.makeline(10,10,align=1)
        p.makeline(Ordinary.WIDTH,10)
        p.line(Ordinary.WIDTH,-10)
        p.makeline(10,-10,align=1)
        p.makeline(10,-Ordinary.HEIGHT)
        p.closepath()
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)


class Fesse(Ordinary):
    def process(self):
        p=partLine(-Ordinary.WIDTH, -20)
        # Fesse is unusual: when "embattled", only the *top* line is
        # crenelated, unless it is blazoned "embattled counter-embattled"
        p.lineType=self.lineType
        p.rect(-Ordinary.WIDTH,-20,Ordinary.WIDTH*3,40)
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)
        
class Saltire(Cross):
    def process(self):
        Cross.process(self)
        self.clipPath.attributes["transform"]="rotate(45)"

class Pall(Ordinary):
    def process(self):
        wd=7*math.cos(math.pi/4)
        p=partLine(-Ordinary.WIDTH-wd, -Ordinary.WIDTH+wd)
        p.makeline(-wd*2,0,align=1)
        p.makeline(-wd*2,Ordinary.HEIGHT)
        p.relhline(4*wd)
        p.makeline(2*wd,0,align=1)
        p.makeline(Ordinary.WIDTH+wd, -Ordinary.WIDTH+wd)
        p.relline(-2*wd,-2*wd)
        p.makeline(0,-wd*2,align=1)
        p.makeline(-Ordinary.WIDTH+wd, -Ordinary.WIDTH-wd)
        p.closepath()
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)

class Pale(Ordinary):
    def process(self):
        p=partLine()
        p.lineType=self.lineType
        p.rect(-10,-Ordinary.HEIGHT,20,Ordinary.HEIGHT*3)
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)

class Bend(Ordinary):
    def __init__(self,*args,**kwargs):
        self.setup(*args,**kwargs)
        self.transform="rotate(-45)"

    def process(self):
        # Hmm.  Not necessarily a good idea, but I think I will NOT use the
        # trick here that's used in Saltire, to isolate the rotation in a
        # group so it isn't inherited.  Things on a bend usually ARE
        # rotated.  May need to reconsider this.
        r=partLine()
        r.lineType=self.lineType
        r.rect(-10,-Ordinary.HEIGHT,20,Ordinary.HEIGHT*3)
        p=SVGdraw.path(r)
        p.attributes["transform"]=self.transform
        self.clipPath=p
        self.clipPathElt.addElement(p)
        # Hrm.  But now the outer clipping path (?) is clipping the end of
        # the bend??

class BendSinister(Bend):
    def __init__(self,*args,**kwargs):
        self.setup(*args,**kwargs)
        self.transform="rotate(45)"

class Chief(Ordinary):
    # Chiefs will also have to be handled specially, as they ordinarily
    # do not overlay things on the field, but push them downward.  Including
    # bordures, right?
    def process(self):
        p=partLine()
        p.lineType=self.lineType
        # sys.stderr.write("Chief's linetype: (%s)\n"%self.lineType)
        # There are days when you want a quarterly chief.  So we'll
        # build the chief around the origin, like a charge, and then
        # move it.
        # Shift fancy-lined chiefs more, so as not to reveal the edge of the
        # shrunken field beneath.
        if p.lineType and p.lineType <> "plain":
           p.rect(-Ordinary.WIDTH, -Ordinary.HEIGHT,
                  Ordinary.WIDTH*3, Ordinary.HEIGHT+13.5)
           self.maingroup.attributes["transform"]="translate(0,%f)"%(-Ordinary.FESSPTY+13.5)
        else:
           p.rect(-Ordinary.WIDTH, -Ordinary.HEIGHT,
                  Ordinary.WIDTH*3, Ordinary.HEIGHT+11)
           self.maingroup.attributes["transform"]="translate(0,%f)"%(-Ordinary.FESSPTY+11)
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)

    def addCharge(self,charge):
       Ordinary.addCharge(self,charge)
       charge.maingroup.attributes["transform"]+=" scale(.7,.66)"

class Bordure(Ordinary):
   # Doing lines of partition is going to be hard with this one.
   def process(self):
      # I don't like copying the field border the hard way like this.
      # Is there a more elegant way?
      pdata=SVGdraw.pathdata()
      pdata.move(-Ordinary.FESSPTX,-Ordinary.FESSPTY)
      pdata.vline(Ordinary.HEIGHT/3-Ordinary.FESSPTY)
      pdata.bezier(-Ordinary.FESSPTX,
                   Ordinary.HEIGHT*7/8-Ordinary.FESSPTY,
                   0,Ordinary.HEIGHT-Ordinary.FESSPTY,
                   0,Ordinary.HEIGHT-Ordinary.FESSPTY)
      pdata.bezier(0,Ordinary.HEIGHT-Ordinary.FESSPTY,
                   Ordinary.FESSPTX,
                   Ordinary.HEIGHT*7/8-Ordinary.FESSPTY,
                   Ordinary.FESSPTX,Ordinary.HEIGHT/3-Ordinary.FESSPTY)
      pdata.vline(-Ordinary.FESSPTY)
      pdata.closepath()
      self.clipPath=SVGdraw.path(pdata)
      self.clipPath.attributes["transform"]=" scale(.75)"
      self.clipPathElt.addElement(SVGdraw.rect(-Ordinary.WIDTH,-Ordinary.HEIGHT,
                                               Ordinary.WIDTH*4,
                                               Ordinary.HEIGHT*4))
      self.clipPathElt.attributes["fill-rule"]="evenodd"
      self.clipPathElt.addElement(self.clipPath)


class Chevron(Ordinary):
    def process(self):
        p=partLine()
        p.lineType=self.lineType
        p.move(-Ordinary.FESSPTX,20)
        p.makeline(0,-20,align=1,shift=-1)
        p.makeline(Ordinary.FESSPTX,20)
        p.relvline(25)
        p.makeline(0,5,align=1)
        p.makeline(-Ordinary.FESSPTX,45,shift=-1)
        p.closepath
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)

class Pile(Ordinary):
    def process(self):
        p=partLine()
        p.lineType=self.lineType
        p.move(-Ordinary.FESSPTX/2,-Ordinary.FESSPTY)
        # The top line is always plain.
        # Need to draw more outside the box in case it is inverted
        p.line(0,-Ordinary.HEIGHT*2)
        p.line(Ordinary.FESSPTX/2,-Ordinary.FESSPTY)
        p.makeline(Ordinary.BASEPT[0],Ordinary.BASEPT[1],align=1)
        p.makeline(-Ordinary.FESSPTX/2,-Ordinary.FESSPTY,align=0)
        p.closepath()
        self.clipPath=SVGdraw.path(p)
        self.clipPathElt.addElement(self.clipPath)

class Base(Ordinary):
   def process(self):
      p=partLine()
      p.lineType=self.lineType
      p.move(-Ordinary.WIDTH,25)
      p.makelinerel(Ordinary.WIDTH*3,0)
      p.vline(Ordinary.HEIGHT)
      p.hline(-Ordinary.WIDTH*3)
      p.closepath()
      self.clipPath=SVGdraw.path(p)
      self.clipPathElt.addElement(self.clipPath)

class Label(Ordinary):
   def __init__(self,points=3,*args,**kwargs):
      self.points=points
      self.setup(*args,**kwargs)

   def process(self):
      p=SVGdraw.pathdata()              # Labels don't get lines of partition.
      p.move(-Ordinary.FESSPTX,-25)
      p.relhline(Ordinary.WIDTH)
      p.relvline(4)
      p.relhline(-2)                    # There's a reason for this.
      for i in range(0,self.points):
         p.relhline((-Ordinary.WIDTH+self.points*4)/(self.points+2.0)-4)
         p.relvline(10)
         p.relhline(-4)
         p.relvline(-10)
      p.hline(-Ordinary.FESSPTX)
      p.closepath()
      self.clipPath=SVGdraw.path(p)
      self.clipPathElt.addElement(self.clipPath)

class ChargeGroup:            # Kind of an invisible ordinary
    def __init__(self,num=None,charge=None):
        self.charges=[]
        self.svg=SVGdraw.svg(x=-Ordinary.FESSPTX,
                             y=-Ordinary.FESSPTY,
                             width=Ordinary.WIDTH,
                             height=Ordinary.HEIGHT,
                             viewBox=(-Ordinary.FESSPTX,
                                      -Ordinary.FESSPTY,
                                      Ordinary.WIDTH,
                                      Ordinary.HEIGHT))
        self.maingroup=SVGdraw.group()
        self.svg.addElement(self.maingroup)
        if num and charge:
           self.numcharges(num,charge)

    def numcharges(self,num,charge):
        for i in range(0,num):
            self.charges.append(copy.deepcopy(charge))

    def finalizeSVG(self):
        # Simplified finalizeSVG for ChargeGroup.
        self.process()
        for charge in self.charges:
            charge.parent=self.parent
            self.maingroup.addElement(charge.finalizeSVG())
        return self.svg

    def process(self):
        self.arrange()

    def arrange(self):
        # This can only work for a relatively small number, say up to 3
        # TODO: check for sibling ordinaries to be "between", or parent
        # ordinaries to be "on", or "in pale/fesse/bend/cross/saltire"
        # And scaling?
        num=len(self.charges)
        if num<1:
            # nothing to do!
            pass
        elif num==1:
            # only for completeness
            obj=self.charges[0]
            obj.shiftto(Ordinary.FESSEPT)
            # Maybe scale it?
            #obj.resize(2)
        else:
            # An even better way to do this: Put a method on the *tincture*
            # objects (or ordinary objects) that returns the appropriate
            # list of lists of positions.  Then things like "two bars" or
            # "three bends" can be subclasses and work the same way and
            # supply information for "between" them; "between" at this
            # point might as well be a synonym for "and".
           
            # The organization should be by background first, then number, I think.
            # First, how to shift things.  I *think* we only need shiftto if
            # we're being countercharged.
            # I think we'll only be using resize and not scale here.
            if isinstance(self.charges[0].tincture,Countercharged):
                def move(obj,location):
                    obj.shiftto(location)
            else:
                def move(obj,location):
                    obj.moveto(location)

            # Wish there were a better way to work this out than trial and error
            # Defaults:
            defaultplacements=[[],[],    # 0 charges, 1 charge ...
                               [(-15,0),(15,0)],            # 2
                               [(-15,-15),(15,-15),(0,10)], # 3
                               # and so on
                               [(-15,-15),(15,-15),(-15,15),(15,15)], 
                               # 5 -> in saltire:
                               [(-20,-20),(20,-20),(0,0),(-20,20),(20,20)]
                               ]
            #scales=[1,1,
            #        .4,.3,.3]
            if isinstance(self.parent.tincture,PerBend) or hasinstance(self.parent.charges,Bend) or isinstance(self.parent.tincture,PerBendSinister) or hasinstance(self.parent.charges,BendSinister):
                # Arrangements for things around a Bend!
                placements=[[],          # not used: num==0
                            [],          # not used: num==1
                            [(25,-25),(-21,21)], # num==2
                            [(5,-33),(-18,18),(30,-15)] # num==3
                            ]
                # BendSinister is just like Bend, with x-coords negated.
                if isinstance(self.parent.tincture,PerBendSinister) or hasinstance(self.parent.charges,BendSinister):
                    for i in range(0,len(placements)):
                        for j in range(0,len(placements[i])):
                            placements[i][j]=(-placements[i][j][0],
                                              placements[i][j][1])
            elif isinstance(self.parent.tincture,PerFesse) or hasinstance(self.parent.charges,Fesse):
                placements=[[],[],
                            [(0,-25),(0,25)],
                            [(-20,-25),(20,-25),(0,25)]
                            ]
            elif isinstance(self.parent.tincture,PerChevron) or hasinstance(self.parent.charges,Chevron):
                placements=[[],[],
                            [(-25,-18),(25,-18)],
                            [(-25,-18),(25,-18),(0,28)]
                            ]
            elif isinstance(self.parent.tincture,PerSaltire):
               placements=[[],[],
                           [(-25,0),(25,0)], # Just guessing that two -> in fesse
                           [(-15,-15),(15,-15),(0,10)], # Gee, I have no idea. Default, perhaps?
                           [(0,-25),(25,0),(0,25),(-25,0)] # Four is the important case IMHO.
                           ]
            # And so on... !!!
            else:
                placements=defaultplacements

            if num>=len(placements):
                # I dunno... Fake it somehow?
                placements=defaultplacements # and try again.
            if num>len(placements):
                raise "Too many objects"
            #scale=scales[num]
            for i in range(0,num):
                move(self.charges[i], placements[num][i])
                #self.charges[i].resize(scale)
                    

class Charge(Ordinary):
    def moveto(self,*args):
        # Remember, args[0] is a tuple!
        if not self.svg.attributes.has_key("transform"):
            self.svg.attributes["transform"]=""
        self.svg.attributes["transform"]+=" translate(%.4f,%.4f)" % args[0]

    # Lousy name, but we need a *different* kind of moving, to slide
    # the outline but not the innards/tincture.
    def shiftto(self,*args):
        if not self.clipPathElt.attributes.has_key("transform"):
            self.clipPathElt.attributes["transform"]=""
        self.clipPathElt.attributes["transform"]+=" translate(%.4f,%.4f)"%args[0]

    def scale(self,x,y=None):
       if not y:                        # I can't scale by 0 anyway.
          y=x
       if not self.svg.attributes.has_key("transform"):
          self.svg.attributes["transform"]=""
       self.svg.attributes["transform"] += " scale(%.2f,%.2f)"%(x,y)

    # Same as shiftto: changes the size of the outline only. 
    def resize(self,x,y=None):
        if not y:
            y=x
        if not self.clipPathElt.attributes.has_key("transform"):
            self.clipPathElt.attributes["transform"]=""
        self.clipPathElt.attributes["transform"] += " scale(%.2f,%.2f)"%(x,y)
              
    def dexterchief(self):
        self.moveto(Ordinary.DEXCHIEF)

    def sinisterchief(self):
        self.moveto(Ordinary.SINCHIEF)

    def chief(self):
        self.moveto(Ordinary.CHIEFPT)

    def addCharge(self,charge):
        Ordinary.addCharge(self,charge)
        charge.maingroup.attributes["transform"]+=" scale(.4)"

class Roundel(Charge):
   def process(self):
      self.clipPath=SVGdraw.circle(cx=0,cy=0,r=12) # make it 36
      self.clipPathElt.addElement(self.clipPath)

class Lozenge(Charge):
   def process(self):
      p=SVGdraw.pathdata()
      p.move(0,-15)
      p.line(10,0)
      p.line(0,15)
      p.line(-10,0)
      p.closepath()
      self.clipPath=SVGdraw.path(p)
      self.clipPathElt.addElement(self.clipPath)

class Billet(Charge):
    def process(self):
        self.clipPath=SVGdraw.rect(-10,-15,20,30)
        self.clipPathElt.addElement(self.clipPath)

class Annulet(Charge):
   def process(self):
      # self.clipPath is used for fimbriation, which at 4 is
      # so wide it overwhelms the annulet.  Woops.
      self.fimbriation_width=2
      self.clipPath=SVGdraw.group()
      self.clipPath.attributes["id"]="ClipPath%04d"%Ordinary.id
      Ordinary.id+=1
      self.clipPath.addElement(SVGdraw.circle(cx=0,cy=0,r=12))
      # We want to draw the second path counter-clockwise, so that it will
      # turn into a hole.
      # Apparently just drawing it is enough, just be sure to set
      # the clip-rule to evenodd.
      self.clipPath.addElement(SVGdraw.circle(cx=0,cy=0,r=8))
      self.clipPathElt.addElement(self.clipPath)
      self.clipPathElt.attributes["clip-rule"]="evenodd"

class ExtCharge(Charge):
    # Path, fimbriation-width, and default tincture (for "proper")
    paths={
        "fleur":("data/Fleur.svg#fleur",4,None),
        "formy":("data/Cross-Pattee-Heraldry.svg#formy",30,None),
        "pommee":("data/Cross-Pattee-Heraldry.svg#pommee",300,None),
        "bottony":("data/Cross-Pattee-Heraldry.svg#bottony",20,None),
        "goute":("data/Cross-Pattee-Heraldry.svg#goute",1,None),
        "crosscrosslet":("data/Cross-Crosslet-Heraldry.svg#cross-crosslet",2,None),
        "mullet":("data/Cross-Pattee-Heraldry.svg#mullet",2,None)
        }
    
    def __init__(self,name,*args,**kwargs):
        self.setup(*args)
        try:
            info=ExtCharge.paths[name]
            (self.path,self.fimbriation_width,self.tincture)=info
            if kwargs.get("extension"): # Not sure this is so great.
               self.path+=str(kwargs["extension"][0])
        except KeyError:
            self.path=name              # Punt.
            

    def process(self):
        self.clipPathElt.addElement(SVGdraw.use(self.path))

    def do_fimbriation(self):
       self.maingroup.addElement(SVGdraw.SVGelement('use',
                                                    attributes={"xlink:href":"%s"%self.path,
                                                                "stroke":self.fimbriation,
                                                                "stroke-width":self.fimbriation_width,
                                                                "fill":"none",
                                                                "transform":self.clipPathElt.attributes.get("transform")}))


def hasinstance(lst,cls):
    for i in lst:
        if isinstance(i,cls):
            return True
    return False

# Other ideas...:

# Presumably each charge (esp. each Ordinary) will be its own <g> element,
# thus allowing a remapping of coordinates.  Obv. we don't want complete
# rescaling, but it's a step.

# I like the idea of a function parent-charges can call on their
# descendents, "suggesting" a transformation to apply, which the charges
# may or may not choose to listen to, or by how much.  By transforming
# their paths only, we can avoid transforming furs used to fill them in.

# A "between" function, which returns a list of points in the
# *surroundings* of this Ordinary suitable for putting n other charges.
# e.g. "a bend between two annulets sable" vs. three annulets vs. a chevron
# between three, etc etc etc.  This is something that relates to a charge's
# *siblings* on the field.

# Old YAPPS parser:
# import parse
# New YACC parser:
import plyyacc

class Blazon:
    """A blazon is a heraldic definition. We would like to be as liberal
    as possible in what we accept."""
    def __init__(self, blazon):
        # Our parser is somewhat finicky, so we want to convert the raw,
        # user-provided text into something it can handle.
        self.blazon = self.Normalize(blazon)
    def Normalize(self, blazon):
        return re.sub("[^a-z0-9 ]+"," ",blazon.lower())
    def GetBlazon(self):
        return self.blazon
    def GetShield(self):
        # Old YAPPS parser:
        # return parse.parse('blazon', self.GetBlazon())
        # New YACC parser:
        return plyyacc.yacc.parse(self.GetBlazon())

if __name__=="__main__":
    cmdlineinput = " ".join(sys.argv[1:])
    blazon = Blazon(cmdlineinput)
    # Old YAPPS parser:
    # return parse.parse('blazon', self.GetBlazon())
    # New YACC parser:
    print plyyacc.yacc.parse(self.GetBlazon())
