# My New Project

This project is initialized with the same imports as the `# Start with imports` section from the `1_foundations/2_lab2.ipynb` notebook. It loads environment variables from your `.env` file using `load_dotenv()`.

## Getting Started

1. Make sure you have a `.env` file in your project root with the necessary API keys.
2. Install the required dependencies (see below).
3. Run `main.py` to start your project.

## Dependencies
- `python-dotenv`
- `openai`
- `anthropic`
- `IPython`

You can install them with:
```bash
pip install python-dotenv openai anthropic ipython
```

## Usage
Edit `main.py` to add your own code after the initial setup. 

## Troubleshooting

### Port 5050 is already in use
If you see an error like:

```
Address already in use
Port 5050 is in use by another program. Either identify and stop that program, or start the server with a different port.
```

This means another process (often a previous Flask server) is still running and using port 5050. To release the port:

1. **Find the process using port 5050:**
   ```sh
   lsof -i :5050
   ```
   This will show output like:
   ```
   COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
   python3  1234 jack   10u  IPv4 0x...      0t0  TCP localhost:5050 (LISTEN)
   ```
2. **Kill the process:**
   Replace `1234` with the PID from the previous command:
   ```sh
   kill 1234
   ```
   If the process does not terminate, force kill it:
   ```sh
   kill -9 1234
   ```
3. **Restart your Flask app.**

**Tip:** Always stop the Flask server with `CTRL+C` in the terminal to release the port cleanly. 