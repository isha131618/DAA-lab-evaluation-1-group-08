import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from copy import deepcopy
import random
import os

# ------------------ CONSTANTS ------------------

TILE = 160
BOARD_SIZE = 480
BG_COLOR = "misty rose"

GOAL = [[1, 2, 3],
        [4, 5, 6],
        [7, 8, 0]]

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# ------------------ ADJACENCY MATRIX GRAPH ------------------

state_index = {}     # state -> index
index_state = {}     # index -> state
adj_matrix = []      # adjacency matrix

def add_state(state):
    key = str(state)
    if key not in state_index:
        idx = len(state_index)
        state_index[key] = idx
        index_state[idx] = deepcopy(state)

        for row in adj_matrix:
            row.append(0)
        adj_matrix.append([0] * (idx + 1))

    return state_index[key]

def add_edge(s1, s2):
    i = add_state(s1)
    j = add_state(s2)
    adj_matrix[i][j] = 1
    adj_matrix[j][i] = 1   # undirected graph

# ------------------ UTILITY FUNCTIONS ------------------

def find_zero(state):
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                return r, c

def manhattan(state):
    d = 0
    for r in range(3):
        for c in range(3):
            v = state[r][c]
            if v != 0:
                tr, tc = divmod(v - 1, 3)
                d += abs(r - tr) + abs(c - tc)
    return d

def linear_conflict(state):
    md = manhattan(state)
    conflicts = 0

    for r in range(3):
        row = [state[r][c] for c in range(3) if state[r][c] != 0]
        for i in range(len(row)):
            for j in range(i + 1, len(row)):
                tr_i, _ = divmod(row[i] - 1, 3)
                tr_j, _ = divmod(row[j] - 1, 3)
                if tr_i == r and tr_j == r and row[i] > row[j]:
                    conflicts += 1

    return md + 2 * conflicts

# ------------------ MERGE SORT ------------------

def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i][0] < right[j][0]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result

# ------------------ GREEDY SOLVER (WITH ADJ MATRIX) ------------------

def greedy_solver(start):
    open_list = [(linear_conflict(start), start, [])]
    visited = set()

    add_state(start)

    while open_list:
        open_list = merge_sort(open_list)
        _, state, path = open_list.pop(0)

        if state == GOAL:
            return path + [state]

        visited.add(str(state))
        zr, zc = find_zero(state)

        for dr, dc in DIRS:
            nr, nc = zr + dr, zc + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                nxt = deepcopy(state)
                nxt[zr][zc], nxt[nr][nc] = nxt[nr][nc], 0

                add_edge(state, nxt)   

                if str(nxt) not in visited:
                    h = linear_conflict(nxt)
                    open_list.append((h, nxt, path + [state]))

    return []

# ------------------ GUI APPLICATION ------------------

class PuzzleApp:
    def __init__(self, root):
        self.root = root
        root.title("8-Puzzle — User vs Greedy AI (Adjacency Matrix)")
        root.geometry("1500x800")
        root.configure(bg=BG_COLOR)

        self.user_state = deepcopy(GOAL)
        self.ai_state = deepcopy(GOAL)

        self.user_steps = 0
        self.ai_steps = 0

        self.image_name = "dog.jpg"

        self.build_top()
        self.build_sidebar()
        self.build_center()
        self.load_image()
        self.update_boards()

    def build_top(self):
        bar = tk.Frame(self.root, bg="Dark slate grey", height=80)
        bar.pack(fill="x")

        tk.Label(bar,
                 text="8-Puzzle — User vs Greedy AI (Adjacency Matrix)",
                 bg="Dark slate grey",
                 fg="white",
                 font=("Segoe UI", 22, "bold")).pack(pady=10)

    def build_sidebar(self):
        side = tk.Frame(self.root, bg="Dark slate grey", width=200)
        side.pack(side="left", fill="y")

        images = ["dog.jpg", "girl.jpg", "bike.jpg",
                  "tiger.jpg", "mickey.jpg", "snowwhite.jpg"]

        for img in images:
            if not os.path.exists(img):
                continue
            im = Image.open(img).resize((90, 90))
            tk_img = ImageTk.PhotoImage(im)
            b = tk.Button(side, image=tk_img, bd=0,
                          command=lambda x=img: self.change_image(x))
            b.image = tk_img
            b.pack(pady=10)

    def build_center(self):
        center = tk.Frame(self.root, bg=BG_COLOR)
        center.pack(expand=True)

        boards = tk.Frame(center, bg=BG_COLOR)
        boards.pack()

        self.user_tiles = self.create_board(boards, "USER", self.move_user)
        self.ai_tiles = self.create_board(boards, "GREEDY AI", None)

        controls = tk.Frame(center, bg=BG_COLOR)
        controls.pack(pady=20)

        tk.Button(controls, text="Shuffle",
                  font=("Segoe UI", 14),
                  width=12, command=self.shuffle).pack(side="left", padx=10)

        tk.Button(controls, text="Solve (AI)",
                  font=("Segoe UI", 14),
                  width=12, command=self.solve_ai).pack(side="left", padx=10)

        self.info_lbl = tk.Label(center,
                                 text="User Steps: 0 | AI Steps: 0",
                                 font=("Segoe UI", 14),
                                 bg=BG_COLOR)
        self.info_lbl.pack()

    def create_board(self, parent, title, command):
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(side="left", padx=40)

        tk.Label(frame, text=title,
                 font=("Segoe UI", 16, "bold"),
                 bg=BG_COLOR).pack()

        board = tk.Frame(frame, bg="black",
                         width=BOARD_SIZE, height=BOARD_SIZE)
        board.pack(pady=10)
        board.pack_propagate(False)

        tiles = []
        for r in range(3):
            for c in range(3):
                b = tk.Button(board, bd=0, bg="black",
                              activebackground="black",
                              command=(lambda r=r, c=c: command(r, c))
                              if command else None)
                b.grid(row=r, column=c)
                tiles.append(b)
        return tiles

    def load_image(self):
        img = Image.open(self.image_name).resize((BOARD_SIZE, BOARD_SIZE))
        self.cuts = []
        for i in range(8):
            r, c = divmod(i, 3)
            piece = img.crop((c * TILE, r * TILE,
                              (c + 1) * TILE, (r + 1) * TILE))
            self.cuts.append(ImageTk.PhotoImage(piece))
        self.cuts.append(None)

    def change_image(self, img):
        self.image_name = img
        self.load_image()
        self.update_boards()

    def update_boards(self):
        self.update_board(self.user_tiles, self.user_state)
        self.update_board(self.ai_tiles, self.ai_state)
        self.info_lbl.config(
            text=f"User Steps: {self.user_steps} | AI Steps: {self.ai_steps}")

    def update_board(self, tiles, state):
        for i in range(9):
            r, c = divmod(i, 3)
            v = state[r][c]
            tiles[i].config(image="" if v == 0 else self.cuts[v - 1])

    def move_user(self, r, c):
        zr, zc = find_zero(self.user_state)
        if abs(r - zr) + abs(c - zc) == 1:
            self.user_state[zr][zc], self.user_state[r][c] = \
                self.user_state[r][c], 0
            self.user_steps += 1
            self.update_boards()

            if self.user_state == GOAL:
                messagebox.showinfo(
                    "User Solved",
                    f"You solved it in {self.user_steps} steps!")

    def shuffle(self):
        state = deepcopy(GOAL)
        for _ in range(150):
            zr, zc = find_zero(state)
            dr, dc = random.choice(DIRS)
            nr, nc = zr + dr, zc + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                state[zr][zc], state[nr][nc] = state[nr][nc], 0

        self.user_state = deepcopy(state)
        self.ai_state = deepcopy(state)
        self.user_steps = 0
        self.ai_steps = 0
        self.update_boards()

    def solve_ai(self):
        self.ai_steps = 0
        path = greedy_solver(deepcopy(self.ai_state))
        self.animate_ai(path, 0)

    def animate_ai(self, path, i):
        if i < len(path):
            if i > 0:
                self.ai_steps += 1
            self.ai_state = deepcopy(path[i])
            self.update_boards()
            self.root.after(400, lambda: self.animate_ai(path, i + 1))

# ------------------ MAIN ------------------

if __name__ == "__main__":
    root = tk.Tk()
    PuzzleApp(root)
    root.mainloop()
