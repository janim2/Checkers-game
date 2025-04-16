import pygame
import sys

# Constants
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
CROWN = pygame.transform.scale(pygame.image.load('crown.png'), (45, 25))
FPS = 60
MENU_FONT_SIZE = 50
BUTTON_COLOR = (50, 50, 50)
HOVER_COLOR = (100, 100, 100)
TEXT_COLOR = (255, 255, 255)

class Piece:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()

    def calc_pos(self):
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2

    def make_king(self):
        self.king = True

    def draw(self, win):
        radius = SQUARE_SIZE // 2 - 15
        pygame.draw.circle(win, self.color, (self.x, self.y), radius)
        if self.king:
            win.blit(CROWN, (self.x - CROWN.get_width()//2, self.y - CROWN.get_height()//2))

    def move(self, row, col):
        self.row = row
        self.col = col
        self.calc_pos()

class Board:
    def __init__(self):
        self.board = []
        self.selected_piece = None
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.game = None
        self.create_board()

    def create_board(self):
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if col % 2 == ((row + 1) % 2):
                    if row < 3:
                        self.board[row].append(Piece(row, col, WHITE))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, RED))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def draw(self, win):
        self.draw_squares(win)
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)

    def draw_squares(self, win):
        win.fill(BLACK)
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 0:
                    pygame.draw.rect(win, GREY, (row*SQUARE_SIZE, col*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    def get_piece(self, row, col):
        return self.board[row][col]

    def move(self, piece, row, col):
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
        
        if row == ROWS - 1 or row == 0:
            if not piece.king:
                piece.make_king()
                if piece.color == RED:
                    self.red_kings += 1
                else:
                    self.white_kings += 1
                self.game.award_king_bonus(piece)

    def get_valid_moves(self, piece):
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        
        if piece.color == RED or piece.king:
            moves.update(self._traverse_left(row -1, max(row-3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row -1, max(row-3, -1), -1, piece.color, right))
        if piece.color == WHITE or piece.king:
            moves.update(self._traverse_left(row +1, min(row+3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row +1, min(row+3, ROWS), 1, piece.color, right))
    
        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            
            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last
                
                if last:
                    if step == -1:
                        row = max(r-3, 0)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self._traverse_left(r+step, row, step, color, left-1, skipped=last))
                    moves.update(self._traverse_right(r+step, row, step, color, left+1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            left -= 1
        
        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            
            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last
                
                if last:
                    if step == -1:
                        row = max(r-3, 0)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self._traverse_left(r+step, row, step, color, right-1, skipped=last))
                    moves.update(self._traverse_right(r+step, row, step, color, right+1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            right += 1
        
        return moves

    def remove(self, pieces):
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
            if piece.color == RED:
                self.red_left -= 1
            else:
                self.white_left -= 1
            self.game.remove_piece(piece)

class Button:
    def __init__(self, text, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont("comicsans", 40)
        self.base_color = BUTTON_COLOR
        self.hover_color = HOVER_COLOR
        self.current_color = self.base_color

    def draw(self, win):
        pygame.draw.rect(win, self.current_color, self.rect)
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        win.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

class Game:
    def __init__(self, win):
        self.states = ["MENU", "PLAYING", "GAME_OVER"]
        self.current_state = "MENU"
        self.winner_color = None
        self.red_score = 0
        self.white_score = 0
        self.piece_value = 10
        self.king_bonus = 5
        self.win_bonus = 100
        self._init(win)

    def _init(self, win):
        self.win = win
        self.selected = None
        self.board = Board()
        self.board.game = self
        self.turn = RED
        self.valid_moves = {}
        self.red_score = 0
        self.white_score = 0
        self.menu_button = Button("Start Game", WIDTH//2-100, HEIGHT//2-25, 200, 50)
        self.restart_button = Button("Play Again", WIDTH//2-100, HEIGHT//2+50, 200, 50)
        self.quit_button = Button("Quit", WIDTH//2-100, HEIGHT//2+125, 200, 50)
        self.font = pygame.font.SysFont("comicsans", 30)

    def draw_turn_indicator(self):
        turn_text = "Red's Turn" if self.turn == RED else "White's Turn"
        score_text = f"Red: {self.red_score}  White: {self.white_score}"
        turn_surface = self.font.render(turn_text, True, TEXT_COLOR)
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.win.blit(turn_surface, (WIDTH - turn_surface.get_width() - 20, 20))
        self.win.blit(score_surface, (WIDTH - score_surface.get_width() - 20, 60))

    def draw_menu(self):
        self.win.fill(BLACK)
        title_font = pygame.font.SysFont("comicsans", MENU_FONT_SIZE)
        title_text = title_font.render("CHECKERS", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//4))
        self.win.blit(title_text, title_rect)
        self.menu_button.draw(self.win)
        self.quit_button.draw(self.win)

    def draw_game_over(self):
        self.win.fill(BLACK)
        result_font = pygame.font.SysFont("comicsans", MENU_FONT_SIZE)
        result_text = result_font.render(f"{self.winner_color} WINS!", True, TEXT_COLOR)
        result_rect = result_text.get_rect(center=(WIDTH//2, HEIGHT//4))
        self.win.blit(result_text, result_rect)
        self.restart_button.draw(self.win)
        self.quit_button.draw(self.win)

    def update(self):
        if self.current_state == "PLAYING":
            self.win.fill(BLACK)
            self.board.draw(self.win)
            self.draw_valid_moves(self.valid_moves)
            self.draw_turn_indicator()
        elif self.current_state == "MENU":
            self.draw_menu()
        elif self.current_state == "GAME_OVER":
            self.draw_game_over()
            
        pygame.display.update()

    def handle_click(self, pos):
        if self.current_state == "MENU":
            if self.menu_button.is_hovered(pos):
                self.current_state = "PLAYING"
            elif self.quit_button.is_hovered(pos):
                pygame.quit()
                sys.exit()
        elif self.current_state == "GAME_OVER":
            if self.restart_button.is_hovered(pos):
                self._init(self.win)
                self.current_state = "PLAYING"
            elif self.quit_button.is_hovered(pos):
                pygame.quit()
                sys.exit()
        elif self.current_state == "PLAYING":
            col = pos[0] // SQUARE_SIZE
            row = pos[1] // SQUARE_SIZE
            if row < ROWS and col < COLS:
                self.select(row, col)

    def winner(self):
        if self.board.red_left <= 0:
            self.winner_color = "WHITE"
            self.white_score += self.win_bonus
            return True
        elif self.board.white_left <= 0:
            self.winner_color = "RED"
            self.red_score += self.win_bonus
            return True
        return False

    def select(self, row, col):
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        
        piece = self.board.get_piece(row, col)
        if piece != 0 and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
            
        return False

    def _move(self, row, col):
        piece = self.board.get_piece(row, col)
        if self.selected and piece == 0 and (row, col) in self.valid_moves:
            # Store potential skipped pieces before moving
            skipped = self.valid_moves.get((row, col), [])
            self.board.move(self.selected, row, col)
            
            if skipped:
                self.board.remove(skipped)
                # Check for additional captures
                new_moves = self.board.get_valid_moves(self.selected)
                new_captures = {move: skips for move, skips in new_moves.items() if skips}
                
                if new_captures:
                    self.valid_moves = new_captures
                    return True  # Stay in move mode for same piece
                
            # Only change turn if no more captures
            self.change_turn()
            return True
            
        return False

    def change_turn(self):
        self.valid_moves = {}
        self.turn = WHITE if self.turn == RED else RED

    def draw_valid_moves(self, moves):
        for move in moves:
            row, col = move
            pygame.draw.circle(self.win, BLUE, (col * SQUARE_SIZE + SQUARE_SIZE//2, row * SQUARE_SIZE + SQUARE_SIZE//2), 15)

    def get_board(self):
        return self.board

    def ai_move(self, board):
        self.board = board
        self.change_turn()

    def remove_piece(self, piece):
        if piece.color == RED:
            self.white_score += self.piece_value
        else:
            self.red_score += self.piece_value

    def award_king_bonus(self, piece):
        if piece.color == RED:
            self.red_score += self.king_bonus
        else:
            self.white_score += self.king_bonus

def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers")
    game = Game(win)
    clock = pygame.time.Clock()

    while True:
        clock.tick(FPS)
        
        if game.current_state == "PLAYING" and game.winner():
            game.current_state = "GAME_OVER"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                game.handle_click(pos)
            if event.type == pygame.MOUSEMOTION and game.current_state != "PLAYING":
                pos = pygame.mouse.get_pos()
                game.menu_button.current_color = game.menu_button.hover_color if game.menu_button.is_hovered(pos) else game.menu_button.base_color
                game.quit_button.current_color = game.quit_button.hover_color if game.quit_button.is_hovered(pos) else game.quit_button.base_color
                if game.current_state == "GAME_OVER":
                    game.restart_button.current_color = game.restart_button.hover_color if game.restart_button.is_hovered(pos) else game.restart_button.base_color

        game.update()

if __name__ == "__main__":
    main() 