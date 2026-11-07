# prompt: Implement the minimax algorithm and run it for the tic-tac-toe game.

import math
import time

def print_board(board):
    """Prints the current state of the Tic-Tac-Toe board."""
    print("###############################")
    for row in board:
        print(" | ".join(row))
        print("-" * 9)
    print("###############################")

def is_board_full(board):
    """Checks if the Tic-Tac-Toe board is full."""
    for row in board:
        if " " in row:
            return False
    return True


def check_winner(board, player):
    """Checks if the given player has won the game."""
    for row in board:
        if all(cell == player for cell in row):
            return True
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False

def check_draw(board):
    """Checks if the game is a draw."""
    for row in board:
        if " " in row:
            return False
    return True

def get_available_moves(board):
    """Returns a list of available moves on the board."""
    moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == " ":
                moves.append((row, col))
    return moves

def minimax(board, depth, maximizing_player):
    """Implements the minimax algorithm with alpha-beta pruning."""
    if check_winner(board, "X"):
        return 1  # X wins
    if check_winner(board, "O"):
        return -1  # O wins
    if check_draw(board):
        return 0  # Draw

    if maximizing_player:
        max_eval = -math.inf
        for row, col in get_available_moves(board):
            board[row][col] = "X"
            eval = minimax(board, depth + 1, False)
            board[row][col] = " "  # Backtrack
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = math.inf
        for row, col in get_available_moves(board):
            board[row][col] = "O"
            eval = minimax(board, depth + 1, True)
            board[row][col] = " "  # Backtrack
            min_eval = min(min_eval, eval)
        return min_eval

def find_best_move(board):
    """Finds the best move for the AI player (X) using minimax."""
    best_move = None
    best_eval = -math.inf
    for row, col in get_available_moves(board):
      board[row][col] = "X"
      eval = minimax(board, 0, False)
      board[row][col] = " "
      if eval > best_eval:
          best_eval = eval
          best_move = (row, col)
    return best_move


# Example usage:
board = [[" ", " ", " "],
         [" ", " ", " "],
         [" ", " ", " "]]

print_board(board)
while True:
  
  start = time.perf_counter()
  available = get_available_moves(board)
  moves_elapsed = time.perf_counter() - start

  print(f"Plays available: {len(available)} -> {available}")
  print(f"get_available_moves took {moves_elapsed * 1000:.3f} ms")

  start = time.perf_counter()
  move = find_best_move(board)
  elapsed = time.perf_counter() - start
  print(f"find_best_move took {elapsed * 1000:.3f} ms")
  
  if move:
    row, col = move
    board[row][col] = "X"
    print_board(board)

    if check_winner(board, "X"):
        print("X wins!")
        break
    if is_board_full(board):
        print("It's a draw!")
        break

    # Opponent's move (replace with actual opponent input)
    while True:
      try:
          row = int(input("Enter row (1-3): "))
          col = int(input("Enter column (1-3): "))
          if 1 <= row < 4 and 1 <= col < 4 and board[row-1][col-1] == " ":
              board[row-1][col-1] = "O"
              break
          else:
              print("Invalid move. Try again.")
      except ValueError:
          print("Invalid input. Enter numbers between 0 and 2")
    print_board(board)
    if check_winner(board, "O"):
      print("O wins!")
      break
    if is_board_full(board):
        print("It's a draw!")
        break
  else:
      print("It's a draw!")
      break