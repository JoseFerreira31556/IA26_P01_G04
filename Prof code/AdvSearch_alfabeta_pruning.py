# prompt: Implement the minimax algorithm and run it for the tic-tac-toe game.
#
# v2 of AdvSearch.py. Same game, two searches side by side:
#   minimax             - the plain algorithm, explores the whole game tree
#   minimax_alpha_beta  - the same algorithm with alpha-beta pruning
# Both count the nodes they visit, so the cost of each one can be compared.

import math
import time

AI = "X"
HUMAN = "O"

# Nodes visited by the last search. find_best_move resets it before searching.
nodes_visited = 0


def empty_board():
    """Returns a new empty Tic-Tac-Toe board."""
    return [[" ", " ", " "],
            [" ", " ", " "],
            [" ", " ", " "]]

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

def get_available_moves(board):
    """Returns a list of available moves on the board."""
    moves = []
    for row in range(3):
        for col in range(3):
            if board[row][col] == " ":
                moves.append((row, col))
    return moves

def evaluate(board, depth):
    """Score of a terminal board from X's point of view, or None if the game is
    still open. Deeper outcomes are worth less, so X goes for the quickest win
    and the slowest defeat instead of any win at any depth."""
    if check_winner(board, AI):
        return 10 - depth
    if check_winner(board, HUMAN):
        return depth - 10
    if is_board_full(board):
        return 0
    return None

def minimax(board, depth, maximizing_player):
    """Plain minimax: every node of the game tree is visited."""
    global nodes_visited
    nodes_visited += 1

    score = evaluate(board, depth)
    if score is not None:
        return score

    if maximizing_player:
        best = -math.inf
        for row, col in get_available_moves(board):
            board[row][col] = AI
            best = max(best, minimax(board, depth + 1, False))
            board[row][col] = " "  # Backtrack
        return best
    else:
        best = math.inf
        for row, col in get_available_moves(board):
            board[row][col] = HUMAN
            best = min(best, minimax(board, depth + 1, True))
            board[row][col] = " "  # Backtrack
        return best

def minimax_alpha_beta(board, depth, maximizing_player,
                       alpha=-math.inf, beta=math.inf):
    
    global nodes_visited
    nodes_visited += 1

    score = evaluate(board, depth)
    if score is not None:
        return score

    if maximizing_player:
        best = -math.inf
        for row, col in get_available_moves(board):
            board[row][col] = AI
            best = max(best, minimax_alpha_beta(board, depth + 1, False,
                                                alpha, beta))
            board[row][col] = " "  # Backtrack
            alpha = max(alpha, best)
            if beta <= alpha:
                break  # O would never let the game reach this branch
        return best
    else:
        best = math.inf
        for row, col in get_available_moves(board):
            board[row][col] = HUMAN
            best = min(best, minimax_alpha_beta(board, depth + 1, True,
                                                alpha, beta))
            board[row][col] = " "  # Backtrack
            beta = min(beta, best)
            if beta <= alpha:
                break  # X would never let the game reach this branch
        return best

def find_best_move(board, search=minimax_alpha_beta):
    """Finds the best move for the AI player (X).

    search is the function used to score each candidate move, so this same root
    loop serves both minimax and minimax_alpha_beta.
    Returns (best_move, nodes_visited, elapsed_seconds)."""
    global nodes_visited
    nodes_visited = 0

    best_move = None
    best_eval = -math.inf
    start = time.perf_counter()
    for row, col in get_available_moves(board):
        board[row][col] = AI
        value = search(board, 1, False)  # depth 1: this move is already played
        board[row][col] = " "
        if value > best_eval:
            best_eval = value
            best_move = (row, col)
    elapsed = time.perf_counter() - start
    return best_move, nodes_visited, elapsed

def compare_searches(board=None):
    """Runs both searches on the same board and reports the cost of each."""
    board = board if board else empty_board()

    start = time.perf_counter()
    available = get_available_moves(board)
    moves_elapsed = time.perf_counter() - start
    print(f"Plays available: {len(available)} -> {available}")
    print(f"get_available_moves took {moves_elapsed * 1000:.3f} ms\n")

    results = {}
    for search in (minimax, minimax_alpha_beta):
        move, nodes, elapsed = find_best_move(board, search)
        results[search.__name__] = (move, nodes, elapsed)
        print(f"{search.__name__:<20} move={move}  "
              f"nodes={nodes:>7}  time={elapsed * 1000:9.3f} ms")

    plain = results["minimax"]
    pruned = results["minimax_alpha_beta"]
    print(f"\nalpha-beta visited {plain[1] / pruned[1]:.1f}x fewer nodes and "
          f"was {plain[2] / pruned[2]:.1f}x faster "
          f"(same move: {plain[0] == pruned[0]})\n")

def ask_human_move(board):
    """Asks the human player (O) for a legal move. Returns 0-based (row, col)."""
    while True:
        try:
            row = int(input("Enter row (1-3): "))
            col = int(input("Enter column (1-3): "))
        except ValueError:
            print("Invalid input. Enter numbers between 1 and 3.")
            continue
        if 1 <= row <= 3 and 1 <= col <= 3 and board[row - 1][col - 1] == " ":
            return row - 1, col - 1
        print("Invalid move. Try again.")

def play(search=minimax_alpha_beta):
    """Plays a full game: the AI is X and moves first, the human is O."""
    board = empty_board()
    print_board(board)

    while True:
        start = time.perf_counter()
        available = get_available_moves(board)
        moves_elapsed = time.perf_counter() - start
        print(f"Plays available: {len(available)} -> {available}")
        print(f"get_available_moves took {moves_elapsed * 1000:.3f} ms")

        move, nodes, elapsed = find_best_move(board, search)
        print(f"{search.__name__} visited {nodes} nodes "
              f"in {elapsed * 1000:.3f} ms")
        if move is None:
            print("It's a draw!")
            break

        row, col = move
        board[row][col] = AI
        print_board(board)
        if check_winner(board, AI):
            print("X wins!")
            break
        if is_board_full(board):
            print("It's a draw!")
            break

        row, col = ask_human_move(board)
        board[row][col] = HUMAN
        print_board(board)
        if check_winner(board, HUMAN):
            print("O wins!")
            break
        if is_board_full(board):
            print("It's a draw!")
            break


# Example usage:
if __name__ == "__main__":
    compare_searches()
    play()
