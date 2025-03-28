import pygame
import random
import numpy as np
import collections


# Define game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CELL_SIZE = 10
BG_COLOR = (255, 255, 255)
PLAYER_COLOR = (0, 255, 0)
ENEMY_COLOR = (255, 0, 0)
ANIMAL_COLOR = (255, 192, 203)
PET_COLOR = (255, 165, 0)  # Orange color
FOOD_COLOR = (0, 0, 255)
NUM_ENEMIES = 31
NUM_FOOD = 10
NUM_ANIMALS = 50
VISION_RANGE = 4


dirty_cells = []

# Define game classes
class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = BG_COLOR
        self.pollution = 0
        self.entity = None

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))


class World:
    def __init__(self):
        # Generate cells
        self.cells = generate_cells()

        # Generate player
        self.player = generate_player(self.cells)

        # Generate enemies
        self.enemies = generate_enemies(self.cells, NUM_ENEMIES)

        # Generate food
        self.food = generate_food(self.cells, NUM_FOOD)

        # Generate animals
        self.animals = generate_animals(self.cells, NUM_ANIMALS)

    def update(self):
        # Update game state

        # Move pets
        for pet in self.player.pets:
            pet.move(self.cells)

        for enemy in self.enemies:
            # Move enemies randomly
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            enemy.move(dx, dy, self.cells)

        for animal in self.animals:
            directions = {
                'up': (0, -1),
                'down': (0, 1),
                'left': (-1, 0),
                'right': (1, 0)
            }

            avg_pollutions = {}

            for direction, (dx, dy) in directions.items():
                pollutions = []
                for step in range(1, VISION_RANGE + 1):
                    for offset in range(-VISION_RANGE, VISION_RANGE + 1):
                        if direction in ['up', 'down']:
                            check_x, check_y = animal.x + offset, animal.y + dy * step
                        else:  # left or right
                            check_x, check_y = animal.x + dx * step, animal.y + offset

                        pollution = self.get_cell_pollution(check_x, check_y)
                        if not np.isnan(pollution):
                            pollutions.append(pollution)

                # If no valid cells, set pollution high to avoid this direction
                avg_pollutions[direction] = np.mean(pollutions) if pollutions else np.inf

            # Choose the direction with the lowest average pollution
            best_direction = min(avg_pollutions, key=avg_pollutions.get)
            dx, dy = directions[best_direction]

            animal.move(dx, dy, self.cells)


        for cell in dirty_cells:
            color_val = 255 - cell.pollution
            cell.color = (color_val, color_val, color_val)
            cell.entity = None
        
        dirty_cells.clear()

    def get_cell_pollution(self,x,y):
        if x < 0 or x >= SCREEN_WIDTH // CELL_SIZE:
            return np.NaN
        if y < 0 or y >= SCREEN_HEIGHT // CELL_SIZE:
            return np.NaN

        return self.cells[(x) + (y) * (SCREEN_WIDTH // CELL_SIZE)].pollution

class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = None
    

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = PLAYER_COLOR
        self.health = 100
        self.food_eaten = 0
        self.pets = []

    def move(self, dx, dy, cells):
        new_x, new_y = self.x + dx, self.y + dy

        if new_x < 0 or new_x >= SCREEN_WIDTH // CELL_SIZE or new_y < 0 or new_y >= SCREEN_HEIGHT // CELL_SIZE:
            return False
        
        new_cell = cells[new_x + new_y * (SCREEN_WIDTH // CELL_SIZE)]

        if isinstance(new_cell.entity, Enemy):
            self.health -= 10
            if self.health <= 0:
                return False

        if isinstance(new_cell.entity, Food):
            self.health += 10
            self.food_eaten += 1
            generate_food(cells, 1)

            if self.food_eaten % 5 == 0:
                self.spawn_pets(cells)

        if new_cell.entity is not None and not isinstance(new_cell.entity, Food):
            return False

        dirty_cells.append(cells[self.x + self.y * (SCREEN_WIDTH // CELL_SIZE)])

        self.x, self.y = new_x, new_y
        new_cell.color = self.color
        new_cell.entity = self
        new_cell.pollution = 0

        return True

    def spawn_pets(self, cells):
        pets_spawned = 0
        while pets_spawned < 2:
            cell = random.choice(cells)
            if cell.color == BG_COLOR and cell.entity is None:
                pet = Pet(cell.x, cell.y, self)
                self.pets.append(pet)
                cell.color = PET_COLOR
                cell.entity = pet
                pets_spawned += 1

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = ENEMY_COLOR
    
    def move(self, dx, dy, cells):

        # Check if move is valid
        new_x = self.x + dx
        new_y = self.y + dy
        if new_x < 0 or new_x >= SCREEN_WIDTH // CELL_SIZE:
            return False
        if new_y < 0 or new_y >= SCREEN_HEIGHT // CELL_SIZE:
            return False
        
        old_cell = cells[self.x + self.y * (SCREEN_WIDTH // CELL_SIZE)]
        new_cell = cells[new_x + new_y * (SCREEN_WIDTH // CELL_SIZE)]

        if isinstance(new_cell.entity,Player):
            return False
        if isinstance(new_cell.entity,Food):
            return False
        if isinstance(new_cell.entity,Enemy):
            return False
        if isinstance(new_cell.entity,Animal):
            return False

        #add pollution
        old_cell.pollution += 1

        #track past paths
        dirty_cells.append(old_cell)

        # Move entity
        self.x = new_x
        self.y = new_y
        new_cell.color = self.color
        new_cell.entity = self
        return True

class Food(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = FOOD_COLOR

class Animal(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = ANIMAL_COLOR
    
    def move(self, dx, dy, cells):

        # Check if move is valid
        new_x = self.x + dx
        new_y = self.y + dy
        if new_x < 0 or new_x >= SCREEN_WIDTH // CELL_SIZE:
            return False
        if new_y < 0 or new_y >= SCREEN_HEIGHT // CELL_SIZE:
            return False
        
        old_cell = cells[self.x + self.y * (SCREEN_WIDTH // CELL_SIZE)]
        new_cell = cells[new_x + new_y * (SCREEN_WIDTH // CELL_SIZE)]

        if isinstance(new_cell.entity,Player):
            return False
        if isinstance(new_cell.entity,Food):
            return False
        if isinstance(new_cell.entity,Enemy):
            return False
        if isinstance(new_cell.entity,Animal):
            return False

        #track past paths
        dirty_cells.append(old_cell)

        # Move entity
        self.x = new_x
        self.y = new_y
        new_cell.color = self.color
        new_cell.entity = self
        return True

class Pet(Entity):
    def __init__(self, x, y, owner):
        super().__init__(x, y)
        self.color = PET_COLOR
        self.owner = owner

    def move(self, cells):
        max_distance = 5
        attempts = 0
        while attempts < 10:
            dx, dy = random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
            new_x, new_y = self.x + dx, self.y + dy
            distance_to_owner = abs(new_x - self.owner.x) + abs(new_y - self.owner.y)

            if (0 <= new_x < SCREEN_WIDTH // CELL_SIZE and
                0 <= new_y < SCREEN_HEIGHT // CELL_SIZE and
                distance_to_owner <= max_distance):

                new_cell = cells[new_x + new_y * (SCREEN_WIDTH // CELL_SIZE)]

                # Avoid collisions with all entities
                if new_cell.entity is not None:
                    attempts += 1
                    continue

                old_cell = cells[self.x + self.y * (SCREEN_WIDTH // CELL_SIZE)]
                dirty_cells.append(old_cell)

                self.x, self.y = new_x, new_y
                new_cell.color = self.color
                new_cell.entity = self
                new_cell.pollution = 0
                break
            attempts += 1

# Define game functions
def generate_cells():
    cells = []
    for y in range(SCREEN_HEIGHT // CELL_SIZE):
        for x in range(SCREEN_WIDTH // CELL_SIZE):
            cell = Cell(x, y)
            cells.append(cell)
    return cells

def generate_player(cells):
    while True:
        cell = random.choice(cells)
        if cell.color == BG_COLOR:
            player = Player(cell.x, cell.y)
            cell.color = PLAYER_COLOR
            cell.entity = player
            return player

def generate_enemies(cells, num_enemies):
    enemies = []
    for i in range(num_enemies):
        while True:
            cell = random.choice(cells)
            if cell.color == BG_COLOR:
                enemy = Enemy(cell.x, cell.y)
                enemies.append(enemy)
                cell.color = ENEMY_COLOR
                cell.entity = enemy
                break
    return enemies

def generate_food(cells, num_food):
    food = []
    for i in range(num_food):
        while True:
            cell = random.choice(cells)
            if cell.entity == None:
                food_item = Food(cell.x, cell.y)
                food.append(food_item)
                cell.color = FOOD_COLOR
                cell.entity = food_item
                break
    return food

def generate_animals(cells, num_animals):
    animals = []
    for i in range(num_animals):
        while True:
            cell = random.choice(cells)
            if cell.color == BG_COLOR:
                animal = Animal(cell.x, cell.y)
                animals.append(animal)
                cell.color = ANIMAL_COLOR
                cell.entity = animal
                break
    return animals

def draw_cells(cells, surface):
    for cell in cells:
        cell.draw(surface)

def main():
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Save the Environment")

    world = World()

    green = (0, 255, 0)
    blue = (0, 0, 128)

    # create a font object.
    # 1st parameter is the font file
    # which is present in pygame.
    # 2nd parameter is size of the font
    font = pygame.font.Font(pygame.font.get_default_font(), 12)

    # create a text surface object,
    # on which text is drawn on it.
    text = font.render('Health', True, (0, 0, 0))
    
    # Game loop
    running = True
    clock = pygame.time.Clock()
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    world.player.move(0, -1, world.cells)
                elif event.key == pygame.K_DOWN:
                    world.player.move(0, 1, world.cells)
                elif event.key == pygame.K_LEFT:
                    world.player.move(-1, 0, world.cells)
                elif event.key == pygame.K_RIGHT:
                    world.player.move(1, 0, world.cells)

        # Move entities
        world.update()

        # Draw screen
        screen.fill(BG_COLOR)
        draw_cells(world.cells, screen)
        pygame.display.flip()

        screen.blit(text, (0,0))

        # Limit frame rate
        clock.tick(10)

    # Quit game
    pygame.quit()

if __name__ == "__main__":
    main()