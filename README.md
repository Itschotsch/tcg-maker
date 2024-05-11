# TCG Maker
A way to automate the creation of TCG cards from a CSV table using HTML and CSS. Written in Python. Not very versatile yet as it was only designed for a very specific usecase.

## Installation
### Using Docker-Compose (Recommended)
1. Install Docker and Docker-Compose.
2. `sudo docker-compose up -d`. Do not use `-d` if you want to see the output.
3. Go to `localhost:8000` in your browser.

### Directly on Your Machine (Not Recommended)
1. Make sure you have TKinter installed. You can install it with `sudo apt-get install python3-tk`.
2. `conda create -n tcg-maker python=3.11`
3. `conda activate tcg-maker`
4. `pip install -r requirements.txt`
5. `python3 -m playwright install`
6. If you're on Ubuntu: `sudo apt-get install libgbm1 libasound2`

## Usage
- `python3 main.py --ip localhost --port 8000` launches a web interface on `localhost:8000`.
- `nohup python3 main.py --ip localhost --port 8000 &` launches a web interface on `localhost:8000` in the background.
