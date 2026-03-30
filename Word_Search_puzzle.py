import sys
import json
import random
import math
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                            QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QKeySequence, QShortcut

class WordSearchGame(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.grid_size is now set in start_new_game()
        self.grid_size = 0 
        self.current_level = 1
        self.found_words = []
        self.selected_cells = []
        self.is_selecting = False
        self.start_cell = None
        self.word_database = self.load_word_database() # Load database
        self.current_words = []
        self.grid_buttons = []
        self.word_buttons = []
        
        self.hints_left = 3  # Number of hints available
        self.word_positions = {}  # Store positions of each word
        self.permanently_highlighted_cells = set()  # NEW: Store cells that should stay highlighted
        
        self.init_ui()
        self.start_new_game()
        
    def load_word_database(self):
        """Load words from JSON database normally, return empty dict on error."""
        json_file = 'word_database.json'
        
        if not os.path.exists(json_file):
            print(f"WARNING: JSON file '{json_file}' not found. Game will start without words.")
            return {}
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, dict):
                print(f"WARNING: JSON file '{json_file}' content is not a dictionary. Returning empty database.")
                return {}
            
            for key in ['easy', 'medium', 'hard']:
                if key not in data or not isinstance(data[key], list):
                    print(f"WARNING: Missing or invalid '{key}' list in JSON. Game might have issues.")
                    data[key] = [] # Ensure it's at least an empty list
                
                # Ensure words are strings and uppercase
                validated_words = []
                for word in data[key]:
                    if isinstance(word, str) and word.strip():
                        validated_words.append(word.strip().upper())
                    else:
                        print(f"WARNING: Invalid word '{word}' in {key} difficulty - skipping.")
                data[key] = validated_words

            print(f"INFO: Successfully loaded word database from '{json_file}'.")
            return data
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON format in '{json_file}': {e}. Game will start without words.")
            return {}
        except Exception as e:
            print(f"ERROR: Could not read JSON file '{json_file}': {e}. Game will start without words.")
            return {}
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Word Search Puzzle Game")
        # Increased window size to accommodate larger grids
        self.setGeometry(100, 100, 1100, 800)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 2px solid #606060;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #808080;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
            QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 2px solid #606060;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for game info and controls
        left_panel = QFrame()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        
        # Game title
        title_label = QLabel("🔍 WORD SEARCH")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; color: #4CAF50; margin: 10px;")
        left_layout.addWidget(title_label)
        
        # Level selector
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Difficulty:"))
        self.level_combo = QComboBox()
        
        # Only add difficulties that exist in JSON and have words
        available_difficulties = []
        for diff in ['easy', 'medium', 'hard']:
            if self.word_database and diff in self.word_database and len(self.word_database[diff]) > 0:
                available_difficulties.append(diff.capitalize())
        
        if available_difficulties:
            self.level_combo.addItems(available_difficulties)
            self.level_combo.currentTextChanged.connect(self.change_difficulty)
        else:
            self.level_combo.addItem("No difficulties available")
            self.level_combo.setEnabled(False) # Disable if no words
        
        level_layout.addWidget(self.level_combo)
        left_layout.addLayout(level_layout)
        
        # Words to find
        words_label = QLabel("Words to Find:")
        words_label.setStyleSheet("color: #4CAF50; margin-top: 20px;")
        left_layout.addWidget(words_label)
        
        self.words_frame = QFrame()
        self.words_layout = QVBoxLayout(self.words_frame)
        left_layout.addWidget(self.words_frame)
        
        # Control buttons
        self.new_game_btn = QPushButton("🎮 New Game")
        self.new_game_btn.clicked.connect(self.start_new_game)
        self.new_game_btn.setStyleSheet("background-color: #4CAF50;")
        left_layout.addWidget(self.new_game_btn)
        
        # Complete selection button
        self.complete_btn = QPushButton("✅ Complete Selection")
        self.complete_btn.clicked.connect(self.complete_selection)
        self.complete_btn.setStyleSheet("background-color: #2196F3;")
        self.complete_btn.setEnabled(False)  # Disabled until selection starts
        left_layout.addWidget(self.complete_btn)
        
        # Reset selection button
        self.reset_btn = QPushButton("🔄 Reset Selection")
        self.reset_btn.clicked.connect(self.reset_selection)
        self.reset_btn.setStyleSheet("background-color: #9E9E9E;")
        self.reset_btn.setEnabled(False)  # Disabled until selection starts
        left_layout.addWidget(self.reset_btn)
        
        self.hint_btn = QPushButton("💡 Hint")
        self.hint_btn.clicked.connect(self.show_hint)
        self.hint_btn.setStyleSheet("background-color: #FF9800;")
        left_layout.addWidget(self.hint_btn)
        
        # NEW: AI Solve button
        self.solve_btn = QPushButton("🤖 Solve Word")
        self.solve_btn.clicked.connect(self.solve_one_word)
        self.solve_btn.setStyleSheet("background-color: #A348A2;") # A new color for the AI button
        left_layout.addWidget(self.solve_btn)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Right panel for the game grid
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        
        # Grid container
        self.grid_frame = QFrame()
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(2)
        right_layout.addWidget(self.grid_frame)
        
        main_layout.addWidget(right_panel)
        
        # Add keyboard shortcuts
        self.complete_shortcut = QShortcut(QKeySequence("Return"), self)
        self.complete_shortcut.activated.connect(self.complete_selection)
        
        self.escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.escape_shortcut.activated.connect(self.reset_selection)
        
    def start_new_game(self):
        """Start a new game using ONLY JSON data"""
        self.found_words = []
        self.hints_left = 3
        self.word_positions = {}
        self.permanently_highlighted_cells = set()  # NEW: Reset permanent highlights
        self.hint_btn.setText(f"💡 Hint ({self.hints_left})")
        self.solve_btn.setEnabled(True) # Re-enable AI button
        self.selected_cells = []
        
        if not self.word_database or self.level_combo.currentText() == "No difficulties available":
            print("INFO: Cannot start new game, no valid word database or difficulties available.")
            return
        
        difficulty = self.level_combo.currentText().lower()
        
        #All levels have 5 words
        word_count = 5
        
        if difficulty == "easy":
            self.grid_size = 12
        elif difficulty == "medium":
            self.grid_size = 14
        else:  # hard
            self.grid_size = 16
        
        # Ensure we don't try to select more words than available
        word_count = min(word_count, len(self.word_database[difficulty]))
        
        if word_count == 0:
            print(f"WARNING: No words to select for {difficulty} difficulty. Cannot start game.")
            return
            
        self.current_words = random.sample(self.word_database[difficulty], word_count)
        
        print(f"🎮 Starting new {difficulty} game with {word_count} words on a {self.grid_size}x{self.grid_size} grid.")
        print(f"   Words: {self.current_words}")
        
        self.create_grid()
        self.place_words()
        self.fill_empty_cells()
        self.create_word_buttons()
        
    def create_grid(self):
        """Create the letter grid with a dynamic size"""
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.grid_buttons = []
        self.grid = [[''] * self.grid_size for _ in range(self.grid_size)]
        
        # --- NEW LOGIC: Adjust button size based on grid size ---
        button_size = 40
        if self.grid_size > 14:
            button_size = 35
        # --------------------------------------------------------
        
        for row in range(self.grid_size):
            button_row = []
            for col in range(self.grid_size):
                btn = QPushButton('')
                btn.setFixedSize(button_size, button_size)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a4a4a;
                        border: 1px solid #666;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #5a5a5a;
                    }
                """)
                btn.clicked.connect(lambda checked, r=row, c=col: self.cell_clicked(r, c))
                self.grid_layout.addWidget(btn, row, col)
                button_row.append(btn)
            self.grid_buttons.append(button_row)
    
    def place_words(self):
        """Place words randomly in the grid"""
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal down-right
            (-1, 1),  # diagonal up-right
        ]
        
        for word in self.current_words:
            placed = False
            attempts = 0
            
            while not placed and attempts < 100:
                direction = random.choice(directions)
                start_row = random.randint(0, self.grid_size - 1)
                start_col = random.randint(0, self.grid_size - 1)
                
                if self.can_place_word(word, start_row, start_col, direction):
                    self.place_word(word, start_row, start_col, direction)
                    placed = True
                
                attempts += 1
            
            if not placed:
                print(f"⚠️  Warning: Could not place word '{word}' after 100 attempts")
    
    def can_place_word(self, word, start_row, start_col, direction):
        """Check if a word can be placed at the given position"""
        dr, dc = direction
        
        for i, letter in enumerate(word):
            row = start_row + i * dr
            col = start_col + i * dc
            
            if (row < 0 or row >= self.grid_size or 
                col < 0 or col >= self.grid_size):
                return False
            
            if (self.grid[row][col] != '' and 
                self.grid[row][col] != letter):
                return False
        
        return True
    
    def place_word(self, word, start_row, start_col, direction):
        """Place a word in the grid and store its positions"""
        dr, dc = direction
        positions = []
        
        for i, letter in enumerate(word):
            row = start_row + i * dr
            col = start_col + i * dc
            self.grid[row][col] = letter
            positions.append((row, col))
        
        # Store the positions for this word
        self.word_positions[word] = positions
        print(f"📍 Placed '{word}' at positions: {positions}")
    
    def fill_empty_cells(self):
        """Fill empty cells with random letters"""
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.grid[row][col] == '':
                    self.grid[row][col] = random.choice(letters)
                
                if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                    self.grid_buttons[row][col].setText(self.grid[row][col])
    
    def create_word_buttons(self):
        """Create buttons for words to find"""
        # Clear existing word buttons
        for i in reversed(range(self.words_layout.count())): 
            widget = self.words_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        self.word_buttons = []
        for word in self.current_words:
            btn = QPushButton(word)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6B6B;
                    color: white;
                    border-radius: 5px;
                    padding: 5px;
                    margin: 2px;
                }
            """)
            self.words_layout.addWidget(btn)
            self.word_buttons.append(btn)
    
    def cell_clicked(self, row, col):
        """Handle cell click for word selection"""
        if not self.is_selecting:
            # First click - start selection
            self.start_cell = (row, col)
            self.is_selecting = True
            self.selected_cells = [(row, col)]
            self.complete_btn.setEnabled(True)  # Enable complete button
            self.reset_btn.setEnabled(True)  # Enable reset button
            self.highlight_cells()
            print(f"🖱️ Started selection at ({row}, {col})")
        else:
            # Already selecting
            current_cell = (row, col)
            
            # If clicking the same start cell, complete selection
            if current_cell == self.start_cell and len(self.selected_cells) > 1:
                print("🎯 Completing selection by clicking start cell")
                self.complete_selection()
                return
            
            # If clicking an empty area or invalid selection, reset
            if not self.is_valid_selection(self.start_cell, current_cell):
                print("❌ Invalid selection, resetting")
                self.reset_selection()
                return
            
            # Valid selection - update the selection
            new_selection = self.get_cells_between(self.start_cell, current_cell)
            self.selected_cells = new_selection
            self.highlight_cells()
            print(f"📏 Extended selection to ({row}, {col}), length: {len(self.selected_cells)}")
    
    def complete_selection(self):
        """Complete the current selection and check for words"""
        if self.is_selecting and len(self.selected_cells) > 0:
            self.check_word_selection()
            self.reset_selection()
    
    def reset_selection(self):
        """Reset the current selection"""
        self.is_selecting = False
        self.start_cell = None
        self.selected_cells = []
        self.complete_btn.setEnabled(False)  # Disable complete button
        self.reset_btn.setEnabled(False)
        self.highlight_cells()
    
    def is_valid_selection(self, start, end):
        """Check if selection forms a straight line"""
        start_row, start_col = start
        end_row, end_col = end
        
        if start == end:
            return True
        
        dr = end_row - start_row
        dc = end_col - start_col
        
        # Check if it's horizontal, vertical, or diagonal
        return (dr == 0 or dc == 0 or abs(dr) == abs(dc))
    
    def get_cells_between(self, start, end):
        """Get all cells between start and end positions"""
        start_row, start_col = start
        end_row, end_col = end
        
        cells = []
        
        if start == end:
            return [start]
        
        dr = end_row - start_row
        dc = end_col - start_col
        
        steps = max(abs(dr), abs(dc))
        
        # Avoid division by zero
        if steps == 0:
            return [start]

        for i in range(steps + 1):
            row = start_row + (dr * i) // steps
            col = start_col + (dc * i) // steps
            cells.append((row, col))
        
        return cells
    
    def highlight_cells(self):
        """Highlight selected cells - MODIFIED to keep found words highlighted"""
        # Reset all cells to default first
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                    self.grid_buttons[row][col].setStyleSheet("""
                        QPushButton {
                            background-color: #4a4a4a;
                            border: 1px solid #666;
                            border-radius: 5px;
                            font-size: 16px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #5a5a5a;
                        }
                    """)
        
        # Highlight permanently found word cells (GREEN)
        for row, col in self.permanently_highlighted_cells:
            if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                self.grid_buttons[row][col].setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        border: 1px solid #666;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                        color: white;
                    }
                """)
        
        # Highlight currently selected cells (YELLOW/GOLD) - these override green temporarily
        for row, col in self.selected_cells:
            if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                self.grid_buttons[row][col].setStyleSheet("""
                    QPushButton {
                        background-color: #FFD700;
                        border: 2px solid #FFA500;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                        color: black;
                    }
                """)
    
    def check_word_selection(self):
        """Check if selected cells form a valid word - MODIFIED to permanently highlight found words"""
        selected_letters = ''.join([self.grid[row][col] for row, col in self.selected_cells])
        reversed_letters = selected_letters[::-1]
        
        for i, word in enumerate(self.current_words):
            if (selected_letters == word or reversed_letters == word) and word not in self.found_words:
                self.found_words.append(word)
                print(f"✅ Found word: {word} ({len(self.found_words)}/{len(self.current_words)})")
                
                # NEW: Add word positions to permanently highlighted cells
                if word in self.word_positions:
                    for pos in self.word_positions[word]:
                        self.permanently_highlighted_cells.add(pos)
            
                # Mark word as found
                if i < len(self.word_buttons):
                    self.word_buttons[i].setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border-radius: 5px;
                            padding: 5px;
                            margin: 2px;
                        }
                    """)
            
                # Check if all words found
                if len(self.found_words) == len(self.current_words):
                    QTimer.singleShot(1000, self.game_won)  # Delay to show final highlight
                    self.solve_btn.setEnabled(False) # Disable AI button once all words are found
            
                break
    
    def clear_selection(self):
        """Clear current selection - MODIFIED to preserve permanent highlights"""
        self.selected_cells = []
        self.highlight_cells()  # This will now preserve the permanently highlighted cells
    
    def show_hint(self):
        """Show hint by highlighting a letter from an unfound word"""
        if self.hints_left > 0:
            remaining_words = [w for w in self.current_words if w not in self.found_words]
            if remaining_words:
                word = random.choice(remaining_words)
                if word in self.word_positions:
                    positions = self.word_positions[word]
                    pos = random.choice(positions)
                    row, col = pos
                
                    if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                        # Highlight the hint cell with orange color
                        self.grid_buttons[row][col].setStyleSheet("""
                            QPushButton {
                                background-color: #FF9800;
                                border: 2px solid #F57C00;
                                border-radius: 5px;
                                font-size: 16px;
                                font-weight: bold;
                                color: white;
                            }
                        """)
                
                        self.hints_left -= 1
                        self.hint_btn.setText(f"💡 Hint ({self.hints_left})")
                
                        # Remove hint highlight after 3 seconds
                        QTimer.singleShot(3000, lambda: self.clear_hint_highlight(row, col))
            else:
                QMessageBox.information(self, "All Found!", "You've found all the words!")
        else:
            QMessageBox.warning(self, "No Hints", "You have no hints left!")

    def clear_hint_highlight(self, row, col):
        """Clear the hint highlight from a cell - MODIFIED to respect permanent highlights"""
        # Check if this cell should be permanently highlighted
        if (row, col) in self.permanently_highlighted_cells:
            # Restore to green (found word color)
            if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                self.grid_buttons[row][col].setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        border: 1px solid #666;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                        color: white;
                    }
                """)
        else:
            # Restore to default color
            if row < len(self.grid_buttons) and col < len(self.grid_buttons[row]):
                self.grid_buttons[row][col].setStyleSheet("""
                    QPushButton {
                        background-color: #4a4a4a;
                        border: 1px solid #666;
                        border-radius: 5px;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #5a5a5a;
                    }
                """)
    
    def solve_one_word(self):
        """AI function to automatically find and highlight one unfound word."""
        # Find the first unfound word
        unfound_words = [word for word in self.current_words if word not in self.found_words]
        
        if not unfound_words:
            QMessageBox.information(self, "No Words Left", "All words have already been found!")
            self.solve_btn.setEnabled(False) # Disable button if no words left
            return
            
        # Get the first unfound word and its position from the internal data
        word_to_solve = unfound_words[0]
        word_positions = self.word_positions.get(word_to_solve)
        
        if word_positions:
            # Add the word to the found list
            self.found_words.append(word_to_solve)
            
            # Add its positions to the permanently highlighted cells
            for pos in word_positions:
                self.permanently_highlighted_cells.add(pos)
                
            print(f"🤖 AI solved word: {word_to_solve}")
            
            # Update the UI
            self.highlight_cells()
            
            # Find the corresponding word button and style it as found
            for btn in self.word_buttons:
                if btn.text() == word_to_solve:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border-radius: 5px;
                            padding: 5px;
                            margin: 2px;
                        }
                    """)
                    break
            
            # Check if all words are now found
            if len(self.found_words) == len(self.current_words):
                QTimer.singleShot(1000, self.game_won)
                self.solve_btn.setEnabled(False)
        else:
            print(f"⚠️  Error: Could not find positions for word '{word_to_solve}' in word_positions.")
        
    def change_difficulty(self):
        """Change game difficulty"""
        self.start_new_game()
    
    def game_won(self):
        """Handle game won"""
        QMessageBox.information(self, "Congratulations!", 
                               "You found all words!🎉")

def main():
    app = QApplication(sys.argv)
    game = WordSearchGame()
    game.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
