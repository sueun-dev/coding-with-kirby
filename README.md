

# **Big Kirby – Virtual Desktop Pet Game**

![Kirby](images/y3il.gif)

**Big Kirby** is an interactive **desktop pet game** where Kirby moves around your screen, eats food, and levels up over time. As Kirby eats, he **grows in size** and **his level increases**. The game also features an **online ranking board**, so you can compete with friends across different computers!

---

## **🎮 Features**
- **🐾 Virtual Pet:** Kirby moves around your screen, interacting with food.
- **🍕 Food System:** Click the top bar to spawn random foods. Kirby eats them automatically.
- **🔼 Level-Up Mechanic:** Kirby grows larger each time he eats, but leveling up becomes harder at higher levels.
- **📊 Online Ranking Board:** Compete with friends! Your Kirby’s size and level are shared globally.
- **🎨 Cute Animations:** Smooth movement with GIF-based animations.
- **🚀 macOS Application:** Package the game as a **standalone `.app`** for Mac users.
- **💾 Persistent Progress:** Your Kirby's size and level are saved even after restarting.

---

# **📥 Installing the Repository**

### **1. Clone the Repository**
```bash
git clone https://github.com/your-username/big-kirby.git
cd big-kirby
```

### **2. Install Dependencies**
Make sure you have **Python 3.9+** installed, then run:
```bash
pip install -r requirements.txt
```

### **3. Run the Game**
```bash
python3 src/main.py
```

---

# **🍏 Running the macOS App**

### **1. Install PyInstaller**
```bash
pip install pyinstaller
```

### **2. Build the macOS App**
Run the following command from the project root:
```bash
pyinstaller --windowed --onefile --add-data "images:images" src/main.py
```
After the build completes, your **Big Kirby.app** will be inside the `dist/` folder.

### **3. Running the macOS App**
Double-click **Big Kirby.app** inside the `dist/` folder.

> 🛑 **Note:** If macOS prevents the app from running due to security restrictions, go to **System Preferences → Security & Privacy → General** and allow the app.

---

# **🎮 How to Play**
### **1. Spawning Food**
- Click the **top bar** to spawn food. Kirby will automatically move towards it.
- Each food item reduces Kirby’s **hunger**.

### **2. Leveling Up**
- Kirby **grows** every time he eats.
- The **higher the level, the harder it is to level up**.

### **3. Checking the Online Ranking**
- Click **“Ranking”** on the top bar to see the **global leaderboard**.
- Rankings **auto-refresh every 5 seconds**.

### **4. Quitting the Game**
- Click **“Quit”** on the top bar to exit the game.

---

# **📂 Folder Structure**
```
big_kirby/
├── src/
│   ├── core/                 # Core game logic
│   │   └── main_controller.py
│   ├── dialogs/              # UI Dialogs
│   │   └── ranking_board.py
│   ├── utils/                # Utility functions
│   │   └── utils.py
│   └── widgets/              # UI Components
│       ├── pet_widget.py
│       ├── snack_widget.py
│       └── transparent_snackbar.py
│   └── main.py
│
├── images/                   # Image assets (GIFs & food images)
│   ├── y3il.gif
│   ├── y3il-reverse.gif
│   ├── food_1.png
│   ├── food_2.png
│   ├── food_3.png
│   ├── food_4.png
│   ├── food_5.png
│   ├── food_6.png
│   ├── food_7.png
│
├── kirby_state.json           # Saves Kirby's state (auto-created)
├── ranking.json               # Stores global ranking (auto-created)
└── README.md                  # Project documentation
```

---

# **🌎 Offline Ranking System**
Your Kirby’s **size and level** are saved **online** and shared across multiple computers.
(I don't have money to use server...)

### **How It Works**
1. When you close the game, your stats are **uploaded** to a shared ranking file.
2. Other players also upload their scores when they exit.
3. When you check the **Ranking Board**, the latest **global** scores are displayed.

> **Note:** For **true online play**, replace the local ranking system with a **real database or web API** (e.g., Firebase, Supabase, or a Flask/Django backend).

---

# **🚀 Contributing**
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m "Added new feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Submit a **pull request**!

---

# **📜 License**
This project is licensed under the **MIT License**. Feel free to use and modify it!

---

# **👨‍💻 Author**
GitHub: [sueun-dev](https://github.com/sueun-dev)  
Email: sueun.dev@gmail.com

---

### **Final Notes**
✅ **Clear distinction** between **installing the repository** and **running the macOS app**  
✅ **Detailed installation steps** for both environments  
✅ **Perfect formatting** with headers, code blocks, and structured sections  

This is now the ideal **README.md** for your **Big Kirby** project! 🚀
