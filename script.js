// Word Search Puzzle Game - Web Version
// Direct port from PyQt6 Python app

class WordSearchGame {
  constructor() {
    this.gridSize = 0;
    this.currentLevel = "hard";
    this.foundWords = [];
    this.selectedCells = [];
    this.isSelecting = false;
    this.startCell = null;
    this.hintsLeft = 3;
    this.wordPositions = {};
    this.permanentlyHighlightedCells = new Set();

    // Word database embedded from word_database.json
    this.wordDatabase = {
      easy: [
        "CAT",
        "DOG",
        "SUN",
        "MOON",
        "STAR",
        "TREE",
        "FISH",
        "BIRD",
        "BOOK",
        "CAKE",
        "GAME",
        "LOVE",
        "HOME",
        "BLUE",
        "FIRE",
        "WIND",
        "ROCK",
        "GOLD",
        "SNOW",
        "RAIN",
        "LEAF",
        "BEAR",
        "DUCK",
        "FROG",
      ],
      medium: [
        "PYTHON",
        "COMPUTER",
        "RAINBOW",
        "MOUNTAIN",
        "OCEAN",
        "FOREST",
        "GUITAR",
        "PLANET",
        "DRAGON",
        "CASTLE",
        "WIZARD",
        "KNIGHT",
        "FLOWER",
        "GARDEN",
        "BRIDGE",
        "ROCKET",
        "JUNGLE",
        "DESERT",
        "ISLAND",
        "VALLEY",
        "STREAM",
        "MEADOW",
        "SUNSET",
        "WINTER",
      ],
      hard: [
        "PROGRAMMING",
        "ADVENTURE",
        "BUTTERFLY",
        "TELESCOPE",
        "UNIVERSE",
        "MYSTERIOUS",
        "WONDERFUL",
        "BEAUTIFUL",
        "FANTASTIC",
        "INCREDIBLE",
        "MAGNIFICENT",
        "SPECTACULAR",
        "EXTRAORDINARY",
        "FASCINATING",
        "BREATHTAKING",
        "OVERWHELMING",
        "UNFORGETTABLE",
        "REMARKABLE",
      ],
    };

    this.currentWords = [];
    this.gridButtons = [];
    this.wordButtons = [];

    this.init();
  }

  init() {
    this.bindEvents();
    this.startNewGame();
  }

  bindEvents() {
    document
      .getElementById("new-game")
      .addEventListener("click", () => this.startNewGame());
    document
      .getElementById("complete")
      .addEventListener("click", () => this.completeSelection());
    document
      .getElementById("reset")
      .addEventListener("click", () => this.resetSelection());
    document
      .getElementById("hint")
      .addEventListener("click", () => this.showHint());
    document
      .getElementById("solve")
      .addEventListener("click", () => this.solveOneWord());
    document.getElementById("difficulty").addEventListener("change", (e) => {
      this.currentLevel = e.target.value;
      this.startNewGame();
    });

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === "Return") {
        this.completeSelection();
      } else if (e.key === "Escape") {
        this.resetSelection();
      }
    });
  }

  startNewGame() {
    this.foundWords = [];
    this.hintsLeft = 3;
    this.wordPositions = {};
    this.permanentlyHighlightedCells.clear();
    this.selectedCells = [];
    this.isSelecting = false;
    this.startCell = null;

    document.getElementById("hint").textContent = `💡 Hint (${this.hintsLeft})`;
    document.getElementById("solve").disabled = false;

    const difficulty = document.getElementById("difficulty").value;
    const availableWords = this.wordDatabase[difficulty];

    if (!availableWords || availableWords.length === 0) {
      console.warn(`No words for ${difficulty}`);
      return;
    }

    // Grid sizes matching Python: easy=12, med=14, hard=16
    const sizes = { easy: 12, medium: 14, hard: 16 };
    this.gridSize = sizes[difficulty];

    const wordCount = 5;
    this.currentWords = this.shuffle(availableWords).slice(
      0,
      Math.min(wordCount, availableWords.length),
    );

    console.log(
      `Starting ${difficulty} game: ${this.currentWords.join(", ")} on ${this.gridSize}x${this.gridSize}`,
    );

    this.createGrid();
    this.placeWords();
    this.fillEmptyCells();
    this.createWordButtons();
    this.updateButtons();
  }

  shuffle(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  createGrid() {
    const gridContainer = document.getElementById("game-grid");
    gridContainer.style.gridTemplateColumns = `repeat(${this.gridSize}, 1fr)`;
    gridContainer.innerHTML = "";

    this.grid = Array(this.gridSize)
      .fill()
      .map(() => Array(this.gridSize).fill(""));
    this.gridButtons = [];

    // Calculate cell size based on grid size (matching Python)
    const cellSize = this.gridSize > 14 ? 35 : 40;

    for (let row = 0; row < this.gridSize; row++) {
      this.gridButtons[row] = [];
      for (let col = 0; col < this.gridSize; col++) {
        const cell = document.createElement("div");
        cell.className = "cell cell-default";
        cell.dataset.row = row;
        cell.dataset.col = col;
        cell.textContent = "";
        cell.style.minWidth = `${cellSize}px`;
        cell.style.minHeight = `${cellSize}px`;
        cell.style.fontSize = `${Math.max(14, 20 - this.gridSize / 2)}px`;

        cell.addEventListener("click", (e) =>
          this.cellClicked(
            parseInt(e.currentTarget.dataset.row),
            parseInt(e.currentTarget.dataset.col),
          ),
        );
        gridContainer.appendChild(cell);
        this.gridButtons[row][col] = cell;
      }
    }
  }

  placeWords() {
    const directions = [
      [0, 1], // horizontal
      [1, 0], // vertical
      [1, 1], // diagonal down-right
      [-1, 1], // diagonal up-right
    ];

    for (const word of this.currentWords) {
      let placed = false;
      let attempts = 0;

      while (!placed && attempts < 100) {
        const dir = directions[Math.floor(Math.random() * directions.length)];
        const startRow = Math.floor(Math.random() * this.gridSize);
        const startCol = Math.floor(Math.random() * this.gridSize);

        if (this.canPlaceWord(word, startRow, startCol, dir)) {
          this.placeWord(word, startRow, startCol, dir);
          placed = true;
        }
        attempts++;
      }

      if (!placed) {
        console.warn(`Could not place word '${word}'`);
      }
    }
  }

  canPlaceWord(word, startRow, startCol, dir) {
    const [dr, dc] = dir;
    for (let i = 0; i < word.length; i++) {
      const row = startRow + i * dr;
      const col = startCol + i * dc;

      if (row < 0 || row >= this.gridSize || col < 0 || col >= this.gridSize) {
        return false;
      }

      if (this.grid[row][col] !== "" && this.grid[row][col] !== word[i]) {
        return false;
      }
    }
    return true;
  }

  placeWord(word, startRow, startCol, dir) {
    const [dr, dc] = dir;
    const positions = [];

    for (let i = 0; i < word.length; i++) {
      const row = startRow + i * dr;
      const col = startCol + i * dc;
      this.grid[row][col] = word[i];
      positions.push([row, col]);
    }

    this.wordPositions[word] = positions;
    console.log(`Placed '${word}' at ${positions}`);
  }

  fillEmptyCells() {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    for (let row = 0; row < this.gridSize; row++) {
      for (let col = 0; col < this.gridSize; col++) {
        if (this.grid[row][col] === "") {
          this.grid[row][col] =
            letters[Math.floor(Math.random() * letters.length)];
        }
        this.gridButtons[row][col].textContent = this.grid[row][col];
      }
    }
  }

  createWordButtons() {
    const wordsList = document.getElementById("words-list");
    wordsList.innerHTML = "";
    this.wordButtons = [];

    for (const word of this.currentWords) {
      const wordDiv = document.createElement("div");
      wordDiv.className = "word-item word-unfound";
      wordDiv.textContent = word;
      wordsList.appendChild(wordDiv);
      this.wordButtons.push(wordDiv);
    }
  }

  cellClicked(row, col) {
    if (!this.isSelecting) {
      // Start selection
      this.startCell = [row, col];
      this.isSelecting = true;
      this.selectedCells = [[row, col]];
      this.updateButtons();
      this.highlightCells();
      console.log(`Started at [${row}, ${col}]`);
    } else {
      const currentCell = [row, col];

      // Complete if clicking start again and >1 cell
      if (
        this.arraysEqual(currentCell, this.startCell) &&
        this.selectedCells.length > 1
      ) {
        this.completeSelection();
        return;
      }

      // Reset if invalid
      if (!this.isValidSelection(this.startCell, currentCell)) {
        this.resetSelection();
        return;
      }

      // Update selection
      this.selectedCells = this.getCellsBetween(this.startCell, currentCell);
      this.highlightCells();
      console.log(
        `Extended to [${row}, ${col}], length: ${this.selectedCells.length}`,
      );
    }
  }

  arraysEqual(a, b) {
    return a[0] === b[0] && a[1] === b[1];
  }

  completeSelection() {
    if (this.isSelecting && this.selectedCells.length > 0) {
      this.checkWordSelection();
      this.resetSelection();
    }
  }

  resetSelection() {
    this.isSelecting = false;
    this.startCell = null;
    this.selectedCells = [];
    this.updateButtons();
    this.highlightCells();
  }

  isValidSelection(start, end) {
    const [sr, sc] = start;
    const [er, ec] = end;
    if (this.arraysEqual(start, end)) return true;

    const dr = er - sr;
    const dc = ec - sc;
    return dr === 0 || dc === 0 || Math.abs(dr) === Math.abs(dc);
  }

  getCellsBetween(start, end) {
    const [sr, sc] = start;
    const [er, ec] = end;
    const cells = [];

    if (this.arraysEqual(start, end)) return [start];

    const dr = er - sr;
    const dc = ec - sc;
    const steps = Math.max(Math.abs(dr), Math.abs(dc));

    if (steps === 0) return [start];

    for (let i = 0; i <= steps; i++) {
      const row = sr + Math.round((dr * i) / steps);
      const col = sc + Math.round((dc * i) / steps);
      cells.push([row, col]);
    }
    return cells;
  }

  highlightCells() {
    // Reset all
    for (let row = 0; row < this.gridSize; row++) {
      for (let col = 0; col < this.gridSize; col++) {
        const cell = this.gridButtons[row][col];
        cell.className = "cell cell-default";

        // Permanent found (green overrides)
        if (this.permanentlyHighlightedCells.has(`${row}-${col}`)) {
          cell.classList.add("cell-found");
        }
      }
    }

    // Current selection (gold overrides)
    for (const [row, col] of this.selectedCells) {
      this.gridButtons[row][col].classList.add("cell-selected");
    }
  }

  checkWordSelection() {
    let selectedLetters = "";
    for (const [row, col] of this.selectedCells) {
      selectedLetters += this.grid[row][col];
    }
    const reversedLetters = selectedLetters.split("").reverse().join("");

    for (let i = 0; i < this.currentWords.length; i++) {
      const word = this.currentWords[i];
      if (
        (selectedLetters === word || reversedLetters === word) &&
        !this.foundWords.includes(word)
      ) {
        this.foundWords.push(word);
        console.log(`Found: ${word}`);

        // Permanent highlight
        if (this.wordPositions[word]) {
          for (const [r, c] of this.wordPositions[word]) {
            this.permanentlyHighlightedCells.add(`${r}-${c}`);
          }
        }

        // Update word button
        if (this.wordButtons[i]) {
          this.wordButtons[i].className = "word-item word-found";
        }

        this.highlightCells();

        // Win check
        if (this.foundWords.length === this.currentWords.length) {
          setTimeout(
            () => alert("Congratulations! You found all words! 🎉"),
            500,
          );
          document.getElementById("solve").disabled = true;
        }
        return;
      }
    }
  }

  showHint() {
    if (this.hintsLeft > 0) {
      const remaining = this.currentWords.filter(
        (w) => !this.foundWords.includes(w),
      );
      if (remaining.length > 0) {
        const word = remaining[Math.floor(Math.random() * remaining.length)];
        if (this.wordPositions[word]) {
          const pos =
            this.wordPositions[word][
              Math.floor(Math.random() * this.wordPositions[word].length)
            ];
          const [row, col] = pos;
          const cell = this.gridButtons[row][col];
          cell.classList.add("cell-hint");

          this.hintsLeft--;
          document.getElementById("hint").textContent =
            `💡 Hint (${this.hintsLeft})`;

          // Clear after 3s
          setTimeout(() => {
            cell.classList.remove("cell-hint");
            if (this.permanentlyHighlightedCells.has(`${row}-${col}`)) {
              cell.classList.add("cell-found");
            }
          }, 3000);
        }
      }
    } else {
      alert("No hints left!");
    }
  }

  solveOneWord() {
    const unfound = this.currentWords.filter(
      (w) => !this.foundWords.includes(w),
    );
    if (unfound.length === 0) {
      alert("All words found!");
      document.getElementById("solve").disabled = true;
      return;
    }

    const word = unfound[0];
    if (this.wordPositions[word]) {
      this.foundWords.push(word);
      for (const [r, c] of this.wordPositions[word]) {
        this.permanentlyHighlightedCells.add(`${r}-${c}`);
      }

      // Update UI
      this.highlightCells();
      const wordIndex = this.currentWords.indexOf(word);
      if (this.wordButtons[wordIndex]) {
        this.wordButtons[wordIndex].className = "word-item word-found";
      }

      console.log(`AI solved: ${word}`);

      if (this.foundWords.length === this.currentWords.length) {
        setTimeout(
          () => alert("Congratulations! You found all words! 🎉"),
          500,
        );
        document.getElementById("solve").disabled = true;
      }
    }
  }

  updateButtons() {
    document.getElementById("complete").disabled = !this.isSelecting;
    document.getElementById("reset").disabled = !this.isSelecting;
  }
}

// Initialize game when DOM loaded
document.addEventListener("DOMContentLoaded", () => {
  new WordSearchGame();
});
