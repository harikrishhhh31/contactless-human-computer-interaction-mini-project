import webview
import os

SERVER_URL = 'http://127.0.0.1:8000/'

def main():
    webview.create_window(
        'Heisenberg - Tutorial',
        url=SERVER_URL,
        width=900,
        height=700,
        resizable=True,
        background_color='#ffffff'
    )
    webview.start()

if __name__ == '__main__':
    main()
