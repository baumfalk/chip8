import pygame, sys
import pygame.locals
from pygame import gfxdraw

from disassembler import Dissassembler

pygame.init()
BLACK = (0,0,0)
WHITE = (255,255,255)
WIDTH = 64*10
HEIGHT = 32*10
windowSurface = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)

windowSurface.fill(BLACK)


def drawScreen(surface, screenbits):
    y = 0
    for line in screenbits:
        x=0
        for pixel in line:
            if pixel:
                pygame.draw.rect(surface, WHITE, (x*10, y*10, 10, 10), 0)
            x += 1
        y += 1

    pygame.display.flip()


d = Dissassembler('roms/test.dms', debug=True)

d.parseBytes(d.memory)
while True:
    d.runNextStep()
    drawScreen(windowSurface, d.screen)
    #pygame.draw.rect(windowSurface, WHITE, (0, 0, 10, 10), 0)

    for event in pygame.event.get():
        print(event)
        # if event.key == pygame.K_p:
        #      #Do what you want to here
        #      pass
        if event.type == pygame.locals.QUIT:
              pygame.quit()
              sys.exit()