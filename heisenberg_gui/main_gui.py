import webview

def main():
    webview.create_window(
        'Heisenberg - Tutorial',
        url='http://127.0.0.1:8000/',
        width=900,
        height=700,
        resizable=True,
        background_color='#ffffff'
    )
    webview.start()

if __name__ == '__main__':
    main()
