import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
import pickle
import keyboard

class MangaMapper:
    def __init__(self, root):
        self.root = root
        self.root.title("MangaBug - Auto Upload em Massa")
        self.root.geometry("1100x800")
        
        # Variáveis
        self.driver = None
        self.cadastrando = False
        self.cancelar = False
        self.config_file = "mangabug_config.json"
        self.log_file = "mangabug_log.txt"
        self.cookies_file = "cookies.pkl"
        self.config = {}
        self.mapeamento_ativo = False
        self.tipo_campo_atual = None
        
        # Carregar configurações
        self.load_config()
        
        # Configurar UI
        self.setup_ui()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text="🎯 MangaBug - Upload Automático em Massa", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Frame principal com duas colunas
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # ===== LADO ESQUERDO - CONFIGURAÇÕES =====
        
        # Frame de instruções
        instrucoes_frame = ttk.LabelFrame(left_frame, text="📋 Instruções", padding="10")
        instrucoes_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        instrucoes = """1. Abra o navegador e faça login
2. Vá até a página de cadastro
3. Mapeie os 4 campos com F2
4. Selecione a pasta dos capítulos
5. Defina o intervalo
6. Clique em INICIAR"""
        
        ttk.Label(instrucoes_frame, text=instrucoes, justify=tk.LEFT).grid(row=0, column=0, pady=5)
        
        # Frame de controle do navegador
        nav_frame = ttk.LabelFrame(left_frame, text="🌐 Navegador", padding="10")
        nav_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(nav_frame, text="URL:").grid(row=0, column=0, padx=5)
        self.url_var = tk.StringVar(value=self.config.get('url', 'https://mangabug-client-mangabug.up.railway.app/admin'))
        ttk.Entry(nav_frame, textvariable=self.url_var, width=50).grid(row=0, column=1, padx=5)
        
        btn_frame = ttk.Frame(nav_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="🌐 Abrir Navegador", command=self.abrir_navegador).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="🍪 Salvar Sessão", command=self.salvar_sessao).grid(row=0, column=1, padx=5)
        
        # Frame de mapeamento dos campos
        mapa_frame = ttk.LabelFrame(left_frame, text="🎯 Mapeamento dos Campos (pressione F2)", padding="10")
        mapa_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Campo Obra
        ttk.Label(mapa_frame, text="1. SELECIONAR OBRA:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.obra_info = tk.StringVar(value="⏳ Não mapeado")
        ttk.Label(mapa_frame, textvariable=self.obra_info, width=30).grid(row=0, column=1, padx=5)
        ttk.Button(mapa_frame, text="Mapear", command=lambda: self.iniciar_mapeamento('obra')).grid(row=0, column=2, padx=5)
        
        # Campo Capítulo
        ttk.Label(mapa_frame, text="2. Nº DO CAPÍTULO:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.capitulo_info = tk.StringVar(value="⏳ Não mapeado")
        ttk.Label(mapa_frame, textvariable=self.capitulo_info, width=30).grid(row=1, column=1, padx=5)
        ttk.Button(mapa_frame, text="Mapear", command=lambda: self.iniciar_mapeamento('capitulo')).grid(row=1, column=2, padx=5)
        
        # Campo Upload
        ttk.Label(mapa_frame, text="3. UPLOAD DE IMAGENS:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.upload_info = tk.StringVar(value="⏳ Não mapeado")
        ttk.Label(mapa_frame, textvariable=self.upload_info, width=30).grid(row=2, column=1, padx=5)
        ttk.Button(mapa_frame, text="Mapear", command=lambda: self.iniciar_mapeamento('upload')).grid(row=2, column=2, padx=5)
        
        # Botão Lançar
        ttk.Label(mapa_frame, text="4. LANÇAR CAPÍTULO:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.lancar_info = tk.StringVar(value="⏳ Não mapeado")
        ttk.Label(mapa_frame, textvariable=self.lancar_info, width=30).grid(row=3, column=1, padx=5)
        ttk.Button(mapa_frame, text="Mapear", command=lambda: self.iniciar_mapeamento('lancar')).grid(row=3, column=2, padx=5)
        
        # Status do mapeamento
        self.status_mapeamento_label = ttk.Label(mapa_frame, text="⏳ Aguardando mapeamento...", foreground="red")
        self.status_mapeamento_label.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(mapa_frame, text="🧹 Limpar Mapeamentos", command=self.limpar_mapeamentos).grid(row=5, column=1, pady=5)
        
        # Frame de intervalo de capítulos
        intervalo_frame = ttk.LabelFrame(left_frame, text="📚 Capítulos", padding="10")
        intervalo_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(intervalo_frame, text="Pasta Base:").grid(row=0, column=0, padx=5, pady=5)
        self.pasta_base_var = tk.StringVar(value=self.config.get('pasta_base', ''))
        ttk.Entry(intervalo_frame, textvariable=self.pasta_base_var, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(intervalo_frame, text="📁", command=self.selecionar_pasta, width=3).grid(row=0, column=2, padx=5)
        
        frame_caps = ttk.Frame(intervalo_frame)
        frame_caps.grid(row=1, column=0, columnspan=3, pady=5)
        
        ttk.Label(frame_caps, text="Inicial:").grid(row=0, column=0, padx=5)
        self.cap_inicial_var = tk.StringVar(value="44")
        ttk.Spinbox(frame_caps, from_=1, to=9999, textvariable=self.cap_inicial_var, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_caps, text="Final:").grid(row=0, column=2, padx=5)
        self.cap_final_var = tk.StringVar(value="97")
        ttk.Spinbox(frame_caps, from_=1, to=9999, textvariable=self.cap_final_var, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Button(frame_caps, text="🔍 Verificar", command=self.verificar_pastas).grid(row=0, column=4, padx=10)
        
        # Frame de opções
        opcoes_frame = ttk.LabelFrame(left_frame, text="⚙️ Opções", padding="10")
        opcoes_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(opcoes_frame, text="Delay entre capítulos (s):").grid(row=0, column=0, padx=5)
        self.delay_var = tk.StringVar(value="10")
        ttk.Entry(opcoes_frame, textvariable=self.delay_var, width=10).grid(row=0, column=1, padx=5)
        
        self.ordenar_imagens_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opcoes_frame, text="Ordenar imagens", variable=self.ordenar_imagens_var).grid(row=0, column=2, padx=10)
        
        # ===== LADO DIREITO - LOGS =====
        
        log_frame = ttk.LabelFrame(right_frame, text="📝 Log de Atividades", padding="10")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Frame para botões do log
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(log_btn_frame, text="🧹 Limpar Log", command=self.limpar_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_btn_frame, text="💾 Salvar Log", command=self.salvar_log).pack(side=tk.LEFT, padx=5)
        
        # Text widget para log com scrollbar
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_text_frame, height=25, width=60, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_scroll = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # ===== BARRA DE PROGRESSO E BOTÕES =====
        
        # Barra de progresso
        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=800)
        self.progress.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Botões de controle
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.btn_iniciar = ttk.Button(control_frame, text="🚀 INICIAR UPLOAD AUTOMÁTICO", 
                                      command=self.iniciar_upload, state='disabled', width=30)
        self.btn_iniciar.grid(row=0, column=0, padx=5)
        
        self.btn_cancelar = ttk.Button(control_frame, text="⛔ CANCELAR", 
                                       command=self.cancelar_upload, state='disabled', width=15)
        self.btn_cancelar.grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="💾 Salvar Config", command=self.salvar_config, width=15).grid(row=0, column=2, padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="✅ Pronto para começar", font=('Arial', 10))
        self.status_label.grid(row=4, column=0, columnspan=2)
        
        # Configurar peso
        main_frame.rowconfigure(1, weight=1)
    
    # ========== MÉTODOS DE LOG ==========
    
    def log(self, mensagem, tipo="INFO"):
        """Adicionar mensagem ao log com timestamp e tipo"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Definir ícone baseado no tipo
        if tipo == "ERRO":
            prefixo = "❌"
        elif tipo == "SUCESSO":
            prefixo = "✅"
        elif tipo == "AVISO":
            prefixo = "⚠️"
        else:
            prefixo = "ℹ️"
        
        linha = f"[{timestamp}] {prefixo} {mensagem}\n"
        
        # Inserir no final do texto
        self.log_text.insert(tk.END, linha)
        self.log_text.see(tk.END)
        self.root.update()
        
        # Salvar no arquivo de log
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensagem}\n")
        except:
            pass
    
    def limpar_log(self):
        """Limpar o conteúdo do log"""
        self.log_text.delete(1.0, tk.END)
        self.log("📝 Log limpo")
    
    def salvar_log(self):
        """Salvar log em um arquivo"""
        try:
            conteudo = self.log_text.get(1.0, tk.END)
            nome_arquivo = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            self.log(f"💾 Log salvo como {nome_arquivo}", "SUCESSO")
            messagebox.showinfo("Sucesso", f"Log salvo como {nome_arquivo}")
        except Exception as e:
            self.log(f"❌ Erro ao salvar log: {str(e)}", "ERRO")
    
    # ========== MÉTODOS DE CONFIGURAÇÃO ==========
    
    def load_config(self):
        """Carregar configurações do arquivo"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    
                # Carregar mapeamentos salvos
                if 'campos' in self.config:
                    campos = self.config['campos']
                    if 'obra' in campos:
                        self.obra_info.set(f"✅ {campos['obra']}")
                    if 'capitulo' in campos:
                        self.capitulo_info.set(f"✅ {campos['capitulo']}")
                    if 'upload' in campos:
                        self.upload_info.set(f"✅ {campos['upload']}")
                    if 'lancar' in campos:
                        self.lancar_info.set(f"✅ {campos['lancar']}")
                    
                    # Verificar se todos estão mapeados
                    self.verificar_mapeamentos()
            else:
                self.config = {}
        except Exception as e:
            self.log(f"Erro ao carregar config: {str(e)}", "ERRO")
            self.config = {}
    
    def salvar_config(self):
        """Salvar configurações no arquivo"""
        self.config['url'] = self.url_var.get()
        self.config['pasta_base'] = self.pasta_base_var.get()
        
        # Salvar mapeamentos
        campos = {}
        
        obra = self.obra_info.get()
        if '✅' in obra:
            campos['obra'] = obra.replace('✅ ', '')
        
        capitulo = self.capitulo_info.get()
        if '✅' in capitulo:
            campos['capitulo'] = capitulo.replace('✅ ', '')
        
        upload = self.upload_info.get()
        if '✅' in upload:
            campos['upload'] = upload.replace('✅ ', '')
        
        lancar = self.lancar_info.get()
        if '✅' in lancar:
            campos['lancar'] = lancar.replace('✅ ', '')
        
        self.config['campos'] = campos
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self.log("✅ Configurações salvas com sucesso!", "SUCESSO")
            messagebox.showinfo("Sucesso", "Configurações salvas!")
        except Exception as e:
            self.log(f"Erro ao salvar: {str(e)}", "ERRO")
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")
    
    # ========== MÉTODOS DO NAVEGADOR ==========
    
    def abrir_navegador(self):
        """Abrir navegador para login manual"""
        try:
            options = Options()
            options.add_argument('--start-maximized')
            
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.driver.get(self.url_var.get())
            
            self.log("🌐 Navegador aberto. Faça login manualmente.", "SUCESSO")
            
            # Tentar carregar cookies se existirem
            if os.path.exists(self.cookies_file):
                try:
                    with open(self.cookies_file, 'rb') as f:
                        cookies = pickle.load(f)
                        for cookie in cookies:
                            self.driver.add_cookie(cookie)
                    self.driver.refresh()
                    self.log("🍪 Cookies carregados com sucesso!", "SUCESSO")
                except Exception as e:
                    self.log(f"Erro ao carregar cookies: {str(e)}", "AVISO")
                    
        except Exception as e:
            self.log(f"Erro ao abrir navegador: {str(e)}", "ERRO")
            messagebox.showerror("Erro", f"Erro ao abrir navegador: {str(e)}")
    
    def salvar_sessao(self):
        """Salvar cookies da sessão atual"""
        if self.driver:
            try:
                with open(self.cookies_file, 'wb') as f:
                    pickle.dump(self.driver.get_cookies(), f)
                self.log("🍪 Sessão salva com sucesso!", "SUCESSO")
                messagebox.showinfo("Sucesso", "Sessão salva!")
            except Exception as e:
                self.log(f"Erro ao salvar sessão: {str(e)}", "ERRO")
        else:
            messagebox.showwarning("Aviso", "Navegador não está aberto!")
    
    # ========== MÉTODOS DE MAPEAMENTO ==========
    
    def iniciar_mapeamento(self, tipo_campo):
        """Iniciar o processo de mapeamento aguardando a tecla F2"""
        if not self.driver:
            messagebox.showwarning("Aviso", "Abra o navegador primeiro!")
            return
        
        self.log(f"🎯 Mapeando campo: {tipo_campo.upper()}")
        self.log(f"👉 Clique no campo e pressione F2")
        
        self.mapeamento_ativo = True
        self.tipo_campo_atual = tipo_campo
        
        # Atualizar status
        self.status_label.config(text=f"Aguardando F2 no campo {tipo_campo}...")
        
        # Iniciar thread para aguardar a tecla F2
        thread = threading.Thread(target=self.aguardar_f2)
        thread.daemon = True
        thread.start()
    
    def aguardar_f2(self):
        """Aguardar a tecla F2 ser pressionada"""
        tempo_inicio = time.time()
        while time.time() - tempo_inicio < 30:
            if keyboard.is_pressed('f2'):
                self.capturar_elemento_atual()
                break
            time.sleep(0.1)
        else:
            self.root.after(0, lambda: self.status_label.config(text="⏰ Tempo esgotado"))
            self.log("❌ Tempo esgotado para mapeamento", "ERRO")
        
        self.mapeamento_ativo = False
    
    def capturar_elemento_atual(self):
        """Capturar o elemento que está sob o mouse no navegador"""
        try:
            # Executar JavaScript para obter o elemento ativo
            script = """
            var elem = document.activeElement;
            if (elem && elem.tagName) {
                var selector = '';
                
                if (elem.id) {
                    selector = '#' + elem.id;
                } else if (elem.name) {
                    selector = '[name="' + elem.name + '"]';
                } else if (elem.className && typeof elem.className === 'string') {
                    var classes = elem.className.split(' ');
                    if (classes.length > 0 && classes[0]) {
                        selector = elem.tagName.toLowerCase() + '.' + classes[0];
                    } else {
                        selector = elem.tagName.toLowerCase();
                    }
                } else {
                    selector = elem.tagName.toLowerCase();
                }
                
                var info = {
                    selector: selector,
                    tag: elem.tagName,
                    id: elem.id,
                    name: elem.name,
                    class: elem.className,
                    type: elem.type
                };
                return info;
            }
            return null;
            """
            
            elemento_info = self.driver.execute_script(script)
            
            if elemento_info:
                seletor = elemento_info['selector']
                
                # Salvar seletor
                if self.tipo_campo_atual == 'obra':
                    self.root.after(0, lambda: self.obra_info.set(f"✅ {seletor}"))
                elif self.tipo_campo_atual == 'capitulo':
                    self.root.after(0, lambda: self.capitulo_info.set(f"✅ {seletor}"))
                elif self.tipo_campo_atual == 'upload':
                    self.root.after(0, lambda: self.upload_info.set(f"✅ {seletor}"))
                elif self.tipo_campo_atual == 'lancar':
                    self.root.after(0, lambda: self.lancar_info.set(f"✅ {seletor}"))
                
                self.log(f"✅ Campo mapeado: {seletor}", "SUCESSO")
                self.log(f"   Tag: {elemento_info['tag']}, ID: {elemento_info['id']}")
                
                # Verificar se todos os campos estão mapeados
                self.root.after(0, self.verificar_mapeamentos)
            else:
                self.log("❌ Não foi possível capturar o elemento", "ERRO")
            
        except Exception as e:
            self.log(f"Erro ao capturar elemento: {str(e)}", "ERRO")
    
    def verificar_mapeamentos(self):
        """Verificar se todos os campos estão mapeados e habilitar botão"""
        obra_ok = '✅' in self.obra_info.get()
        capitulo_ok = '✅' in self.capitulo_info.get()
        upload_ok = '✅' in self.upload_info.get()
        lancar_ok = '✅' in self.lancar_info.get()
        
        if obra_ok and capitulo_ok and upload_ok and lancar_ok:
            self.btn_iniciar.config(state='normal')
            self.status_mapeamento_label.config(text="✅ TODOS OS CAMPOS MAPEADOS!", foreground="green")
            self.log("🎉 Todos os campos mapeados! Pronto para iniciar!", "SUCESSO")
        else:
            faltam = []
            if not obra_ok: faltam.append("Obra")
            if not capitulo_ok: faltam.append("Capítulo")
            if not upload_ok: faltam.append("Upload")
            if not lancar_ok: faltam.append("Botão")
            
            self.status_mapeamento_label.config(text=f"⏳ Faltam: {', '.join(faltam)}", foreground="red")
    
    def limpar_mapeamentos(self):
        """Limpar todos os mapeamentos"""
        self.obra_info.set("⏳ Não mapeado")
        self.capitulo_info.set("⏳ Não mapeado")
        self.upload_info.set("⏳ Não mapeado")
        self.lancar_info.set("⏳ Não mapeado")
        self.btn_iniciar.config(state='disabled')
        self.status_mapeamento_label.config(text="⏳ Aguardando mapeamento...", foreground="red")
        self.log("🧹 Mapeamentos limpos")
    
    # ========== MÉTODOS DE PASTAS ==========
    
    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta base dos capítulos")
        if pasta:
            self.pasta_base_var.set(pasta)
            self.log(f"📁 Pasta base: {pasta}")
    
    def verificar_pastas(self):
        """Verificar se as pastas dos capítulos existem"""
        pasta_base = self.pasta_base_var.get()
        if not pasta_base or not os.path.exists(pasta_base):
            messagebox.showerror("Erro", "Pasta base não encontrada!")
            return
        
        try:
            cap_inicial = int(self.cap_inicial_var.get())
            cap_final = int(self.cap_final_var.get())
        except:
            messagebox.showerror("Erro", "Intervalo inválido!")
            return
        
        self.log(f"\n🔍 Verificando capítulos de {cap_inicial} a {cap_final}...")
        
        encontrados = 0
        total = cap_final - cap_inicial + 1
        
        for num in range(cap_inicial, cap_final + 1):
            # Tentar diferentes formatos de pasta
            possiveis_nomes = [
                f"Capítulo {num:03d}",
                f"Capitulo {num:03d}",
                f"Chapter {num:03d}",
                f"Cap. {num}",
                f"{num:03d}",
                f"Capítulo {num}",
                f"Capitulo {num}"
            ]
            
            encontrado = False
            for nome in possiveis_nomes:
                caminho = os.path.join(pasta_base, nome)
                if os.path.exists(caminho):
                    imagens = self.get_imagens_da_pasta(caminho)
                    if imagens:
                        encontrados += 1
                        self.log(f"  ✅ Capítulo {num}: {len(imagens)} imagens")
                        encontrado = True
                        break
            
            if not encontrado:
                self.log(f"  ❌ Capítulo {num}: pasta não encontrada", "AVISO")
        
        self.log(f"\n📊 Total: {encontrados} de {total} capítulos encontrados")
        
        if encontrados == total:
            messagebox.showinfo("Sucesso", f"Todos os {total} capítulos encontrados!")
        else:
            messagebox.showwarning("Atenção", f"Encontrados {encontrados} de {total} capítulos")
    
    def get_imagens_da_pasta(self, pasta):
        """Retorna lista de imagens na pasta, ordenadas"""
        imagens = []
        ext_validas = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        
        try:
            for arquivo in os.listdir(pasta):
                if arquivo.lower().endswith(ext_validas):
                    imagens.append(os.path.join(pasta, arquivo))
            
            # Ordenar por número da página
            if self.ordenar_imagens_var.get():
                imagens.sort(key=lambda x: self.extrair_numero_pagina(x))
        except Exception as e:
            self.log(f"Erro ao ler pasta: {str(e)}", "ERRO")
        
        return imagens
    
    def extrair_numero_pagina(self, caminho):
        """Extrai número da página do nome do arquivo"""
        nome = os.path.basename(caminho).lower()
        numeros = re.findall(r'\d+', nome)
        if numeros:
            return int(numeros[-1])
        return 0
    
    def encontrar_pasta_capitulo(self, numero):
        """Encontra a pasta do capítulo pelo número"""
        pasta_base = self.pasta_base_var.get()
        
        possiveis_nomes = [
            f"Capítulo {numero:03d}",
            f"Capitulo {numero:03d}",
            f"Chapter {numero:03d}",
            f"Cap. {numero}",
            f"{numero:03d}",
            f"Capítulo {numero}",
            f"Capitulo {numero}"
        ]
        
        for nome in possiveis_nomes:
            caminho = os.path.join(pasta_base, nome)
            if os.path.exists(caminho):
                return caminho
        
        return None
    
    # ========== MÉTODOS DE UPLOAD ==========
    
    def iniciar_upload(self):
        """Iniciar o processo automático de upload para TODOS os capítulos"""
        # Validar
        if not self.driver:
            messagebox.showerror("Erro", "Navegador não está aberto!")
            return
        
        if not self.pasta_base_var.get():
            messagebox.showerror("Erro", "Selecione a pasta base!")
            return
        
        try:
            cap_inicial = int(self.cap_inicial_var.get())
            cap_final = int(self.cap_final_var.get())
            if cap_inicial > cap_final:
                messagebox.showerror("Erro", "Capítulo inicial não pode ser maior que o final!")
                return
        except:
            messagebox.showerror("Erro", "Intervalo inválido!")
            return
        
        total = cap_final - cap_inicial + 1
        msg = f"🚀 INICIAR UPLOAD AUTOMÁTICO?\n\n"
        msg += f"📚 Capítulos: {cap_inicial} a {cap_final} ({total} capítulos)\n"
        msg += f"⏱️ Delay: {self.delay_var.get()}s\n\n"
        msg += "⚠️ NÃO MEXA no mouse/teclado durante o processo!\n\n"
        msg += "Deseja continuar?"
        
        if not messagebox.askyesno("Confirmar", msg):
            return
        
        # Desabilitar botões
        self.btn_iniciar.config(state='disabled')
        self.btn_cancelar.config(state='normal')
        
        self.cadastrando = True
        self.cancelar = False
        
        self.log("\n" + "="*60)
        self.log("🚀 INICIANDO UPLOAD AUTOMÁTICO")
        self.log(f"📚 Capítulos: {cap_inicial} a {cap_final}")
        self.log("="*60)
        
        # Iniciar thread
        thread = threading.Thread(target=self.processar_upload)
        thread.daemon = True
        thread.start()
    
    def processar_upload(self):
        """Processar o upload dos capítulos"""
        try:
            cap_inicial = int(self.cap_inicial_var.get())
            cap_final = int(self.cap_final_var.get())
            total = cap_final - cap_inicial + 1
            
            for idx, num in enumerate(range(cap_inicial, cap_final + 1), 1):
                if self.cancelar:
                    self.log("⛔ Upload cancelado pelo usuário")
                    break
                
                self.log(f"\n📚 Processando capítulo {num} ({idx}/{total})...")
                
                # Atualizar progresso
                progresso = (idx / total) * 100
                self.root.after(0, self.atualizar_progresso, progresso)
                
                # Encontrar pasta do capítulo
                pasta_capitulo = self.encontrar_pasta_capitulo(num)
                
                if not pasta_capitulo:
                    self.log(f"❌ Pasta do capítulo {num} não encontrada", "ERRO")
                    continue
                
                # Pegar imagens
                imagens = self.get_imagens_da_pasta(pasta_capitulo)
                if not imagens:
                    self.log(f"❌ Nenhuma imagem encontrada no capítulo {num}", "ERRO")
                    continue
                
                self.log(f"📁 {len(imagens)} imagens encontradas")
                
                # Preencher formulário
                if not self.preencher_formulario(num, imagens):
                    self.log(f"❌ Falha no capítulo {num}", "ERRO")
                    continue
                
                self.log(f"✅ Capítulo {num} concluído!", "SUCESSO")
                
                # Aguardar delay
                if idx < total:
                    delay = int(self.delay_var.get())
                    self.log(f"⏱️ Aguardando {delay}s...")
                    time.sleep(delay)
            
            self.log("\n" + "="*60)
            self.log("✅ UPLOAD FINALIZADO!", "SUCESSO")
            
        except Exception as e:
            self.log(f"❌ ERRO GERAL: {str(e)}", "ERRO")
        
        finally:
            self.root.after(0, self.finalizar_upload)
    
    def preencher_formulario(self, numero_capitulo, imagens):
        """Preencher o formulário usando os seletores mapeados"""
        try:
            driver = self.driver
            
            # Extrair seletores
            seletor_obra = self.obra_info.get().replace('✅ ', '')
            seletor_capitulo = self.capitulo_info.get().replace('✅ ', '')
            seletor_upload = self.upload_info.get().replace('✅ ', '')
            seletor_lancar = self.lancar_info.get().replace('✅ ', '')
            
            # 1. SELECIONAR OBRA
            self.log("📌 Selecionando obra...")
            try:
                elemento_obra = driver.find_element(By.CSS_SELECTOR, seletor_obra)
                elemento_obra.click()
                time.sleep(1)
                
                # Se for um campo de texto, pode precisar digitar
                if elemento_obra.tag_name.lower() == 'input':
                    elemento_obra.clear()
                    elemento_obra.send_keys("Assassino")
                    time.sleep(1)
                    elemento_obra.send_keys(Keys.ENTER)
            except Exception as e:
                self.log(f"⚠️ Erro ao selecionar obra: {str(e)}", "AVISO")
            
            # 2. PREENCHER CAPÍTULO - VERSÃO CORRIGIDA
            self.log(f"🔢 Preenchendo capítulo {numero_capitulo}...")
            try:
                # Aguardar um pouco
                time.sleep(1)
                
                # Encontrar elemento
                elemento_capitulo = driver.find_element(By.CSS_SELECTOR, seletor_capitulo)
                
                # Limpar campo de múltiplas formas
                elemento_capitulo.clear()
                driver.execute_script("arguments[0].value = '';", elemento_capitulo)
                elemento_capitulo.send_keys(Keys.CONTROL + 'a')
                elemento_capitulo.send_keys(Keys.DELETE)
                time.sleep(0.5)
                
                # Digitar número
                texto_capitulo = str(numero_capitulo)
                
                # Usar JavaScript para definir o valor diretamente (mais confiável)
                driver.execute_script(f"arguments[0].value = '{texto_capitulo}';", elemento_capitulo)
                
                # Disparar eventos para o site reconhecer a mudança
                driver.execute_script("""
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """, elemento_capitulo)
                
                # Verificar o valor
                valor_final = elemento_capitulo.get_attribute('value')
                self.log(f"   Valor final: '{valor_final}'")
                
                if valor_final != texto_capitulo:
                    self.log(f"⚠️ Valor diferente. Tentando novamente...", "AVISO")
                    # Segunda tentativa
                    driver.execute_script(f"arguments[0].value = '{texto_capitulo}';", elemento_capitulo)
                    
            except Exception as e:
                self.log(f"⚠️ Erro ao preencher capítulo: {str(e)}", "AVISO")
                # Tentar método alternativo
                try:
                    driver.execute_script(f"document.querySelector('{seletor_capitulo}').value = '{numero_capitulo}';")
                except:
                    pass
            
            # 3. UPLOAD DAS IMAGENS
            self.log("📤 Fazendo upload...")
            try:
                elemento_upload = driver.find_element(By.CSS_SELECTOR, seletor_upload)
                
                # Upload múltiplo
                if len(imagens) == 1:
                    elemento_upload.send_keys(imagens[0])
                else:
                    # Para upload múltiplo, enviar todos os caminhos
                    elemento_upload.send_keys("\n".join(imagens))
                
                self.log(f"✅ {len(imagens)} imagens enviadas", "SUCESSO")
                time.sleep(3)
            except Exception as e:
                self.log(f"⚠️ Erro no upload: {str(e)}", "AVISO")
            
            # 4. CLICAR EM LANÇAR
            self.log("🚀 Lançando capítulo...")
            try:
                elemento_lancar = driver.find_element(By.CSS_SELECTOR, seletor_lancar)
                
                # Rolar até o elemento
                driver.execute_script("arguments[0].scrollIntoView(true);", elemento_lancar)
                time.sleep(1)
                
                elemento_lancar.click()
                time.sleep(2)
            except Exception as e:
                self.log(f"⚠️ Erro ao clicar em Lançar: {str(e)}", "AVISO")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erro no formulário: {str(e)}", "ERRO")
            return False
    
    def atualizar_progresso(self, valor):
        """Atualizar a barra de progresso"""
        self.progress['value'] = valor
        self.root.update_idletasks()
    
    def finalizar_upload(self):
        """Finalizar o processo de upload"""
        self.cadastrando = False
        self.btn_iniciar.config(state='normal')
        self.btn_cancelar.config(state='disabled')
        self.progress['value'] = 0
        self.status_label.config(text="✅ Processo finalizado")
    
    def cancelar_upload(self):
        """Cancelar o upload em andamento"""
        self.cancelar = True
        self.log("⛔ Cancelando upload...")

if __name__ == "__main__":
    root = tk.Tk()
    app = MangaMapper(root)
    root.mainloop()