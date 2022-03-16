# This program was writen by E.Parker on 11,29,2921
# This program contains various utilities used in loading/rendering 3d objects
import math, pygame, time, os
from pygame.locals import *

# Define colour palette
colour = ('2D3740','394650','465560','586770','728289','829296','A4B3B1','BAC7C1','CBD6CD','ECF1EB',)
DEGTORADCONST = (math.pi / 180)

# ==============================DISPLAY===============================#

def paletteGen(colours):
    """ This function generates a colour palette from a list of hex codes"""
    palatte = ()
    for i in range(len(colours)):
        red = int("0x"+colours[i][0:2],0)
        grn = int("0x"+colours[i][2:4],0)
        blu = int("0x"+colours[i][4:6],0)
        palatte = palatte + ((red,grn,blu,),)
    return (palatte)

COLOUR = paletteGen(colour)

def display_text(windowSurface,line,text,basicFont,fg,linetype):
    """ This function writes text on the screen """
    # Variables:
    # widnowSurface      -     Surface the text is drawn on
    # line               -     Currently broken,

    # set up the text
    text = basicFont.render(text, False, fg)
    textRect = text.get_rect()

    textRect.top = windowSurface.get_rect().top + (basicFont.get_height() * line)
    if linetype == 'l':
        textRect.left = windowSurface.get_rect().left
    elif linetype == 'r':
        textRect.right = windowSurface.get_rect().right
    elif linetype == 'c':
        textRect.centerx = windowSurface.get_rect().centerx

    # draw the text's background rectangle onto the surface
    windowSurface.blit(text, textRect)

# ===============================SORTING==============================#

def QuickSort(sort,indx):
    """my implementation of the QuickSort algorithm originaly writen by Tony Hoare, 1960."""

    elements = len(sort)

    # Base case
    if elements < 2:
        return sort, indx

    current_position = 0

    for i in range(1, elements):
        if sort[i] < sort[0]:
            current_position += 1
            sort[i], sort[current_position] = sort[current_position], sort[i]
            indx[i], indx[current_position] = indx[current_position], indx[i]
    sort[0], sort[current_position] = sort[current_position], sort[0]
    indx[0], indx[current_position] = indx[current_position], indx[0]

    # recursively sort blocks
    left = QuickSort(sort[0:current_position],indx[0:current_position])
    right = QuickSort(sort[current_position + 1:elements],indx[current_position + 1:elements])

    # recombine lists into one list
    return sort, left[1] + [indx[current_position]] + right[1]

# ==========================3D Projection=============================#

def GenClip(fov,near,far):
    """ This function handles generating the points that form the clipping plane used when rendering.
        The planes are stored as a mesh to make rotating and translating the points easy."""

    Hfov = (fov - 9.45) * DEGTORADCONST

    # Im not sure why i need this number for the aspect, the 16/9 aspect ratio doesnt quite work.
    aspect = 0.68
    Vfov = Hfov * aspect

    # Solving for the top and left points on the far plane
    HfarsideLength = far * (math.tan((Hfov)))  # get horisontal side length
    VfarsideLength = far * (math.tan((Vfov)))  # get vertical side length

    # generate points:
    # These points are the 8 corners of the thrustum fromed by the area seen by the camera.

    c1 = pygame.math.Vector3(HfarsideLength,VfarsideLength,far)
    c2 = pygame.math.Vector3(HfarsideLength,-VfarsideLength,far)
    c3 = c1.normalize() * near
    c4 = c2.normalize() * near
    c5 = pygame.math.Vector3(-HfarsideLength,VfarsideLength,far)
    c6 = pygame.math.Vector3(-HfarsideLength,-VfarsideLength,far)
    c7 = c5.normalize() * near
    c8 = c6.normalize() * near

    # Generate mesh from points.
    # I store it as a mesh so that i can then reuse the Plane class when clipping polygons.
    # there are two planes for each face, this helps catch floating point errors.

    points = ((c1,c5,c7,None),
              (c6,c2,c4,None),
              (c6,c5,c1,None),
              (c7,c4,c3,None),
              (c3,c2,c1,None),
              (c5,c6,c8,None),
              (c7,c3,c1,None),
              (c4,c7,c8,None),
              (c8,c7,c5,None),
              (c4,c8,c6,None),
              (c6,c1,c2,None),
              (c4,c2,c3,None),)

    return points

def clipTrigon(points,planes,lookVector):
    """ This function clips 3d trigons to a list of planes."""
    # Check all points against planes, the update list of points before checking next plane.
    # This method means i only need to do as many passes as there are planes.

    #Variables:
    #i  -   index used to count through list of points. This is done with a while because the length of points changes with each pass.
    #a  -   stores the first point in the list of points.
    #b  -   stores the second point in the list of points.
    #c  -   stores the third point in the list of points.

    #inside -   used to keep track of the number of points that are within the view of the camera.
    #aInside -  bool for if point "a" is in the camera's view
    #bInside -  bool for if point "b" is in the camera's view
    #cInside -  bool for if point "c" is in the camera's view

    

    for plane in planes:
        i = 0
        while i < len(points):
            a, b, c = points[i][0], points[i][1], points[i][2]
            inside = 0

            # Check if the player can see the face:
            if not points[i][3][0].dot(lookVector) > 0.5:
                #Check if each point is within 0.001 units of the current face or less.
                if plane.pointToPlane(a) > 0.0001:
                    aInside = True
                    inside += 1
                else:
                    aInside = False

                if plane.pointToPlane(b) > 0.0001:
                    bInside = True
                    inside += 1
                else:
                    bInside = False

                if plane.pointToPlane(c) > 0.0001:
                    cInside = True
                    inside += 1
                else:
                    cInside = False

            if inside == 0: #Don't render polygon
                del points[i]

            elif inside == 1: #Clip into trigon
                if aInside:
                    points[i] = (a,plane.vectorPlaneIntersect(a,b),plane.vectorPlaneIntersect(a,c),points[i][3])
                elif bInside:
                    points[i] = (b,plane.vectorPlaneIntersect(b,a),plane.vectorPlaneIntersect(b,c),points[i][3])
                elif cInside:
                    points[i] = (c,plane.vectorPlaneIntersect(c,b),plane.vectorPlaneIntersect(c,a),points[i][3])

            elif inside == 2: #Clip into quad, then quad to trigon.
                #store metatdata in temp location so both new faces can inherit the same normal vector and colour.
                metadata = points[i][3]
                if not aInside:     #A is not on screen
                    ab, ac = plane.vectorPlaneIntersect(a,b), plane.vectorPlaneIntersect(a,c)
                    points[i] = (b,ab,ac,metadata)
                    points.insert(i,(c,b,ac,metadata))
                elif not bInside:   #B is not on screen
                    ba, bc = plane.vectorPlaneIntersect(b,a), plane.vectorPlaneIntersect(b,c)
                    points[i] = (a,ba,bc,metadata)
                    points.insert(i,(a,c,bc,metadata))
                elif not cInside:   #C is not on screen
                    cb, ca = plane.vectorPlaneIntersect(c,b), plane.vectorPlaneIntersect(c,a)
                    points[i] = (b,cb,ca,metadata)
                    points.insert(i,(b,a,ca,metadata))
            i += 1
    return points

def pointOnScreen(point, width, height):
    """ Just a simple is this point on screen function. Nothing special here."""
    # left right top bottom
    if 0 < point[0] < width and 0 < point[1] < height:
        return True
    return False

class Atlas():
    """ The Atlas class is a simple datatype that stores the relevent data for a texture atlas. Think of it like one big texture all meshes reference for image information.
        This method cuts down on memory because There's only one image to load, no swaping between variables or storing textures localy to each mesh.
        This idea was borrowed from Quake 1 (ID Tech engine 2, and onward)."""
    def __init__(self,filename):
        self.image = pygame.image.load(filename).convert_alpha()
        self.width = self.image.get_width() - 1
        self.height = self.image.get_height() - 1
        self.surface = pygame.Surface((self.width+1,self.height+1))
        self.surface.blit(self.image,(0,0))
        self.surface = pygame.transform.flip(self.surface,False,True)

def calcLighting(palette, colour, normal, light_vect):
    """ This function is used to calculate flat shading from lighting vector.
        The palatte can be any length but must be ordered from dark to light.
        New colour is assinged by blending the palette with the specified colour. """
    if len(colour) > 3:
        colourAlpha = colour[3]
    else:
        colourAlpha = 255
    index = round((pygame.math.Vector3.dot(light_vect,normal) + 2) * 2) % len(palette)
    return ((palette[index][0] + (colour[0] * 3)) // 4), ((palette[index][1] + (colour[1] * 3)) // 4), ((palette[index][2] + (colour[2] * 3)) // 4), colourAlpha

# ===================Rotation Position and Scale======================#

def x_rot(points, angle):
    """ Rotates points around the X axis. """
    for point in points:
        for i in range(3):
            y, z = point[i][1], point[i][2]
            y1 = (y * math.cos(angle)) - (z * math.sin(angle))
            z1 = (z * math.cos(angle)) + (y * math.sin(angle))
            point[i].update(point[i][0], y1, z1)
    return points

def y_rot(points, angle):
    """ Rotates points around the Y axis. """
    for point in points:
        for i in range(3):
            x, z = point[i][0], point[i][2]
            x1 = (x * math.cos(angle)) - (z * math.sin(angle))
            z1 = (z * math.cos(angle)) + (x * math.sin(angle))
            point[i].update(x1, point[i][1], z1)
    return points

def z_rot(points, angle):
    """ Rotates points around the Z axis. """
    for point in points:
        for i in range(3):
            x, y = point[i][0], point[i][1]
            x1 = (x * math.cos(angle)) - (y * math.sin(angle))
            y1 = (y * math.cos(angle)) + (x * math.sin(angle))
            point[i].update(x1, y1, point[i][2])
    return points

def xyz_scale(points, scale):
    """ This function scales the points """
    new_points = []
    for point in points:
        new_point = (pygame.math.Vector3(point[0][0] * scale[0], point[0][1] * scale[1], point[0][2] * scale[0]),
                     pygame.math.Vector3(point[1][0] * scale[0], point[1][1] * scale[1], point[1][2] * scale[1]),
                     pygame.math.Vector3(point[2][0] * scale[0], point[2][1] * scale[1], point[2][2] * scale[2]),point[3],)
        new_points.append(new_point)
    return new_points

def xyz_move(points, pos):
    """ This function changes the position of the points """
    new_points = []
    for point in points:
        new_point = (pygame.math.Vector3(point[0][0] - pos[0], point[0][1] - pos[1], point[0][2] - pos[2]),
                     pygame.math.Vector3(point[1][0] - pos[0], point[1][1] - pos[1], point[1][2] - pos[2]),
                     pygame.math.Vector3(point[2][0] - pos[0], point[2][1] - pos[1], point[2][2] - pos[2]),point[3],)
        new_points.append(new_point)
    return new_points

def get_normal(face):
    """ This function generates a normal vector from a given face """

    a, b = face[1] - face[0], face[2] - face[0]
    normal = pygame.math.Vector3((a[1] * b[2]) - (a[2] * b[1]),
                                 (a[2] * b[0]) - (a[0] * b[2]),
                                 (a[0] * b[1]) - (a[1] * b[0]))
    if normal != (0,0,0):
        normal = normal.normalize()
    return normal

# ====================================================================#

class Plane():
    """ This class defines a basic 3d plane as defined by a 3 points. """
    def __init__(self,point):
            self.n = get_normal(point)
            self.v1, self.v2, self.v3 = point[0], point[1], point[2]
            self.p = (point[0]+point[1]+point[2])/3
            self.d = (pygame.math.Vector3(self.v1 + self.v2 + self.v3) / 3).dot(self.n)

    def pointToPlane(self, point):
        """ This function calculates the point-to-plane distance from any given point. """
        return(self.n.dot(point)-self.d)

    def vectorPlaneIntersect(self, start, end):
        """ This function calculates the intersection point of a ray and a plane """
        ad = start.dot(self.n)
        t = (self.d - ad) / ((end.dot(self.n)) - ad)
        ray = end - start
        intersect = (ray * t) + start
        return intersect

class Mesh():
    """ The Mesh class is a generic container for 3d model information such as, vertecies, faces, position, rotation, scale and colour."""
    def __init__(self, filename, pos, rot, scale, lighting, dynamic, enabled, colour, rendertype):
        self.colour = colour
        self.points = LoadObj(filename, pos, rot, scale, COLOUR, self.colour, rendertype)
        self.rot = rot              # object rotation
        self.pos = pos              # object position
        self.scale = scale          # object scale

        self.enabled = enabled      # internal variable to store if the object should be drawn or not.
        self.realtime = lighting    # does the object use real-time or baked lighting
        self.dynamic = dynamic      # does the object need to rotate or is it fixed in place

    def Update(self):
        """ This function updates the position, rotation and scale of the mesh. This transformation is perminate and changes the origin aswell.
            Set the position, rotation and scale before calling this function."""
        self.points = x_rot(self.points,self.rot[0])
        self.points = y_rot(self.points,self.rot[1])
        self.points = z_rot(self.points,self.rot[2])
        self.points = xyz_scale(self.points,self.pos)
        self.points = xyz_move(self.points,self.pos)

# =======================Collision Detection==========================#

class MeshCollider():
    """ This class stores all the relevent information for a mesh collider, along with methods to collide with objects. """

    def __init__(self, filename, pos, rot, scale, gap, enabled):

        self.points = LoadObj(filename, pos, rot, scale, None, None, None)
        self.planes = ()
        self.enabled = enabled

        newmesh = ()
        for i in range(len(self.points)):

            point = self.points[i]

            # Generate plane for each face so speed up runtime exicution:
            plane = Plane(point)
            self.planes = self.planes + (plane,)
            a, b, c = point[0], point[1], point[2]

            # Generate list of points that form the face:
            newpoints = (a, b, c,)
            ystep = int(a.distance_to(c) / gap)

            for y in range(ystep):
                ylerp = (y / ystep)

                cA = a.lerp(c, ylerp)
                cB = b.lerp(c, ylerp)

                # Get the distance betweem the newly generated points from previous lerp operation:
                xstep = int(cA.distance_to(cB) / gap)

                for x in range(xstep):
                    xlerp = (x / xstep)
                    newpoint = cA.lerp(cB, xlerp)
                    newpoints = newpoints + (newpoint,)

            # add new points to temporary container.
            newmesh = newmesh + (newpoints,)

        # Overwrite old mesh data with the new mesh
        self.points = newmesh

    def sphereIntersect(self, pos, rad):
        """ This function handles checking for intersections with a sphere collider."""
        # this method is functionally the same as the other method that unintersects the sphere.
        # this one is more efficient for triggers / non-colliding colliders.
        radSqr = rad * rad
        for i in range(len(self.points)):
            ptpdist = self.planes[i].pointToPlane(pos)
            if rad > ptpdist > -rad:
                for point in self.points[i]:
                    if ((point - pos) * (point - pos)) < radSqr:
                        return True
        return False

    def sphereCollideCheck(self, pos, rad):
        """ This function handles un-intersecting a sphere collider with a mesh."""

        # Δshift     -       Vector3 that will un-intersect the player from all of the faces collided wit
        # collisions -       number of collisions detected. used when calculating Δshift
        # ptpdist    -       stores point-to-plane distance.
        
        Δshift = pygame.math.Vector3(0, 0, 0)
        collisions = 0
        radSqr = rad * rad
        for i in range(len(self.points)):
            ptpdist = self.planes[i].pointToPlane(pos)
            if rad > ptpdist > -rad:
                for point in self.points[i]:
                    if ((point - pos) * (point - pos)) < radSqr:
                        collisions += 1
                        if self.planes[i].n[1] > 0.6:
                            Δshift += pygame.math.Vector3(0, rad - ptpdist, 0)
                        else:
                            Δshift += pygame.math.Vector3(self.planes[i].n * (rad - ptpdist))
                        break
        if collisions != 0:
            Δshift = Δshift / collisions
        return Δshift, collisions

class Trigger():
    """ This class stores all the information associated with a trigger object. Used for updating verious aspects of the game."""
    def __init__(self,filename,pos,rot,scale,gap,keyword,enabled,mod):
        # Variables:
        # self.mesh      -       mesh used for collision detection
        # self.keyword   -       String that defines what the trigger does, for example, "ENABLE" or "INTERACT".
        # self.enabled   -       bool for if the trigger is active.
        # self.mod       -       arbitrary list containing moddifiers. Used to set flags based on the keyword.

        self.mesh = MeshCollider(filename, pos, rot, scale, gap, True)
        self.keyword = keyword
        self.enabled = enabled
        self.mod = mod

# ===========================LOAD OBJECT==============================#

def LoadObj(filename, pos, rot, scale, palette, colour, rendertype):
    """ This function loads a standard .obj file and returns a list of vertices in expanded form
        
        denoting vertex: start line with the letter 'v', then, list the x,y,z values for the point.
        denoting face:   start line with the letter 'f', then, list the index of 3 vertices that form a face.
        *All other notation is ignored, normals are planned for a later version.
        
        example:
        o ship
        v 1.000000 1.000000 2.000000
        v 2.000000 4.000000 6.000000
        v 4.000000 -1.000000 -4.000000 ...
        f 1 2 3 ..."""

    # Variables:
    # verts      -       stores the list of verticies
    # faces      -       stores the list of faces
    # objfile    -       stores the whole file
    # temp_ls    -       list of lists containing vertices of a single face

    verts = []
    faces = []
    texps = []
    expVerts = []
    expTex = []

    objfile = open(filename, "r")

    # Getting object data:
    for lines in objfile:

        temp_ls = []
        line = lines.strip("\n")
        line = line.split()

        # if vertex
        if line[0] == 'v':
            verts.append(pygame.math.Vector3(float(line[1]),float(line[2]),float(line[3])))

        if rendertype == 3:
            # if texture coordinate
            if line[0] == 'vt':
                texps.append(pygame.math.Vector2(float(line[1]),float(line[2])))
                # if face with texture data
            elif line[0] == 'f':
                face1, face2, face3 = line[1].split('/'), line[2].split('/'), line[3].split('/')
                faces.append((int(face1[0]) - 1, int(face2[0]) - 1, int(face3[0]) - 1, int(face1[1]) - 1, int(face2[1]) - 1, int(face3[1]) - 1))
        else:
            if line[0] == 'f':
                faces.append((int(line[1]) - 1, int(line[2]) - 1, int(line[3]) - 1,))

    # Generate faces from face indices
    for face in faces:

        # Get normal
        f1, f2, f3 = face[0], face[1], face[2]
        normal = get_normal((verts[face[0]], verts[face[1]], verts[face[2]],))

        # Get Lighting
        if colour is not None:  # If part has a colour
            newColour = calcLighting(palette, colour, normal, pygame.math.Vector3(1, 1, 1))
        else:
            rendertype, newColour = None, None

        if rendertype == 3:
           newColour = (texps[face[3]],texps[face[4]],texps[face[5]])

        expVerts.append([verts[face[0]],verts[face[1]],verts[face[2]],[normal,rendertype,newColour]])

    # Rotate, Scale, Shift
    expVerts = x_rot(expVerts, rot[0])
    expVerts = y_rot(expVerts, rot[1])
    expVerts = z_rot(expVerts, rot[2])
    expVerts = xyz_scale(expVerts, scale)
    expVerts = xyz_move(expVerts, pos)
    return expVerts


