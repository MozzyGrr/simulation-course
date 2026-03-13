import pygame
import numpy as np
import random

pygame.init()

WIDTH = 1200
HEIGHT = 800
SIM_SIZE = 800
GRID_SIZE = 180
CELL = SIM_SIZE / GRID_SIZE
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wildfire Simulation")

clock = pygame.time.Clock()

empty = 0
wood = 1
fire = 2
ash = 3
water = 4

COLORS = {
    empty:(15,18,28),
    wood:(40,200,120),
    fire:(255,80,20),
    ash:(120,120,120),
    water:(60,140,255)
}

spread = 0.35
humidity = 0.2
growth = 0.002
lightning = 0.00005
fps = 60

wind = (0,0)
paused = False
ash_decay = 0.02
burn_duration = 3

grid = np.random.choice([empty,wood],(GRID_SIZE,GRID_SIZE),p=[0.4,0.6])
burn_time = np.zeros((GRID_SIZE,GRID_SIZE))

font = pygame.font.SysFont("arial",16)
big_font = pygame.font.SysFont("arial",26)

class Slider:
    def __init__(self,x,y,h,minv,maxv,val,name):
        self.x=x
        self.y=y
        self.h=h
        self.min=minv
        self.max=maxv
        self.val=val
        self.name=name
        self.drag=False

    def draw(self):
        pygame.draw.line(screen,(80,80,90),(self.x,self.y),(self.x,self.y+self.h),4)
        pos=(self.val-self.min)/(self.max-self.min)
        ky=self.y+self.h-(pos*self.h)
        pygame.draw.circle(screen,(0,255,180),(int(self.x),int(ky)),6)
        valtxt=font.render(f"{self.val:.4f}",True,(180,255,200))
        screen.blit(valtxt,(self.x-valtxt.get_width()//2,self.y-25))
        words = self.name.split()
        for i,word in enumerate(words):
            txt=font.render(word,True,(220,220,220))
            screen.blit(txt,(self.x-txt.get_width()//2,self.y+self.h+8 + i*18))

    def update(self,event):
        if event.type==pygame.MOUSEBUTTONDOWN:
            mx,my=event.pos
            if abs(mx-self.x)<15 and self.y<my<self.y+self.h:
                self.drag=True
        if event.type==pygame.MOUSEBUTTONUP:
            self.drag=False
        if event.type==pygame.MOUSEMOTION and self.drag:
            my=event.pos[1]
            my=max(self.y,min(self.y+self.h,my))
            ratio=(self.y+self.h-my)/self.h
            self.val=self.min+ratio*(self.max-self.min)

class Button:
    def __init__(self,x,y,w,h,label):
        self.rect=pygame.Rect(x,y,w,h)
        self.label=label
    def draw(self):
        pygame.draw.rect(screen,(50,55,70),self.rect,border_radius=6)
        txt=font.render(self.label,True,(255,255,255))
        screen.blit(txt,
                    (self.rect.centerx-txt.get_width()//2,
                     self.rect.centery-txt.get_height()//2))
    def click(self,event):
        return event.type==pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)

sliders=[
Slider(870,200,250,0.01,1.0,spread,"Fire Spread Chance"),
Slider(930,200,250,0.0,0.9,humidity,"Air Humidity"),
Slider(990,200,250,0.0,0.01,growth,"Tree Growth Rate"),
Slider(1050,200,250,0.0,0.001,lightning,"Lightning Strike Chance"),
Slider(1110,200,250,10,120,fps,"Simulation Speed")
]

pause_btn=Button(860,60,120,40,"pause")
reset_btn=Button(1000,60,120,40,"reset")
clear_btn=Button(860,110,260,40,"clear map")
ignite_btn=Button(860,620,120,40,"ignite tree")
water_btn=Button(1000,620,120,40,"add water")

wind_u=Button(960,680,40,40,"↑")
wind_l=Button(910,720,40,40,"←")
wind_s=Button(960,720,40,40,"•")
wind_r=Button(1010,720,40,40,"→")
wind_d=Button(960,760,40,40,"↓")

buttons=[pause_btn,reset_btn,clear_btn,ignite_btn,water_btn,
         wind_l,wind_r,wind_u,wind_d,wind_s]

def update_sim():
    global grid,burn_time
    new_grid=grid.copy()
    new_burn=burn_time.copy()
    wind_strength = 0.8

    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            state=grid[x,y]

            if state==fire:
                new_burn[x,y]+=1
                if new_burn[x,y]>=burn_duration:
                    new_grid[x,y]=ash
                    new_burn[x,y]=0

            elif state==ash:
                if random.random()<ash_decay:
                    new_grid[x,y]=empty

            elif state==empty:
                if random.random()<growth:
                    new_grid[x,y]=wood

            elif state==wood:

                if random.random()<lightning:
                    new_grid[x,y]=fire
                    new_burn[x,y]=1
                    continue

                catch=False

                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:

                        if dx==0 and dy==0:
                            continue

                        nx=x+dx
                        ny=y+dy

                        if 0<=nx<GRID_SIZE and 0<=ny<GRID_SIZE:

                            if grid[nx,ny]==fire:

                                prob=spread

                                if abs(dx)+abs(dy)==2:
                                    prob*=0.7

                                # -------- ВЛИЯНИЕ ВОДЫ --------
                                water_count=0

                                for wx in [-1,0,1]:
                                    for wy in [-1,0,1]:

                                        if wx==0 and wy==0:
                                            continue

                                        cx=x+wx
                                        cy=y+wy

                                        if 0<=cx<GRID_SIZE and 0<=cy<GRID_SIZE:
                                            if grid[cx,cy]==water:
                                                water_count+=1

                                if water_count>0:
                                    prob *= (0.6 ** water_count)
                                # --------------------------------

                                dir_x = x - nx
                                dir_y = y - ny

                                if wind != (0,0):

                                    wind_len = (wind[0]**2 + wind[1]**2)**0.5
                                    wind_x = wind[0]/wind_len
                                    wind_y = wind[1]/wind_len

                                    dir_len = (dir_x**2 + dir_y**2)**0.5
                                    dir_x /= dir_len
                                    dir_y /= dir_len

                                    dot = wind_x*dir_x + wind_y*dir_y

                                    prob += dot*wind_strength

                                prob *= 1 - humidity

                                if random.random()<prob:
                                    catch=True
                                    break

                    if catch:
                        break

                if catch:
                    new_grid[x,y]=fire
                    new_burn[x,y]=1

    grid=new_grid
    burn_time=new_burn

def draw_world():
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect=pygame.Rect(int(x*CELL),int(y*CELL),int(CELL+1),int(CELL+1))
            color=COLORS[grid[x,y]]
            if grid[x,y]==fire:
                color=(255,random.randint(60,120),20)
            pygame.draw.rect(screen,color,rect)

def draw_gui():
    pygame.draw.rect(screen,(22,25,35),(800,0,400,HEIGHT))
    title=big_font.render("WILDFIRE CONTROL",True,(0,255,180))
    screen.blit(title,(870,20))
    for s in sliders: s.draw()
    for b in buttons: b.draw()

running=True
while running:

    clock.tick(int(fps))
    screen.fill((10,12,18))

    for event in pygame.event.get():

        if event.type==pygame.QUIT:
            running=False

        for s in sliders:
            s.update(event)

        if pause_btn.click(event):
            paused=not paused

        if reset_btn.click(event):
            grid=np.random.choice([empty,wood],(GRID_SIZE,GRID_SIZE),p=[0.4,0.6])

        if clear_btn.click(event):
            grid=np.zeros((GRID_SIZE,GRID_SIZE))

        if ignite_btn.click(event):
            trees = np.argwhere(grid==wood)
            if len(trees)>0:
                x,y = random.choice(trees)
                grid[x,y]=fire
                burn_time[x,y]=1

        if water_btn.click(event):
            empties = np.argwhere(grid==empty)
            if len(empties)>0:
                x,y = random.choice(empties)
                grid[x,y]=water

        if wind_l.click(event): wind=(-1,0)
        if wind_r.click(event): wind=(1,0)
        if wind_u.click(event): wind=(0,-1)
        if wind_d.click(event): wind=(0,1)
        if wind_s.click(event): wind=(0,0)

    spread=sliders[0].val
    humidity=sliders[1].val
    growth=sliders[2].val
    lightning=sliders[3].val
    fps=sliders[4].val

    if not paused:
        update_sim()

    draw_world()
    draw_gui()

    pygame.display.flip()

pygame.quit()
