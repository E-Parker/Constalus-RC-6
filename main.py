#This program was writen by Ethan Parker on 11.12.2021
#Constalus Engine version 3.5.3

#if pygame.gfxdraw no longer works, please replace any instance of render type 4 with 0.
#gfxdraw is only used to achive a fake transparency effect and isnt nessesary for the game to run.
import math, pygame, pygame.gfxdraw, os, random, copy
from pygame.locals import *
from func import QuickSort as sort
from func import Mesh, MeshCollider, Atlas, Plane, display_text, get_normal, x_rot, y_rot, z_rot, xyz_move, GenClip, clipTrigon, pointOnScreen, Trigger, COLOUR

ISFOURBYTHREE = False            # Change this if useing a 4:3 monitor for fake 16:9 mode.
SENSITIVITY = 2.5               # Mouse sensitivity
NEARCLIP, FARCLIP = 0.2, 64     # near and far cliping plane

# Setting up window:
if ISFOURBYTHREE:
    WIDTH, HEIGHT,  = 1280,1024
else:
    WIDTH, HEIGHT = 1280,720

RWIDTH = WIDTH
RHEIGHT = int(RWIDTH * (9/ 16))  # Scale render height to

CENTERX, CENTERY = WIDTH//2, HEIGHT//2

def setResolution(width,height,rwidth,rheight,res,fov):
    """ This function initializes the main window surface."""
    s_res = (width, height)                     # Bases resolution
    r_res = (rwidth//res, rheight//res)         # Render resolution
    centr = (r_res[0]//2, r_res[1]//2,)         # Center of the Render surface
    scale = (r_res[0]//math.sqrt((fov/10)))     # Scale variable used when projecting points from world space to screenspace
    return s_res, r_res, centr, scale, fov, res

def terminate():
    """ This function terminates the game. """
    pygame.quit()
    os._exit(1)

def randomPosition(positions,numpos):
    """ This function randomly selects 'numpos' number of positions from 'position'.
        This function is used to get sudo-random positions for objects."""
    newpos = []
    indecies = [x for x in range(len(positions))]
    
    for i in range(numpos):
        position = (random.randrange(len(indecies)))
        newpos.append(positions[indecies[position]])
        del indecies[position]

    return newpos

class Camera():
    def __init__(self, startpos, startrot, movespeed, fov, nearclip, farclip):

        # Variables
        # self.move_left         -   Bool for if moving left
        # self.move_right        -   Bool for if moving right
        # self.move_forward      -   Bool for if moving forward
        # self.move_back         -   Bool for if moving backward
        # self.jump              -   Bool for if attempting to jump
        # self.interact          -   Bool for if attempting to interact
        
        # self.move_vect         -   vector that stores direction the camera is moving
        # self.camera_vect       -   vector that stores the direction the camera is looking in

        # self.near              -   near clip
        # self.far               -   far clip
        # self.clipMesh          -   mesh used to generate clipping planes
        # self.clipPlanes        -   list of planes to clip polygons against

        # self.height            -   Height of the player
        # self.radius            -   radius of sphere collider
        # self.airborne          -   Dual purpose. used to store if the player is in the air (not colliding) and for how long.
        # self.jumpheight        -   Maximum height of the player's jump
        # self.jumpboost         -   Temporary speed boost for clearing large gaps
        # self.currentjumpheight -   used to keep track of the jump height offset

        # self.items             -   list of items in the players "inventory". Items are stored with as a string.
        # self.alive             -   keeps track of if the player has died or not.

        # Movement:
        self.move = False
        self.move_left = False
        self.move_right = False
        self.move_forward = False
        self.move_back = False
        self.jump = False
        self.interact = False
        self.pos = startpos
        self.rot = startrot
        self.movespeed = movespeed
        self.maxspeed = movespeed
        self.lookspeed = SENSITIVITY / 1000
        self.height = 0.25
        self.airborne = 0
        self.jumpheight = 1.3
        self.jumpboost = 1.3
        self.currentjumpheight = None

        # Other information
        self.items = []
        self.collisions = 0
        self.reset = False
        self.alive = True
        self.radius = 0.25

        # Vectors
        self.move_vect   = pygame.math.Vector3(0,0,1)
        self.camera_vect = pygame.math.Vector3(0,0,1)
        self.reference   = pygame.math.Vector3(0,0,1)

        # This is used for calculating if a point can be seen by the camera.
        self.near = nearclip
        self.far = farclip
        
        # Set up the clipping planes
        self.clipMesh = GenClip(fov,self.near,self.far)
        self.clipPlanes = ()
        for face in self.clipMesh:
            self.clipPlanes = self.clipPlanes + (Plane(face),)  

        # Rotate vectors to align with starting orientation:
        self.move_vect.update(self.move_vect.rotate_x(startrot[0]))
        self.move_vect.update(self.move_vect.rotate_y(startrot[1]))
        self.move_vect.update(self.move_vect.rotate_z(startrot[2]))
    
        self.camera_vect.update(self.camera_vect.rotate_x(startrot[0]))
        self.camera_vect.update(self.camera_vect.rotate_y(startrot[1]))
        self.camera_vect.update(self.camera_vect.rotate_z(startrot[2]))

    def getPos(self):
        """ retunrs the current position of the camera. """
        return self.pos

    def getMove(self):
        """ returns the movement vector. """
        return self.move_vect

    def getLook(self):
        """ returns the direction as a vector. """
        return self.camera_vect

    def update(self, Δtime, colliders, musicPlaying, music):
        """ This function handles all inputs and updates assosiated vectors. """
        
        self.interact = False
        
        # handle inputs
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                os._exit(1)
            elif event.type == KEYDOWN:              
                # update the direction of the player 
                if event.key == K_SPACE:
                    if self.airborne > -0.2:
                        self.jump = True
                if event.key == ord('e'):
                    self.interact = True
                if event.key == ord('a'):
                    self.move_left = True
                    self.move_right = False
                    self.move = True
                if event.key == ord('d'):
                     self.move_right = True
                     self.move_left = False
                     self.move = True
                if event.key == ord('w'):
                    self.move_forward = True
                    self.move_back = False
                    self.move = True
                if event.key == ord('s'):
                    self.move_back = True
                    self.move_forward = False
                    self.move = True
            elif event.type == KEYUP:
                if event.key == K_ESCAPE:
                    terminate()
                # the player has stopped moving
                if event.key == ord('g'):
                    self.reset = True
                if event.key == ord('a'):
                    self.move_left = False
                if event.key == ord('d'):
                    self.move_right = False
                if event.key == ord('w'):
                    self.move_forward = False
                if event.key == ord('s'):
                    self.move_back = False
                if event.key == ord('e'):
                    self.interact = False
                if event.key == ord('m'):
                    musicPlaying = not musicPlaying
                    if musicPlaying:
                        for i in range(len(music)):
                            music[i].stop()
                    else:
                        for i in range(len(music)):
                            music[i].play(-1,0,0)
                    
        #if none of the directional keys are being pressed, the player isnt moveing.
        if not self.move_left and not self.move_right and not self.move_forward and not self.move_back:
            self.move = False
        
        vect = pygame.math.Vector3(0,0,0)
        self.movespeed = self.maxspeed * Δtime #scale movespeed by the amount of time between now and the last frame:
        if self.movespeed > 1:
            self.movespeed = 1
        
        # change direction of vect based on directional input from the player
        if self.move_forward:
            vect += self.move_vect
        if self.move_back:
            vect += self.move_vect.rotate_y(180)
        if self.move_left:
            vect += self.move_vect.rotate_y(90)
        if self.move_right:
            vect += self.move_vect.rotate_y(270)

        if self.jump:
            if self.currentjumpheight is None:
                self.currentjumpheight = self.jumpheight
            self.movespeed = self.movespeed * self.jumpboost
            if self.currentjumpheight > 0:
                self.currentjumpheight -= 0.01
                vect += pygame.math.Vector3(0, self.currentjumpheight, 0)
        
        # Update player position
        vect -= pygame.math.Vector3(0, 0.5 - self.airborne, 0) # Subtract gravity
        vect = vect * self.movespeed                         # scale to movespeed
        self.pos += vect
        
        # Check collisions:
        self.collisions = 0
        for collider in colliders:
            if collider.enabled:
                collision = collider.sphereCollideCheck(self.pos, self.radius)
                self.pos += collision[0]
                self.collisions += collision[1]

        # if colliding, reset jump and airborne time
        if self.collisions != 0:
            self.airborne = 0
            self.jump = False
            self.currentjumpheight = None
        else:
            self.airborne -= (0.05 * Δtime)

        # HANDLE ROTATION:

        # Get mouse position
        rotation = pygame.mouse.get_pos()
        roty, rotx = (rotation[0] - CENTERX) * self.lookspeed, (rotation[1] - CENTERY) * self.lookspeed
        
        # Update rotation
        self.rot[0] += rotx
        self.rot[1] += roty

        # Clamp rotation to 90 degrees up or down, this prevents camera from over rotating:
        if self.rot[0] > 1.4: self.rot[0] = 1.4
        if self.rot[0] < -1.4: self.rot[0] = -1.4

        # Rotate camera vector
        self.camera_vect.rotate_x_rad(rotx)
        self.camera_vect.rotate_y_rad(roty)

        # Rotate movement vector    
        self.move_vect = pygame.math.Vector3.rotate_y_rad(self.reference,-self.rot[1])

        # Reset mouse possition for next render
        pygame.mouse.set_pos(CENTERX, CENTERY)

        return musicPlaying
        
class Game():
    """ Game class for 3D render engine.
        Expects display settings and a list of scene data."""
    def __init__(self, windowSurface, Font, disp, scenes, music):

        # Variables:
        # self.disp          -   stores various display settings such as screen resolution, render resolution, center of screen, scale and fov.
        # self.screen        -   surface the game renders to. Used for rendering at a lower resolution than the monitor. I couldve used pygame.SCALED flag but this method lets me do fake 16:9 on 4:3 monitor.
        # self.font          -   Stores the font used in Display Text function in "func.py"

        # self.projected     -   Tuple of the points after projecting them to screenspace. Stored as a tuple because the faster read times really help when there's over 1000 elements. besides, Im not doing any writes to that area of memorry after its been computed
        # self.depth         -   List of the average Z value for a projected face. Used to sort by depth relative to camera.

        # self.uninitScenes  -   stores unmodified copys of all the levels to allow the game to be restarted.
        # self.scenes        -   stores all of the level data for quick switching between levels.
        # self.scene         -   list of items in the current scene for run-time manipulation.
        # self.meshs         -   list of meshes in self.scene. All meshes get displayed to the screen.
        # self.colliders     -   list of mesh colliders. used to check collision against the camera object.
        # self.textures      -   When loading a scene, the texture atlas' and other assiosiated data is stored in this tuple.

        # self.total         -   Used for debuging. also, very handy when trying to keep polygon count down.
        # self.camera        -   behaves like a "Player" object, stores and updates some variables related to rendering the secene.
        
        # self.Δtime         -   Time between each frame, or in other words, the time it took to render the last frame. used to normalize movement and animation to the framerate of the game.
        # self.tick          -   Used to store the current "tick". similar to the system used in Minecraft, where game logic updates on a per tick basis instead of per frame.
        # self.cycle         -   Stores the amount of tick cylces that have occured. to get the current frame, self.tick + (self.cycle * self.tpc)
        # self.tpc           -   ticks per cycle. used to help mitigate short int overflow error
        
        # Display Settings:
        self.scenes = scenes
        self.disp = disp
        self.rescale = (self.disp[1][0] * self.disp[5],self.disp[1][1] * self.disp[5])
        self.scalepos = (0,((HEIGHT - RHEIGHT) // 2))
        self.font = Font

        # Frame Δ:
        self.Δtime = 1
        self.tick = 0
        self.cycle = 0
        self.tpc = 512
        
        # Define Render Surface:
        self.screen = pygame.Surface(disp[1]).convert_alpha()

        # Set up hud elements 
        self.onscreenText = []
        self.onscreenTime = []
        self.reticle = pygame.image.load("assets/textures/reticle.png").convert_alpha()
        self.transparency = pygame.Surface((8,8)).convert_alpha()
        self.transparency.set_alpha(128)

        # Load Menu Images:       
        self.menuImage = pygame.image.load("assets/textures/main.png").convert()
        self.menuImageBlank = pygame.image.load("assets/textures/main_clear.png").convert()
        self.loadingTransition = pygame.image.load("assets/textures/loading.png").convert()

        self.menuImage = pygame.transform.scale(self.menuImage,disp[1])
        self.menuImageBlank = pygame.transform.scale(self.menuImageBlank,disp[1])
        self.loadingTransition = pygame.transform.scale(self.loadingTransition,disp[1])

        # Load Music:
        self.music = []
        self.playvol = []
        self.max_volume = 1
        self.musicplaying = True
        for i in range(len(music)):
            self.music.append(pygame.mixer.Sound(music[i][0]))
            self.music[i].set_volume(0)

        for i in range(len(music)):
             self.music[i].play(-1,0,0)

        # Draw Main Menu:
        self.main_menu(windowSurface, 0)

        # Draw loading transition:
        self.drawTransition((255, 255, 255), self.loadingTransition, windowSurface)
        self.screen.blit(self.loadingTransition, (0, 0))
        
        # initialize Rendering:
        self.camera = Camera(pygame.math.Vector3(0, 1, 0), [0, -math.pi/2, 0], 0.03, self.disp[4], NEARCLIP, FARCLIP)
        self.projected = ()
        self.depth = []
        
        # Generate Scene:
        self.level = 0
        self.scenes = []
        self.textures = ()
        total = 0
        
        for x in range(len(scenes)):
            scenedata = scenes[x]
            meshes = ()
            colliders = ()
            triggers = ()
            for i in range(len(scenedata)):
                # Get mesh
                if len(scenedata[i]) >= 9:
                   newobject = Mesh(scenedata[i][1],scenedata[i][2],scenedata[i][3],scenedata[i][4],scenedata[i][5],scenedata[i][6],scenedata[i][7],scenedata[i][8],scenedata[i][9])
                
                # Append to scene
                if scenedata[i][0] == 'MDL':
                    meshes = meshes + (newobject,)

                elif scenedata[i][0] == 'COL':
                    colliders = colliders + (MeshCollider(scenedata[i][1],scenedata[i][2],scenedata[i][3],scenedata[i][4],self.camera.radius/2,scenedata[i][6]),)

                elif scenedata[i][0] == 'TEX':
                    self.textures = self.textures + (Atlas(scenedata[i][1]),)

                elif scenedata[i][0] == 'TRG':
                    triggers = triggers + (Trigger(scenedata[i][1],scenedata[i][2],scenedata[i][3],scenedata[i][4],(self.camera.radius/2),scenedata[i][5],scenedata[i][6],scenedata[i][7]),)
            
            # Append to self.scenes, which will get worked on by the game, and to self.uninitScenes which is used to overwrite self.scenes when the game restarts.
            self.scenes.append((meshes,colliders,triggers))
            
            # Display level loading message
            display_text(self.screen,x + 16,"Level "+str(x + 1)+" loaded successfully.",self.font,COLOUR[5],"c")
            self.drawScreen(windowSurface)

        self.scene = self.scenes[self.level]
        self.uninitScenes = copy.deepcopy(self.scenes)
        self.gamestate = 2

    # RELATED TO DISPLAYING SCREENS
    
    def drawTransition(self,colour,image,windowSurface):
        size = self.screen.get_size()
        screen = pygame.Surface(size).convert_alpha()
        screen.set_alpha(16)
        
        if image is not None:
            image = pygame.transform.scale(image,size)
        else:
            image = pygame.Surface(size)
            image.fill(colour)
        screen.blit(image,(0,0))
        self.screen.blit(screen,(0,0))
        
        for i in range((32)):
            self.screen.blit(screen,(0,0))
            self.drawScreen(windowSurface)
            pygame.display.flip()
            pygame.time.delay(30)

    def main_menu(self,windowSurface,start):
        """ This function displays the main menu for the game. """

        screenindex = start

        while screenindex != -1:

            while screenindex == 0:

                self.screen.blit(self.menuImage,(0,0))
                display_text(self.screen,16,"Press SPACE to start.    ",self.font,COLOUR[5],"c")
                display_text(self.screen,18,"Press H for instructions.",self.font,COLOUR[5],"c")
                display_text(self.screen,20,"Press ESCAPE to exit.    ",self.font,COLOUR[5],"c")
                
                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            terminate()
                        elif event.key == K_SPACE:
                            frames = 0
                            screenindex = -1
                        elif event.key == ord('h'):
                            frames = 0
                            screenindex = 1
            # Help Screen
            while screenindex == 1:
                self.screen.blit(self.menuImageBlank,(0,0))
                
                display_text(self.screen,3,"HELP SCREEN PAGE 1 of 4:",self.font,COLOUR[5],"c")
                display_text(self.screen,5,"Dr. Gerritt Moony spent his entire career studying Minoan civilization",self.font,COLOUR[5],"c")
                display_text(self.screen,6,"but had little to show for his efforts. According to legend, when ",self.font,COLOUR[5],"c")
                display_text(self.screen,7,"Minos became ruler of Crete his father, Zeus, gifted him an enormous",self.font,COLOUR[5],"c")
                display_text(self.screen,8,"ruby. The magnificent gem was placed at the pinnacle of the temple of",self.font,COLOUR[5],"c")
                display_text(self.screen,9,"the Sun Goddess on the tiny island of Constalus. There, it served as",self.font,COLOUR[5],"c")
                display_text(self.screen,10,"a beacon to guide Minoan ships on the Aegean Sea. Sadly, the Minoan",self.font,COLOUR[5],"c")
                display_text(self.screen,11,"language was lost to the ages, and with it, the location of the",self.font,COLOUR[5],"c")
                display_text(self.screen,12,"fabled island. If only Dr. Moony could find Zeus’",self.font,COLOUR[5],"c")
                display_text(self.screen,13,"gift to Minos, he’d earn his place in the history books.",self.font,COLOUR[5],"c")
                display_text(self.screen,15,"At long last, Dr. Moony learned to decipher the ancient Minoan scripts ",self.font,COLOUR[5],"c")
                display_text(self.screen,16,"and set off to transcribe the secrets hidden in the tablets at the ",self.font,COLOUR[5],"c")
                display_text(self.screen,17,"Palace of Knossos.",self.font,COLOUR[5],"c")

                display_text(self.screen,23,"Press H to continue to next page or press ESCAPE to return to previous menu.",self.font,COLOUR[5],"c")

                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            frames = 0
                            screenindex = 0
                        elif event.key == ord('h'):
                            frames = 0
                            screenindex = 2

            while screenindex == 2:
                self.screen.blit(self.menuImageBlank,(0,0))
                
                display_text(self.screen,3,"HELP SCREEN PAGE 2 of 4:",self.font,COLOUR[5],"c")
                display_text(self.screen,8,"TABLET ONE TRANSLATION:",self.font,COLOUR[5],"c")
                display_text(self.screen,9,"The window to our Godly Palace rests upon the isle of Constalus.",self.font,COLOUR[5],"c")
                display_text(self.screen,10,"Under Zeus’ watchful eye, ships find safety in the sky. To make ",self.font,COLOUR[5],"c")
                display_text(self.screen,11,"the Eye of Zeus your compass, fix his gaze upon Olympus.",self.font,COLOUR[5],"c")
                display_text(self.screen,13,"TABLET TWO TRANSLATION:",self.font,COLOUR[5],"c")
                display_text(self.screen,14,"Twenty leagues sail north of Knossos, in alignment with Mount",self.font,COLOUR[5],"c")
                display_text(self.screen,15,"Juktas.  Approach the island from the left, or else prepare to",self.font,COLOUR[5],"c")
                display_text(self.screen,16,"meet with death.",self.font,COLOUR[5],"c")
                display_text(self.screen,23,"Press H to continue to next page or press ESCAPE to return to previous menu.",self.font,COLOUR[5],"c")

                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            frames = 0
                            screenindex = 1
                        elif event.key == ord('h'):
                            frames = 0
                            screenindex = 3

            while screenindex == 3:
                self.screen.blit(self.menuImageBlank,(0,0))
                
                display_text(self.screen,3,"HELP SCREEN PAGE 3 of 4:",self.font,COLOUR[5],"c")
                display_text(self.screen,5,"Armed with directions and newfound confidence, Dr. Moony charters a ",self.font,COLOUR[5],"c")
                display_text(self.screen,6,"boat from Heraklion and sets sail for Constalus. He hasn’t been this ",self.font,COLOUR[5],"c")
                display_text(self.screen,7,"excited in years, but there’s a nagging feeling plaguing his mind.",self.font,COLOUR[5],"c")
                display_text(self.screen,8,"It’s a foggy memory from his early studies – an archaic Sicilian",self.font,COLOUR[5],"c")
                display_text(self.screen,9,"tapestry depicting a small island, a gigantic jewel, Daedalus’",self.font,COLOUR[5],"c")
                display_text(self.screen,10,"treachery, and a monstrous creature.  He tells himself it’s probably ",self.font,COLOUR[5],"c") 
                display_text(self.screen,11,"just another myth, but is it really?",self.font,COLOUR[5],"c")
                display_text(self.screen,23,"Press H to continue to next page or press ESCAPE to return to previous menu.",self.font,COLOUR[5],"c")

                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            frames = 0
                            screenindex = 2
                        elif event.key == ord('h'):
                            frames = 0
                            screenindex = 4
               
            while screenindex == 4:
                self.screen.blit(self.menuImageBlank,(0,0))

                display_text(self.screen,3,"HELP SCREEN PAGE 4 of 4:",self.font,COLOUR[5],"c")
                display_text(self.screen,5,"CONTROLS:",self.font,COLOUR[5],"c")
                display_text(self.screen,10, "                                                MUTE     QUIT ",self.font,COLOUR[5],"c")
                display_text(self.screen,10,"           └┐                                    ┌───╖    ┌───╖",self.font,COLOUR[5],"c")
                display_text(self.screen,11,"            └┐          ┌───╖┌───╖               │ M ║    │esc║",self.font,COLOUR[5],"c")
                display_text(self.screen,12,"  LOOK/AIM   │  FORWARD │ W ║│ E ║ INTERACT      ╘═══╝    ╘═══╝",self.font,COLOUR[5],"c")
                display_text(self.screen,13,"            ┌┘       ┌──┴╥┬─╨┴╥┬─╨─╖   ┌──────────────────╖    ",self.font,COLOUR[5],"c")
                display_text(self.screen,14,"           ╓╪╖       │ A ║│ S ║│ D ║   │      Space       ║    ",self.font,COLOUR[5],"c")
                display_text(self.screen,15,"      <──  ║┴║  ──>  ╘═══╝╘═══╝╘═══╝   ╘══════════════════╝    ",self.font,COLOUR[5],"c")
                display_text(self.screen,16,"           ╘═╛       LEFT BACK RIGHT           JUMP            ",self.font,COLOUR[5],"c")
                display_text(self.screen,23,"press ESCAPE to return to previous menu.",self.font,COLOUR[5],"c")
                
                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            frames = 0
                            screenindex = 3

            while screenindex == 10:
                self.screen.blit(self.menuImage,(0,0))

                display_text(self.screen,14,"You died!",self.font,COLOUR[5],"c")
                display_text(self.screen,16,"Press space to return to main menu.",self.font,COLOUR[5],"c")
                display_text(self.screen,17,"Press escape to quit the game.",self.font,COLOUR[5],"c")
                
                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            terminate()
                        elif event.key == K_SPACE:
                            screenindex = 0
                            
            while screenindex == 11:
                self.screen.blit(self.menuImage,(0,0))

                display_text(self.screen,14,"Thank you for playing.",self.font,COLOUR[5],"c")
                display_text(self.screen,16,"Press space to return to main menu.",self.font,COLOUR[5],"c")
                display_text(self.screen,17,"Press escape to quit the game.",self.font,COLOUR[5],"c")
                
                self.drawScreen(windowSurface)

                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            terminate()
                        elif event.key == K_SPACE:
                            screenindex = 0  

    # RELATED TO RENDERING 3D SCENE
    
    def TextureMapedTrigon(self,index):
        """ This function is for drawing texture mapped trigons to the screen. I'm really proud of this. I wrote all of this without help or any tutorial.
            The way i wrote this has a major draw back though. Because I'm interpolating between points, i dont get a perfect scanline and so i have to redraw a couple pixels.
            I'll rewrite this later with a proper rasterizer. By using pixelarrays i could do write a whole scanline in one go instead of doing it per pixel. """
        # Projected point vectors
        gap = 2
        a = pygame.math.Vector2(self.projected[index][0])/gap
        b = pygame.math.Vector2(self.projected[index][1])/gap
        c = pygame.math.Vector2(self.projected[index][2])/gap

        # Texture coordinate vectors
        t1 =  self.projected[index][3][2][0]
        t2 =  self.projected[index][3][2][1]
        t3 =  self.projected[index][3][2][2]
        
        ystep = int(a.distance_to(c))       # Get the distance between point a and point c:   
        for y in range(ystep):
            ylerp = (y/ystep)               # Convert y step to float from 0 to 1
            # liniarly interpolate across both the texture surface and the render surface
            
            cA = a.lerp(c,ylerp)
            cB = b.lerp(c,ylerp)
            ct1 = t1.lerp(t3,ylerp)
            ct2 = t2.lerp(t3,ylerp)
            
            xstep = int(cA.distance_to(cB)) # Get the distance betweem the newly generated points from previous lerp operation
            for x in range(xstep):
                xlerp = (x/xstep)
                
                point = cA.lerp(cB,xlerp)
                texpoint = ct1.lerp(ct2,xlerp)
                
                tex = (round(texpoint[0]*self.textures[0].width)%self.textures[0].width,round(texpoint[1]*self.textures[0].height)%self.textures[0].height)
                if point[0] >= 0 and point[0] <= self.disp[1][0] and point[1] >= 0 and point[1] <= self.disp[1][1]:
                    clr = self.textures[0].surface.get_at(tex)
                    point = point * gap
                    pygame.draw.rect(self.screen,clr,(int(point[0]-gap-1),int(point[1]-gap-1),gap+1,gap+1))
    
    def project_points(self):
        """ This function takes a list of points and a camera object,
            projecting the points from 3D space down to screenspace with correct perspective."""

        # ==========================PROJECTING POINTS=========================#

        # Reset projected and depth lists
        self.projected = []
        self.depth = []

        lookVector = self.camera.camera_vect

        for i in range(len(self.scene[0])):
            mesh = self.scene[0][i]

            if mesh.enabled:
                points = mesh.points
                
                if mesh.dynamic:
                    points = x_rot(points,mesh.rot[0])
                    points = y_rot(points,mesh.rot[1])
                    points = z_rot(points,mesh.rot[2])
                    points = xyz_move(points,mesh.pos)

                # Transform object Reletive to camera
                points = xyz_move(points, self.camera.pos + pygame.math.Vector3(0, self.camera.height, 0))
                points = y_rot(points, -self.camera.rot[1])
                points = x_rot(points, -self.camera.rot[0])

                for i in range(len(points)):
                    points[i][3][0] = get_normal(points[i])

                # Clip Polygons against camera clipping planes.
                points = clipTrigon(points, self.camera.clipPlanes, lookVector)
                points = clipTrigon(points, self.camera.clipPlanes, lookVector)
                
                for point in points:
                    
                    # Clear variables for next pass:
                    projected = ()      
                    onscreen = True 
                    z = ((point[0] + point[1] + point[2])/3)[2]
                    
                    for i in range(3):
                        projected += (pygame.math.Vector2((((point[i][0] / -point[i][2])*self.disp[3]) + self.disp[2][0]),
                                                          (((point[i][1] / -point[i][2])*self.disp[3]) + self.disp[2][1])),)
                        # Check projected point is valid:
                        if not pointOnScreen(projected[i],self.disp[1][0],self.disp[1][1]):
                            onscreen = False
                            break

                    if onscreen:
                        projected += (point[3],)
                        self.projected.append(projected)
                        self.depth.append(z)
    
        # =====================RENDERING POINTS TO SCREEN=====================#

        if len(self.projected) != 0:
            
            # generate a list of indices which will be sorted by the depth information.
            # This approach is used because it's faster to swap two sets of data instead of the whole list of points
            
            # SORTING POLYGONS:
            index = [i for i in range(len(self.projected))]
            sortedindex = sort(self.depth, index)

            # DRAWING POLYGONS:

            # locking screen before draw: This prevents reads and almost doubles rendering speed
            self.screen.lock()
            
            # Draw faces to the screen:
            for x in range(len(self.projected)-1,-1,-1):
                index = sortedindex[1][x]
                
                if self.projected[index][3][1] == 0:    # Filled
                    pygame.draw.polygon(self.screen,self.projected[index][3][2],self.projected[index][0:3])
                    
                elif self.projected[index][3][1] == 1:  # Lines
                    pygame.draw.lines(self.screen,self.projected[index][3][2],True,self.projected[index][0:3],1)

                elif self.projected[index][3][1] == 2:  # Dots
                    for i in range(3):
                        pygame.draw.circle(self.screen,self.projected[index][3][2],self.projected[index][i],1)
                    
                elif self.projected[index][3][1] == 3:  # Textured
                    self.TextureMapedTrigon(index)
                
                elif self.projected[index][3][1] == 4:  # Fake Transparency
                    self.screen.unlock()
                    self.transparency.fill(self.projected[index][3][2])
                    pygame.gfxdraw.textured_polygon(self.screen,self.projected[index][0:3],self.transparency,0,0)
                    self.screen.lock()

            self.screen.unlock()
            del self.projected
            del self.depth

    def Reset(self,state, windowSurface):
        """ This function handles reseting the game in the event of a death or reset call."""

        if state == 0:   # is a reset:
            menuIndex = 0
            
        elif state == 1: # is a death:
            menuIndex = 10
            self.drawTransition((200, 60, 60), None, windowSurface)

        elif state == 2: # ending reached:
            menuIndex = 11
            self.drawTransition((200, 200, 200), None, windowSurface)

        # Reset music
        for i in range(len(self.music)):
            self.music[i].set_volume(0)

        # Draw screen transition to make death more obvious
        self.drawTransition((255,255,255),self.menuImage,windowSurface)

        # Display game over screen
        self.main_menu(windowSurface, menuIndex)
        self.drawTransition((255, 255, 255), self.loadingTransition, windowSurface)
        
        # Clear scene and camera
        del self.scene
        del self.camera
        del self.scenes

        # Reset scenes to how they were upon initialization
        self.scenes = copy.deepcopy(self.uninitScenes)

        # Clear other data:
        self.camera = Camera(pygame.math.Vector3(0, 1, 0), [0, -math.pi/2, 0], 0.03, self.disp[4], NEARCLIP, FARCLIP)

        self.onscreenText = []
        self.onscreenTime = []
        self.tick = 0
        self.cycle = 0
        self.level = 0
        self.scene = self.scenes[self.level]

    def updateAudio(self):
        """ This function handles updating audio tracks."""         
        i = 0
        while i < len(self.playvol):
            self.music[self.playvol[i][0]].set_volume(self.max_volume)
            del self.playvol[i]
            i += 1

    def frameDelta(self,clock,fps):
        """ This function handles the frame delta calculations"""
        # Frame delta
        self.Δtime = clock.tick(60) * 0.001 * fps
        self.tick += self.Δtime

        # Update current tick:
        if self.tick >= self.tpc:
            self.tick = self.tick - self.tpc
            self.cycle += 1

    def getInput(self):
        """ This function handles user input"""
        self.musicplaying = self.camera.update(self.Δtime,self.scene[1],self.musicplaying, self.music)

    def runLogic(self,clock,fps):
        """ This function handles the game logic run each frame before displaying the frame."""

        # CALCULATE FRAME Δ
        self.frameDelta(clock,fps)
        if self.Δtime > 10:
            self.Δtime = 10

        # UPDATE GAME STATE
        if self.camera.reset:
            self.gamestate = 1

        if not self.camera.alive:
            self.gamestate = 0

        # UPDATE ONSCREEN TEXT
        
        index = 0
        while index < len(self.onscreenText):
            # subtract number of frames that have passed from onscreen time
            self.onscreenTime[index] -= self.Δtime
            if self.onscreenTime[index] < 0:
                # If the timer is at or bellow 0, remove from queue.
                del self.onscreenTime[index]
                del self.onscreenText[index]
            index += 1
        del index

        # UPDATE MUSIC
        self.updateAudio()

        # CHECK TRIGGERS

        for trigger in self.scene[2]:
            # Check intersection with the trigger,
            if trigger.enabled:
                runcheck = True
                
                # if trigger is an interact trigger and the player is pressing +interact, contunue.
                if len(trigger.keyword) > 1:
                    if trigger.keyword[1] == "INTERACT" and not self.camera.interact:
                        runcheck = False
                
                # if intersecting trigger change game state by
                if runcheck and trigger.mesh.sphereIntersect(self.camera.pos,self.camera.radius):

                    # run corresponding routine
                    if trigger.keyword[0] == "INVENTORY":
                        have = 0
                        havechecks = 0
                        for i in range(len(trigger.mod[0])):
                            # Add item to inventory
                            if trigger.mod[0][i] == "GET":
                                if trigger.mod[1][i] not in self.camera.items:
                                    self.camera.items.append(trigger.mod[1][i])
                                trigger.enabled = False

                            # Remove item from inventory
                            elif trigger.mod[0][i] == "LOSE":
                                if trigger.mod[1][i] in self.camera.items:
                                    self.camera.items.remove(trigger.mod[1][i])
                                trigger.enabled = False

                            # Check if player has any specified item(s)
                            elif trigger.mod[0][i] == "HAVE": #Has the item
                                havechecks += 1
                                if trigger.mod[1][i] in self.camera.items:
                                    have += 1
                            elif trigger.mod[0][i] == "DHAVE": #does not have the item
                                havechecks += 1
                                if trigger.mod[1][i] not in self.camera.items:
                                    have += 1
                        # if the player has all the specified items (FOR HAVE AND DHAVE ONLY!):
                        # if trigger has assosiated text, add it to the queue
                        if trigger.mod[2] is not None:
                            self.onscreenTime.append(120)
                            if have != havechecks: # Pass check text:
                                self.onscreenText.append(trigger.mod[2][1])
                            else:                  # Fail check text:
                                self.onscreenText.append(trigger.mod[2][0])
                    
                        if havechecks != 0 and have == havechecks:
                            # overwrite trigger with secondary trigger information:
                            trigger.keyword, trigger.mod = trigger.keyword[2:len(trigger.keyword)], trigger.mod[3:len(trigger.mod)]

                    if trigger.keyword[0] == "KILL":
                        self.camera.alive = False
                    elif trigger.keyword[0] == "ENABLE" or trigger.keyword[0] == "DISABLE":
                        # set setflag to true if keyword is ENABLE selt False if keyword is DISABLE.
                        setflag = True
                        if trigger.keyword[0] == "DISABLE": setflag = False
                        for i in range(len(trigger.mod[0])):
                            if trigger.mod[1][i] == "MDL":
                                self.scene[0][trigger.mod[0][i]].enabled = setflag
                            elif trigger.mod[1][i] == "COL":
                                self.scene[1][trigger.mod[0][i]].enabled = setflag
                            elif trigger.mod[1][i] == "TRG":
                                self.scene[2][trigger.mod[0][i]].enabled = setflag
                    
                    elif trigger.keyword[0] == "EXIT":
                        # -1 game state is the win condition
                        if trigger.mod[0] == -1:
                            self.gamestate = -1
                            return
                        # Replace data with new level
                        self.scenes[self.level] = self.scene
                        self.level = trigger.mod[0]
                        self.scene = self.scenes[self.level]
                        self.camera.pos = trigger.mod[1]
                    elif trigger.keyword[0] == "HINT":
                        for text in trigger.mod[0]:
                            if text not in self.onscreenText:
                                self.onscreenTime.append(trigger.mod[1])
                                self.onscreenText.append(text)
                        # if repeat set to True, only show it once if set to False.
                        trigger.enabled = trigger.mod[2]
                    elif trigger.keyword[0] == "SETPLAYER":
                        self.camera.pos = trigger.mod[0]
                        self.camera.rot = trigger.mod[1]
                        trigger.enabled = False
                    elif trigger.keyword[0] == "TIME":
                        trigger.mod[0] -= self.Δtime
                        if trigger.mod[0] <= 0:
                            trigger.keyword, trigger.mod = trigger.keyword[1:len(trigger.keyword)], trigger.mod[1:len(trigger.mod)]
                    elif trigger.keyword[0] == "PLAYVOL":
                        self.playvol.append(trigger.mod)
                        trigger.enabled = False

    def CheckReset(self, windowSurface):
        # Check for death/reset
        if self.gamestate == 2: # Do nothing
            return
        
        elif self.gamestate == 1:   # Reset condition
            self.Reset(0,windowSurface)
            self.gamestate = 2
            self.camera.reset = False
        
        elif self.gamestate == 0:  # Death condition
            self.Reset(1,windowSurface)
            self.gamestate = 2
            
        elif self.gamestate == -1:  # Ending condition
            self.Reset(2,windowSurface)
            self.gamestate = 2

    def drawScreen(self, windowSurface):
        """ This function handles scaling and transforming the rendersurface to the window surface."""
        screenscale = pygame.transform.scale(self.screen,self.rescale)
        windowSurface.blit(screenscale,self.scalepos)

        # Update Screen
        pygame.display.flip()

    def displayHud(self):
        # Display HUD elements
        self.screen.blit(self.reticle,(self.disp[2][0]-16,self.disp[2][1]-16))

        # Display Frames Per Second
        display_text(self.screen,0,"FPS : "+str(round(60 / self.Δtime,3)),self.font,COLOUR[0],"l")
        
        # Display onscreenText
        for i in range(len(self.onscreenText)):
            display_text(self.screen,14 + i,self.onscreenText[i],self.font,COLOUR[0],"c")

        # Display inventory
        inventory = "ITEMS : "
        for i in range(len(self.camera.items)):
            inventory += " "+self.camera.items[i]
        display_text(self.screen,23,inventory,self.font,COLOUR[0],"l")
            
    def displayFrame(self,windowSurface):
        """ This function handles rendering and displaying the current frame"""

        self.screen.fill(COLOUR[8])
        self.project_points()
        self.displayHud()
        self.drawScreen(windowSurface)

        # Check for a reset:
        self.CheckReset(windowSurface)

def main():
    """ Mainline function for Constalus"""
    pygame.init()
    fps = 60
    disp_settings = setResolution(WIDTH,HEIGHT,RWIDTH,RHEIGHT,2,60)

    #   SET WINDOW SURFCE FLAGS
    flags = pygame.FULLSCREEN | pygame.SCALED
    windowSurface = pygame.display.set_mode((WIDTH,HEIGHT),flags,depth = 0,vsync = 1)

    #   INIT DISPLAY
    icon = pygame.image.load("assets/textures/icon.png").convert()
    pygame.display.set_caption("Constalus")     #Set caption
    pygame.display.set_icon(icon)               #Set icon
    clock = pygame.time.Clock()                 #Define clock
    font = pygame.font.SysFont("courier new",12)#Set up font

    possiblepos = [(0.5,-0.2,5),
                   (-7,-0.2,9),
                   (-4,-0.2,3.6),
                   (-15,-0.2,6),
                   (-10.9,-0.2,9),
                   (-12.7,-0.2,7),
                   (-10,-0.2,-3),
                   (-15,-0.2,-7),
                   (-2,-0.2,-2.5),
                   (0,-0.2,-9),
                   (-14.5,-0.2,-9),
                   (-8.5,-0.2,-9)]
    
    randpos = randomPosition(possiblepos,6)

    # All this is how i declare objects in the scene.
    # Scenes are stored with 3 types. There are Three data types.
    # MDL, Short for "Model" which is stored useing the Mesh class,
    # MDLs require a .obj file as it is every easy to decode. Just be sure to not incude any UV or Normal information,
    # unless useing render type 3.

    # COL, Short for "Collider" Which is a variant of the Mesh class that handles collision detection with sphere
    # objects. Colliders are all mesh colliders, not capable of detecting when the player is within the area defined by
    # the mesh, only intersecting with the outside edge.
    
    # TRG, Short for "Trigger" stores any events that happen in the game. They all work on the same principle.
    # All TRG objects have a keyword list and a mod list. The keyword stores the action to be done, and the mod
    # list stores the modifiers that effect what is actually being triggered. For example,
    # the text: ["ENABLE"],True[[1],["MDL"]] is active, and will enable the second model in the scene when touched.

    # Decalring MDL:
    # |FILENAME|POSITION|ROTATION|SCALE|DYNAMIC LIGHTING|DYNAMIC POSSITION|ACTIVE|COLOUR|RENDER TYPE|

    # Declaring COL:
    # |FILENAME|POSITION|ROTATION|SCALE|NONE,USED ELSEWHERE|ACTIVE|

    # Declaring TRG:
    # |FILENAME|POSSITION|ROTATION|SCALE|KEYWORD(LIST)|ACTIVE|MODIFFIER(LIST)|
    
    data00 = (('MDL',"assets/level/00/ruins_0.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(200,170,140),0,),
              ('MDL',"assets/level/00/ruins_1.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(115,114,112),0,),
              ('MDL',"assets/level/00/ruins_2.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(158,88,88),  0,),
              ('MDL',"assets/level/00/ground.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True,(160,200,100),0,),
              ('MDL',"assets/level/00/water_0.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(219,241,235),0,),
              ('MDL',"assets/level/00/water_1.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(198,231,226),0,),
              ('MDL',"assets/level/00/water_2.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(176,218,213),0,),
              ('MDL',"assets/level/00/water_3.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True,(156,210,210),0,),
              ('MDL',"assets/level/00/shore.obj",        (0,0,0),(0,0,0),(1,1,1),False,False,True,(243,237,210),0,),
              ('MDL',"assets/level/00/mount.obj",        (0,0,0),(0,0,0),(1,1,1),False,False,True,(200,170,140),0,),
              ('MDL',"assets/level/00/boat.obj",      (0,0.52,0),(0,0,0),(1,1,1),False,False,True,(100,80,65),  0,),
              ('MDL',"assets/level/00/ruby.obj",         (0,0,0),(0,0,0),(1,1,1),False,False,True,(178,88,98),  4,),
              ('MDL',"assets/level/00/temple_earth.obj", (0,0,0),(0,0,0),(1,1,1),False,False,True,(178,88,98),  3,),
              ('COL',"assets/level/00/island_c.obj",     (0,0,0),(0,0,0),(1,1,1),None,True,),
              ('TRG',"assets/level/00/triggers/Exit.obj",(0,0,0),(0,0,0),(1,1,1),["EXIT"],     True,  [1,(0,0,0)],),
              ('TRG',"assets/level/00/triggers/ruby_hint.obj", (0,0,0),(0,0,0),(1,1,1),["INVENTORY","INTERACT"], True,[["GET"],["RUBY"],None]),
              ('TRG',"assets/level/00/triggers/ruby_hint.obj", (0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[11],["MDL"]]),
              ('TRG',"assets/level/00/triggers/ruby_hint.obj", (0,0,0),(0,0,0),(1,1,1),["ENABLE","INTERACT"],True,  [[5],["TRG"]]),
              ('TRG',"assets/level/00/triggers/ruby_hint.obj", (0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,  [['I can’t believe it!  I’ve really done it.',
                                                                                                                     'I’ve found The Eye of Zeus!  But, how did it get here?',
                                                                                                                     'Did Daedalus put it in the temple for safekeeping? It’s so heavy!',
                                                                                                                     'There’s no way he could fly it off the island with his wings of ',
                                                                                                                     'wax, wood, and feathers.'],700,False]),
              
              ('TRG',"assets/level/00/triggers/after_ruby_pickup.obj",  (0,0,0),(0,0,0),(1,1,1),["HINT"],False,  [['The legend says this place has a lighthouse.',
                                                                                                                   'If I can get it working, someone will come to rescue me.',
                                                                                                                   'Maybe it’s in that other temple?'],500,False]),
              
              ('TRG',"assets/level/00/triggers/hint_0.obj",             (0,0,0),(0,0,0),(1,1,1),["HINT"],True,  [['Where am I?  My boat!  What’s happened?'],300,False]),
              ('TRG',"assets/level/00/triggers/hint_1.obj",             (0,0,0),(0,0,0),(1,1,1),["HINT"],True,  [['Are those temples?','Have I actually made it to Constalus?','I’d better go take a closer look.'],300,False]),

              ('TRG',"assets/level/00/triggers/boat_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["HINT"],True,  [['A ruined boat.'],10,True]),
              ('TRG',"assets/level/00/triggers/boat_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,  [['The hull is cracked beyond repair.  This boat will never sail again. '],120,True]),
              ('TRG',"assets/level/00/triggers/boat_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"],True,[[8],['TRG']]),
              ('TRG',"assets/level/00/triggers/vase_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["HINT"],True,  [['An ancient broken vase.'],10,True]),
              ('TRG',"assets/level/00/triggers/vase_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,  [['How did this get here?  Maybe it came from inside that temple?'],120,True]),
              ('TRG',"assets/level/00/triggers/vase_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"],True,[[11],['TRG']]),  
              ('TRG',"assets/level/00/triggers/earth_temple_hint.obj",  (0,0,0),(0,0,0),(1,1,1),["HINT"],True,  [['I wonder what’s inside here?','Might this be the temple of the Earth Goddess?'],300,False]),              
              ('TEX',"assets/textures/earth_temple.png",),
              ('TRG', "assets/level/00/triggers/hint_0.obj", (0,0,0),(0,0,0),(1,1,1),["PLAYVOL"],True,[0, 0, 3000]),
              ('TRG', "assets/level/00/triggers/hint_1.obj", (0,0,0),(0,0,0),(1,1,1),["PLAYVOL"],True,[1, 0, 3000]),
              ('TRG', "assets/level/00/triggers/earth_temple_hint.obj", (0, 0, 0), (0, 0, 0), (1, 1, 1), ["PLAYVOL"], True, [2, 0, 3000]),
            )
                
    data01 = (('MDL',"assets/level/01/puzzle.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (120,179,186),0,),
              ('MDL',"assets/level/01/door.obj",         (0,0,0),(0,0,0),(1,1,1),False,False,False,(120,179,186),0,),
              ('MDL',"assets/level/01/cave_0.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (115,114,112),0,),
              ('MDL',"assets/level/01/cave_1.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (98,97,96),   0,),
              ('MDL',"assets/level/01/cave_r.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (78,77,76),   0,),
              ('MDL',"assets/level/01/cave_2.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (96,88,85),   0,),
              ('MDL',"assets/level/01/cave_3.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),   0,),
              ('MDL',"assets/level/01/cave_3_O.obj",     (0,0,0),(0,0,0),(1,1,1),False,False,False,(59,57,56),   0,),
              ('MDL',"assets/level/01/cave_4.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (39,37,37,),  0,),
              ('MDL',"assets/level/01/cave_5.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (25,23,23),   0,),
              ('COL',"assets/level/01/cave_c.obj",       (0,0,0),(0,0,0),(1,1,1),None,True,),
              ('COL',"assets/level/01/cave_c_O.obj",     (0,0,0),(0,0,0),(1,1,1),None,False,),
              ('TRG',"assets/level/01/triggers/DoorOpen.obj",    (0,0,0),(0,0,0),(1,1,1),["ENABLE"],     True,   [[1,7,1,2,8],["MDL","MDL","COL","TRG","TRG"]]),
              ('TRG',"assets/level/01/triggers/DoorOpen.obj",    (0,0,0),(0,0,0),(1,1,1),["DISABLE"],    True,   [[0,6,0,0,1],["MDL","MDL","COL","TRG","TRG"]]),
              ('TRG',"assets/level/01/triggers/Exit_next.obj",   (0,0,0),(0,0,0),(1,1,1),["EXIT"],       False,  [2,(0,0,0)]),
              ('TRG',"assets/level/01/triggers/Exit_outside.obj",(0,0,0),(0,0,0),(1,1,1),["EXIT"],       True,   [0,(8.07,3.4,28.3)]),
              ('TRG',"assets/level/01/triggers/Kill.obj",        (0,0,0),(0,0,0),(1,1,1),["KILL"],       True,   None),
              ('TRG',"assets/level/01/triggers/hint.obj",        (0,0,0),(0,0,0),(1,1,1),["HINT"],True,  [['A triangular shape with images at its vertices and glyphs below'],10,True]),
              ('TRG',"assets/level/01/triggers/hint.obj",        (0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,  [['The inscription reads:','Open the temple of the Goddess to thee,','align yourself with earth, sky, and sea.'],300,True]),
              ('TRG',"assets/level/01/triggers/hint.obj",        (0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"],True,[[5],['TRG']]),
              ('TRG',"assets/level/01/triggers/DoorOpen.obj",    (0,0,0),(0,0,0),(1,1,1),["HINT"],False,  [['Is that a door?  Of course, it all makes sense!',
                                                                                                            'I aligned with the triad and the temple has opened for me.',
                                                                                                            'It looks like it might be some sort of maze.'],500,False]),
              ('TRG', "assets/level/01/triggers/DoorOpen.obj", (0, 0, 0), (0, 0, 0), (1, 1, 1),["PLAYVOL"],True,[3, 0, 3000]),
              )

    data02 = (('MDL',"assets/level/02/room_0.obj",      (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),   0,),
              ('MDL',"assets/level/02/L_room_1.obj",    (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),   0,),
              ('MDL',"assets/level/02/L_room_2.obj",    (0,0,0),(0,0,0),(1,1,1),False,False,True, (78,77,76),   0,),
              ('MDL',"assets/level/02/R_room_1.obj",    (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),   0,),
              ('MDL',"assets/level/02/R_room_2.obj",    (0,0,0),(0,0,0),(1,1,1),False,False,True, (78,77,76),   0,),
              ('MDL',"assets/level/02/ruins.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (78,77,76),   0,),
              ('COL',"assets/level/02/room_c.obj",      (0,0,0),(0,0,0),(1,1,1),None,True,),
              ('COL',"assets/level/02/room_c_2.obj",    (0,0,0),(0,0,0),(1,1,1),None,False,),
              ('TRG',"assets/level/02/triggers/R_Disable.obj",  (0,0,0),(0,0,0),(1,1,1),["DISABLE"],True,[[3,4,0,5],["MDL","MDL","MDL","MDL"]]),
              ('TRG',"assets/level/02/triggers/R_Enable.obj",   (0,0,0),(0,0,0),(1,1,1),["ENABLE"], True,[[3,4,0,5],["MDL","MDL","MDL","MDL"]]),
              ('TRG',"assets/level/02/triggers/L_Disable.obj",  (0,0,0),(0,0,0),(1,1,1),["DISABLE"],True,[[1,2,0,5],["MDL","MDL","MDL","MDL"]]),
              ('TRG',"assets/level/02/triggers/L_Enable.obj",   (0,0,0),(0,0,0),(1,1,1),["ENABLE"], True,[[1,2,0,5],["MDL","MDL","MDL","MDL"]]),
              # Rubble 1 MDL 6
              ('MDL',"assets/level/02/rubble.obj",       randpos[0],(0,0,0),(1,1,1),False,False,True,(120,179,186), 0,),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[0],(0,0,0),(1,1,1),["INVENTORY","INTERACT"], True,[["GET"],["D1"],["A broken piece of the archway."]]),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[0],(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[6,4,16],["MDL","TRG","TRG"]]),
              # Rubble 2 MDL 7
              ('MDL',"assets/level/02/rubble.obj",       randpos[1],(0,0,0),(1,1,1),False,False,True,(120,179,186), 0,),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[1],(0,0,0),(1,1,1),["INVENTORY","INTERACT"], True,[["GET"],["D2"],["A broken piece of the archway."]]),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[1],(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[7,6,17],["MDL","TRG","TRG"]]),
              # Rubble 3 MDL 8
              ('MDL',"assets/level/02/rubble.obj",       randpos[2],(0,0,0),(1,1,1),False,False,True,(120,179,186), 0,),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[2],(0,0,0),(1,1,1),["INVENTORY","INTERACT"], True,[["GET"],["D3"],["A broken piece of the archway."]]),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[2],(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[8,8,18],["MDL","TRG","TRG"]]),
              # Rubble 4 MDL 9
              ('MDL',"assets/level/02/rubble.obj",       randpos[3],(0,0,0),(1,1,1),False,False,True,(120,179,186), 0,),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[3],(0,0,0),(1,1,1),["INVENTORY","INTERACT"], True,[["GET"],["D4"],["A broken piece of the archway."]]),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[3],(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[9,10,19],["MDL","TRG","TRG"]]),
              # dummy rubble 5 MDL 10
              ('MDL',"assets/level/02/rubble.obj",       randpos[4],(0,0,0),(1,1,1),False,False,True,(120,179,186), 0,),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[4],(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[10,20],["MDL","TRG"]]),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[4],(0,0,0),(1,1,1),["ENABLE","INTERACT"], True,  [[22],["TRG"]]),
              # dummy rubble 6 MDL 11
              ('MDL',"assets/level/02/rubble.obj",       randpos[5],(0,0,0),(1,1,1),False,False,True,(120,179,186), 0,),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[5],(0,0,0),(1,1,1),["DISABLE","INTERACT"], True,  [[11,21],["MDL","TRG"]]),
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[5],(0,0,0),(1,1,1),["ENABLE","INTERACT"], True,  [[23],["TRG"]]),
              # TRG starts at 16
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[0],(0,0,0),(1,1,1),["HINT"],True,[['Press "E" to search rubble'],10,True]),#16
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[1],(0,0,0),(1,1,1),["HINT"],True,[['Press "E" to search rubble'],10,True]),#17
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[2],(0,0,0),(1,1,1),["HINT"],True,[['Press "E" to search rubble'],10,True]),#18
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[3],(0,0,0),(1,1,1),["HINT"],True,[['Press "E" to search rubble'],10,True]),#19
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[4],(0,0,0),(1,1,1),["HINT"],True,[['Press "E" to search rubble'],10,True]),#20
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[5],(0,0,0),(1,1,1),["HINT"],True,[['Press "E" to search rubble'],10,True]),#21
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[4],(0,0,0),(1,1,1),["HINT"],False,[['Hmm... Nothing of use here, I should keep looking.'],120,False]),#22
              ('TRG',"assets/level/02/triggers/Find.obj",randpos[5],(0,0,0),(1,1,1),["HINT"],False,[['Hmm... Nothing of use here, I should keep looking.'],120,False]),#23
              ('MDL',"assets/level/02/d1.obj",(0,0,0),(0,0,0),(1,1,1),False,False,True,(120,179,186), 4,),#12
              ('MDL',"assets/level/02/d2.obj",(0,0,0),(0,0,0),(1,1,1),False,False,True,(120,179,186), 4,),#13
              ('MDL',"assets/level/02/d3.obj",(0,0,0),(0,0,0),(1,1,1),False,False,True,(120,179,186), 4,),#14
              ('MDL',"assets/level/02/d4.obj",(0,0,0),(0,0,0),(1,1,1),False,False,True,(120,179,186), 4,),#15
              ('MDL',"assets/level/02/door_final.obj", (0,0,0),(0,0,0),(1,1,1),False,False,False,(59,57,56), 0,),#16
              ('MDL',"assets/level/02/door_final2.obj",(0,0,0),(0,0,0),(1,1,1),False,False,False,(120,179,186), 0,),#17
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["INVENTORY","INTERACT","ENABLE"],False,[["HAVE","HAVE","HAVE","HAVE"],["D1","D2","D3","D4"],["That's it! the door appears to be open now.","'Still don't have all 4 pieces. Better keep looking."],[16,17,25,27,28,30,31,1],["MDL","MDL","TRG","TRG","TRG","TRG","TRG","COL"]]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["DISABLE"],False,[[0,12,13,14,15,24,26,0],["MDL","MDL","MDL","MDL","MDL","TRG","TRG","COL"]]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["HINT"],True,[['A plinth with glyphs on it.'],10,True]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["HINT"],False,[['aha! That looks like it opened the door.'],120,False]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["SETPLAYER"],False,[[5.25,0.4,0],[0,-math.pi/2,0]]),              
              ('TRG',"assets/level/02/triggers/Exit.obj",     (0,0,0),(0,0,0),(1,1,1),["EXIT"],True,[3,(0,0,0)]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["INVENTORY"],False,[["LOSE","LOSE","LOSE","LOSE"],["D1","D2","D3","D4"],None]),
              ('TRG',"assets/level/02/triggers/hint0.obj",    (0,0,0),(0,0,0),(1,1,1),["HINT"],False,[["I've already been this way."],60,True]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"],True,[[26],["TRG"]]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["ENABLE","INTERACT"],True,[[24],["TRG"]]),
              ('TRG',"assets/level/02/triggers/DoorCheck.obj",(0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,[['The inscription reads:',
                                                                                                                 '"Align the arches and ascend, beware if thou aren’t Zeus’ friend."','',
                                                                                                                 'I’m not sure what that means, but I think I see some rubble over there.',
                                                                                                                 'Maybe I can rebuild the arches if the pieces are still here.'],400,False]),
              ('TRG',"assets/level/02/triggers/minotaur.obj", (0,0,0),(0,0,0),(1,1,1),["HINT"],True,[['A floor pattern with glyphs on it.'],10,True]), 
              ('TRG',"assets/level/02/triggers/minotaur.obj", (0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,[['The inscription reads:','"Enter the labyrinth if you dare, the Minotaur defends Zeus’ stare."',],120,True]),
              ('TRG',"assets/level/02/triggers/minotaur.obj", (0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"],True,[[35],["TRG"]]),
              )
            
    data03 = (('MDL',"assets/level/03/Lense.obj",           (0,0,0),(0,0,0),(1,1,1),False,False,True, (120,179,186), 4,),
              ('MDL',"assets/level/03/Ray.obj",             (0,0,0),(0,0,0),(1,1,1),False,False,True, (219,241,235), 4,),
              ('MDL',"assets/level/03/ruby.obj",            (0,0,0),(0,0,0),(1,1,1),False,False,False,(178,88,98),   4,),
              ('MDL',"assets/level/03/Ray_Kill.obj",        (0,0,0),(0,0,0),(1,1,1),False,False,False,(219,241,235), 4,),
              ('MDL',"assets/level/03/Ray_Beam.obj",        (0,0,0),(0,0,0),(1,1,1),False,False,False,(253,94,125),  4,),

              ('MDL',"assets/level/03/Tower.obj",           (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),    0,),
              ('MDL',"assets/level/03/Ray_emitter.obj",     (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),    0,),
              ('MDL',"assets/level/03/Tower2.obj",          (0,0,0),(0,0,0),(1,1,1),False,False,True, (158,88,88),   0,),
              ('MDL',"assets/level/03/Stairs.obj",          (0,0,0),(0,0,0),(1,1,1),False,False,True, (59,57,56),    0,),
              ('MDL',"assets/level/03/LastLevel.obj",       (0,0,0),(0,0,0),(1,1,1),False,False,True, (120,179,186), 0,),
              ('MDL',"assets/level/03/Mirror.obj",          (0,0,0),(0,0,0),(1,1,1),False,False,True, (219,241,235), 0,),

              ('MDL',"assets/level/03/outside/ground.obj",  (0,0,0),(0,0,0),(1,1,1),False,False,True, (243,237,210), 0,),
              ('MDL',"assets/level/03/outside/water_0.obj", (0,0,0),(0,0,0),(1,1,1),False,False,True, (219,241,235), 0,),
              ('MDL',"assets/level/03/outside/water_1.obj", (0,0,0),(0,0,0),(1,1,1),False,False,True, (198,231,226), 0,),
              ('MDL',"assets/level/03/outside/water_2.obj", (0,0,0),(0,0,0),(1,1,1),False,False,True, (176,218,213), 0,),
              ('MDL',"assets/level/03/outside/water_3.obj", (0,0,0),(0,0,0),(1,1,1),False,False,True, (156,210,210), 0,),
              ('MDL',"assets/level/03/outside/shore.obj",   (0,0,0),(0,0,0),(1,1,1),False,False,True, (160,200,100), 0,),
               
              ('COL',"assets/level/03/Tower_Collider.obj",  (0,0,0),(0,0,0),(1,1,1),None,True,),
              ('COL',"assets/level/03/Stairs_collider.obj", (0,0,0),(0,0,0),(1,1,1),None,True,),
              ('COL',"assets/level/03/Ray_emitter.obj",     (0,0,0),(0,0,0),(1,1,1),None,True,),

              # Return to last area
              ('TRG',"assets/level/03/triggers/ExitLastLevel.obj",  (0,0,0),(0,0,0),(1,1,1),["EXIT"],True,[2,(13,0.8,0)]),

              # Checks after player steps off platform, Indiana Jones style weighted pressure plate
              ('TRG',"assets/level/03/triggers/Ruby_Check.obj",     (0,0,0),(0,0,0),(1,1,1),["KILL"],False,None),
              ('TRG',"assets/level/03/triggers/Ruby_Check.obj",     (0,0,0),(0,0,0),(1,1,1),["ENABLE"],     False,[[3],["MDL"]]), # death 
              ('TRG',"assets/level/03/triggers/Ruby_Check.obj",     (0,0,0),(0,0,0),(1,1,1),["ENABLE"],     False,[[4],["MDL"]]), # live
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",     (0,0,0),(0,0,0),(1,1,1),["DISABLE"],    False,[[6,1,2,7,8],["TRG","TRG","TRG","TRG","TRG"]]), # live
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",     (0,0,0),(0,0,0),(1,1,1),["INVENTORY"],  False,[["LOSE"],["RUBY"],None]),
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",     (0,0,0),(0,0,0),(1,1,1),["ENABLE"],     True, [[1],["TRG"]]),
                
              # Checks for if the player has the ruby in their inventory
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",      (0,0,0),(0,0,0),(1,1,1),["INVENTORY","INTERACT","ENABLE"],False,[["HAVE"],["RUBY"],["I've done it! I've lit the beacon.","I must be missing something, I dont have anything to part with!"],[4,3,5,16,17,2],["TRG","TRG","TRG","TRG","TRG","MDL"]]),
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",      (0,0,0),(0,0,0),(1,1,1),["INVENTORY","INTERACT","ENABLE"],False,[["DHAVE"],["RUBY"],None,[2,1],["TRG","TRG"]]),

              # Hints
              ('TRG',"assets/level/03/triggers/hint_0.obj",          (0,0,0),(0,0,0),(1,1,1),["HINT"],True,[["Is that a stairway?"],100,False]),
              ('TRG',"assets/level/03/triggers/hint_1.obj",          (0,0,0),(0,0,0),(1,1,1),["HINT"],True,[['I can see something on that platform to the left, but I’ll',
                                                                                                              'have to take a step closer to make it out clearly.',
                                                                                                              'I wish I could fly like Daedalus could,',
                                                                                                              'something about that platform makes me uneasy.'],400,False]),
              ('TRG',"assets/level/03/Ray.obj",             (0,0,0),(0,0,0),(1,1,1),["KILL"],True,None),

              # Inscruiption
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",      (0,0,0),(0,0,0),(1,1,1),["HINT"],True,[["A triangular glyph."],10,True]),
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",      (0,0,0),(0,0,0),(1,1,1),["HINT","INTERACT"],True,[['The inscription reads:','"Part with the ruby that you cherish,','or the Gods will watch you perish."'],200,False]),
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",      (0,0,0),(0,0,0),(1,1,1),["ENABLE","INTERACT"],True,[[8,7],["TRG","TRG"]]),     
              ('TRG',"assets/level/03/triggers/Ruby_Place.obj",      (0,0,0),(0,0,0),(1,1,1),["DISABLE","INTERACT"],True,[[12,13,15],["TRG","TRG","TRG"]]), 
              ('TRG',"assets/level/03/triggers/Ruby_Check.obj",      (0,0,0),(0,0,0),(1,1,1),["HINT"],False,[['It should only be a matter','of time before someone rescues me.'],200,False]),
              ('TRG',"assets/level/03/triggers/Ruby_Check.obj",      (0,0,0),(0,0,0),(1,1,1),["TIME","EXIT"],False,[200,-1,(0,0,0)],)
              )
    
    scenes = (data00, data01, data02, data03)

    music = (("assets/sounds/track 0.wav",),
             ("assets/sounds/track 1.wav",),
             ("assets/sounds/track 2.wav",),
             ("assets/sounds/track 3.wav",),)
    
    # Initialize Game
    game = Game(windowSurface,font,disp_settings,scenes,music)
    
    # Hide Mouse
    pygame.mouse.set_visible(False)
    pygame.mouse.set_pos(CENTERX,CENTERY)
    
    while True:
        game.getInput()
        game.runLogic(clock,fps)
        game.displayFrame(windowSurface)
main()
