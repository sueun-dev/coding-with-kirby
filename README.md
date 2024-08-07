# coding-with-kirby

Kirby keeps wandering around the screen. Whether you're coding 👨‍💻 or doing something else, enjoy the company of adorable Kirby. I made it just because it's cute! 🥰🌟

This project includes code for the Kirby animation and interaction on the desktop.

## Running the Application

### For macOS Users

1. **Download the `big_kirby.app`** file from the `dist` directory.

2. **Move the `big_kirby.app`** file to your `Applications` folder (optional, but recommended).

3. **First Attempt to Open the App**:
    - Open Finder and navigate to the location of `big_kirby.app` (e.g., `dist/big_kirby.app`).
    - Double-click the `big_kirby.app` file.

4. **Handling the "Apple cannot check it for malicious software" Message**:
    - You will see a message: `"big_kirby.app” can’t be opened because Apple cannot check it for malicious software."`
    - Click **OK** to close the message.

5. **System Preferences**:
    - Open **System Preferences** from the Apple menu (``).
    - Go to **Security & Privacy**.
    - In the **General** tab, you will see a message about `big_kirby.app` being blocked.
    - Click the **Lock** icon in the lower-left corner to unlock the settings.
    - Click **Open Anyway** next to the message about `big_kirby.app`.

6. **Re-open the App**:
    - Navigate back to `big_kirby.app` in Finder.
    - Double-click `big_kirby.app` again.
    - A new message will appear: `"big_kirby.app” is an application downloaded from the internet. Are you sure you want to open it?`
    - Click **Open**.

### Additional Information

- If you encounter any issues, you can also run the app via Terminal:
    ```bash
    cd dist/big_kirby.app/Contents/MacOS/
    ./big_kirby
    ```

## Repository Structure

coding-with-kirby/

├── big_kirby.py

├── big_kirby.spec

├── dist/

│ └── big_kirby.app

├── README.md

├── requirements.txt

└── resources/

├── y3il.gif

├── y3il-reverse.gif

└── strberry.gif


## License

This project is licensed under the MIT License.
