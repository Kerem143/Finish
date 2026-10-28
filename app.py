from flask import Flask, render_template_string, request
import os
import subprocess
import threading

app = Flask(__name__)
CODES_DIR = 'codes'

if not os.path.exists(CODES_DIR):
    os.makedirs(CODES_DIR)

active_process = None
output_log = ""

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>C++ Terminal Paneli</title>
    <script>
        // Sayfa yenilendiğinde konsol ekranını en aşağı (son mesaja) kaydırır
        window.onload = function() {
            var consoleBox = document.getElementById("console-box");
            consoleBox.scrollTop = consoleBox.scrollHeight;
        };
    </script>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #0d1117; color: #c9d1d9;">
    <div style="background: #161b22; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); max-width: 800px; margin: auto; border: 1px solid #30363d;">
        <h2 style="margin-top: 0; color: #58a6ff;">🚀 C++ Docker Terminal Paneli</h2>
        
        <!-- Dosya Seçme ve Başlatma Formu -->
        <form method="POST" action="/start" style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
            <select name="filename" style="padding: 10px; width: 70%; background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; font-size: 14px;">
                {% for file in files %}
                    <option value="{{ file }}" {% if file == selected_file %}selected{% endif %}>{{ file }}</option>
                {% endfor %}
            </select>
            <button type="submit" style="padding: 10px 20px; background: #238636; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">Programı Başlat</button>
        </form>

        <hr style="border: 0; border-top: 1px solid #30363d; margin: 20px 0;">

        <!-- Konsol Ekranı -->
        <div style="font-size: 13px; color: #8b949e; margin-bottom: 5px;">Terminal Çıktısı:</div>
        <pre id="console-box" style="background: #010409; color: #56d364; padding: 15px; border-radius: 6px; font-family: 'Courier New', Courier, monospace; height: 280px; overflow-y: auto; white-space: pre-wrap; border: 1px solid #30363d; font-size: 14px; line-height: 1.4;">{{ output }}</pre>

        <!-- Girdi Gönderme Formu -->
        <form method="POST" action="/send" style="margin-top: 15px; display: flex; gap: 10px;">
            <input type="text" name="user_input" placeholder="Bir değer girin ve Enter'a basın..." style="flex: 1; padding: 12px; background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; font-family: monospace; font-size: 14px;" autocomplete="off" autofocus required>
            <button type="submit" style="padding: 12px 24px; background: #1f6feb; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">Gönder</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    global output_log
    files = [f for f in os.listdir(CODES_DIR) if f.endswith('.cpp')]
    return render_template_string(HTML_TEMPLATE, files=files, output=output_log, selected_file="")

@app.route('/start', methods=['POST'])
def start_program():
    global active_process, output_log
    filename = request.form.get('filename')
    
    if active_process and active_process.poll() is None:
        active_process.terminate()
        
    if filename:
        file_path = os.path.join(CODES_DIR, filename)
        exe_path = os.path.join(CODES_DIR, "output_prog")
        
        # Derleme
        compile_res = subprocess.run(['g++', file_path, '-o', exe_path], capture_output=True, text=True)
        if compile_res.returncode != 0:
            output_log = "Derleme Hatası:\n" + compile_res.stderr
        else:
            output_log = ""  # Başlangıçtaki o süslü yazıları tamamen kaldırdık, tertemiz ekran!
            active_process = subprocess.Popen(
                [exe_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            def read_output():
                global output_log, active_process
                while active_process and active_process.poll() is None:
                    char = active_process.stdout.read(1)
                    if char:
                        output_log += char
                    else:
                        break
            
            t = threading.Thread(target=read_output, daemon=True)
            t.start()

    files = [f for f in os.listdir(CODES_DIR) if f.endswith('.cpp')]
    return render_template_string(HTML_TEMPLATE, files=files, output=output_log, selected_file=filename)

@app.route('/send', methods=['POST'])
def send_input():
    global active_process, output_log
    user_input = request.form.get('user_input', '')
    
    if active_process and active_process.poll() is None:
        try:
            active_process.stdin.write(user_input + '\n')
            active_process.stdin.flush()
            output_log += user_input + "\n"
        except Exception as e:
            output_log += f"\nHata: {str(e)}\n"

    files = [f for f in os.listdir(CODES_DIR) if f.endswith('.cpp')]
    return render_template_string(HTML_TEMPLATE, files=files, output=output_log)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)