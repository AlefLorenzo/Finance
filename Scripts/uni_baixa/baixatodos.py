#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LYCANTOONS DOWNLOADER - Versão com Selenium (para sites dinâmicos)
"""

import os
import re
import time
import threading
import queue
import urllib.request
from urllib.parse import urljoin
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

# Tentar importar Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager # type: ignore
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class LycanToonsDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("📚 LYCANTOONS DOWNLOADER - Selenium")
        self.root.geometry("1400x800")
        
        # Controles
        self.downloading = False
        self.url_queue = queue.Queue()
        self.driver = None
        
        # Dados
        self.capitulos = []
        self.stats = {'capitulos': 0, 'paginas': 0, 'erros': 0}
        
        # Configurações
        self.output_dir = ""
        self.max_threads = 1  # Selenium só pode usar 1 thread
        self.delay = 3
        
        # Headers para downloads de imagem
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,*/*',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Connection': 'keep-alive',
        }
        
        self.setup_ui()
        
        # Verificar Selenium
        if not SELENIUM_AVAILABLE:
            messagebox.showwarning("Aviso", 
                "Selenium não está instalado!\n\n"
                "Instale com:\n"
                "pip install selenium webdriver-manager")
        
    def setup_ui(self):
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=0, column=0, sticky="nsew")
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)
        
        # Título
        ttk.Label(main, text="📚 LYCANTOONS DOWNLOADER - Selenium", 
                 font=('Arial', 18, 'bold')).grid(row=0, column=0, pady=10)
        
        # Status do Selenium
        status_selenium = "✅ Disponível" if SELENIUM_AVAILABLE else "❌ Não instalado"
        ttk.Label(main, text=f"Selenium: {status_selenium}", 
                 foreground="green" if SELENIUM_AVAILABLE else "red").grid(row=0, column=0, sticky="e", padx=10)
        
        # URL da Série
        url_frame = ttk.LabelFrame(main, text="📌 URL da SÉRIE", padding="10")
        url_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, padx=5)
        self.url_var = tk.StringVar(value="https://lycantoons.com/series/meio-sangue")
        ttk.Entry(url_frame, textvariable=self.url_var, width=80).grid(row=0, column=1, padx=5, sticky="ew")
        
        btn_frame = ttk.Frame(url_frame)
        btn_frame.grid(row=0, column=2, padx=5)
        
        self.btn_extrair = ttk.Button(btn_frame, text="🌐 ABRIR NAVEGADOR", 
                                       command=self.abrir_navegador, width=18)
        self.btn_extrair.pack(side=tk.LEFT, padx=2)
        
        self.btn_capitulos = ttk.Button(btn_frame, text="📋 EXTRAIR CAPÍTULOS", 
                                        command=self.extrair_capitulos, state='disabled', width=18)
        self.btn_capitulos.pack(side=tk.LEFT, padx=2)
        
        url_frame.columnconfigure(1, weight=1)
        
        # Configurações
        config_frame = ttk.LabelFrame(main, text="⚙️ Configurações", padding="10")
        config_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        ttk.Label(config_frame, text="Pasta:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.output_var = tk.StringVar(value="./downloads")
        ttk.Entry(config_frame, textvariable=self.output_var, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="📂", command=self.selecionar_pasta, width=3).grid(row=0, column=2, padx=5)
        
        ttk.Label(config_frame, text="Delay (s):").grid(row=0, column=3, padx=5, sticky="w")
        self.delay_var = tk.StringVar(value="3")
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.delay_var, width=5).grid(row=0, column=4, padx=5)
        
        # Intervalo de capítulos
        intervalo_frame = ttk.Frame(config_frame)
        intervalo_frame.grid(row=1, column=0, columnspan=5, pady=10, sticky="w")
        
        ttk.Label(intervalo_frame, text="Baixar do capítulo:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.cap_inicial_var = tk.StringVar(value="0")
        ttk.Spinbox(intervalo_frame, from_=0, to=200, textvariable=self.cap_inicial_var, width=5).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(intervalo_frame, text="até o capítulo:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.cap_final_var = tk.StringVar(value="41")
        ttk.Spinbox(intervalo_frame, from_=0, to=200, textvariable=self.cap_final_var, width=5).pack(side=tk.LEFT, padx=2)
        
        # Lista de capítulos
        lista_frame = ttk.LabelFrame(main, text="📖 Capítulos Encontrados", padding="10")
        lista_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        lista_frame.columnconfigure(0, weight=1)
        lista_frame.rowconfigure(0, weight=1)
        
        columns = ('Nº', 'URL', 'Status')
        self.tree = ttk.Treeview(lista_frame, columns=columns, show='headings', height=12)
        self.tree.heading('Nº', text='Capítulo')
        self.tree.heading('URL', text='URL')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('Nº', width=60)
        self.tree.column('URL', width=500)
        self.tree.column('Status', width=120)
        
        scroll = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        
        # Botões
        btn_frame2 = ttk.Frame(lista_frame)
        btn_frame2.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.btn_download = ttk.Button(btn_frame2, text="🚀 BAIXAR INTERVALO", 
                                       command=self.iniciar_download, state='disabled')
        self.btn_download.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = ttk.Button(btn_frame2, text="⏹️ PARAR", 
                                   command=self.parar_download, state='disabled')
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        
        # Log
        log_frame = ttk.LabelFrame(main, text="📝 Log", padding="5")
        log_frame.grid(row=4, column=0, sticky="ew", pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, font=('Consolas', 9))
        self.log_text.pack(fill=tk.X)
        
        # Tags de cores
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCESSO", foreground="green")
        self.log_text.tag_configure("ERRO", foreground="red")
        self.log_text.tag_configure("AVISO", foreground="orange")
        self.log_text.tag_configure("DETECT", foreground="blue")
        
        # Estatísticas
        stats_frame = ttk.Frame(main)
        stats_frame.grid(row=5, column=0, sticky="ew", pady=5)
        
        self.stats_labels = {}
        stats_items = [('Capítulos:', 'capitulos'), ('Páginas:', 'paginas'), ('Erros:', 'erros')]
        
        for i, (texto, chave) in enumerate(stats_items):
            ttk.Label(stats_frame, text=texto).grid(row=0, column=i*2, padx=5)
            self.stats_labels[chave] = ttk.Label(stats_frame, text="0")
            self.stats_labels[chave].grid(row=0, column=i*2+1, padx=5)
        
        # Progresso
        self.progress = ttk.Progressbar(main, mode='indeterminate', length=800)
        self.progress.grid(row=6, column=0, pady=5)
        
        # Status
        self.status_label = ttk.Label(main, text="✅ Pronto")
        self.status_label.grid(row=7, column=0, pady=5)
        
    # ===== FUNÇÕES BÁSICAS =====
    
    def log(self, msg, tipo="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n", tipo)
        self.log_text.see(tk.END)
        self.root.update()
    
    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.output_var.set(pasta)
    
    def atualizar_stats(self):
        self.stats_labels['capitulos'].config(text=str(self.stats['capitulos']))
        self.stats_labels['paginas'].config(text=str(self.stats['paginas']))
        self.stats_labels['erros'].config(text=str(self.stats['erros']))
        self.root.update()
    
    # ===== SELENIUM =====
    
    def abrir_navegador(self):
        """Abrir navegador para interação manual"""
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("Erro", "Selenium não está instalado!")
            return
        
        try:
            options = Options()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            
            self.log("🌐 Iniciando Chrome...", "INFO")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            url = self.url_var.get().strip()
            self.driver.get(url)
            
            self.log("✅ Navegador aberto!", "SUCESSO")
            self.log("⏳ Aguarde o site carregar completamente...", "INFO")
            self.log("👉 Depois clique em 'EXTRAIR CAPÍTULOS'", "INFO")
            
            self.btn_capitulos.config(state='normal')
            self.btn_extrair.config(state='disabled')
            
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}", "ERRO")
            messagebox.showerror("Erro", f"Falha ao abrir navegador:\n{str(e)}")
    
    def extrair_capitulos(self):
        """Extrair capítulos usando Selenium"""
        if not self.driver:
            messagebox.showerror("Erro", "Abra o navegador primeiro!")
            return
        
        self.log("🔍 Extraindo capítulos...", "DETECT")
        
        try:
            # Esperar elementos carregarem
            time.sleep(3)
            
            # Encontrar todos os links de capítulos
            # Baseado na estrutura observada: divs com texto "Cap. X"
            elementos = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Cap.')]")
            
            self.capitulos = []
            base_url = '/'.join(self.url_var.get().split('/')[:3])
            
            for elem in elementos:
                texto = elem.text
                match = re.search(r'Cap\.?\s*(\d+)', texto)
                if match:
                    num = int(match.group(1))
                    
                    # Tentar encontrar o link associado
                    try:
                        link_elem = elem.find_element(By.XPATH, "./..")
                        href = link_elem.get_attribute('href')
                    except:
                        # Se não achar link, construir URL padrão
                        href = f"{base_url}/{num}"
                    
                    if href and href not in [c['url'] for c in self.capitulos]:
                        self.capitulos.append({
                            'numero': num,
                            'url': href
                        })
                        self.log(f"   ✅ Capítulo {num} encontrado", "DETECT")
            
            # Ordenar
            self.capitulos.sort(key=lambda x: x['numero'])
            
            if self.capitulos:
                # Limpar tree
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                for cap in self.capitulos:
                    self.tree.insert('', 'end', values=(
                        cap['numero'],
                        cap['url'][:60] + '...',
                        'Detectado'
                    ))
                
                # Atualizar intervalo
                min_cap = min(c['numero'] for c in self.capitulos)
                max_cap = max(c['numero'] for c in self.capitulos)
                self.cap_inicial_var.set(str(min_cap))
                self.cap_final_var.set(str(max_cap))
                
                self.log(f"✅ Total: {len(self.capitulos)} capítulos", "SUCESSO")
                self.btn_download.config(state='normal')
            else:
                self.log("⚠️ Nenhum capítulo encontrado!", "AVISO")
            
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}", "ERRO")
    
    # ===== DOWNLOAD =====
    
    def baixar_imagem(self, url_img, pasta_destino, nome_arquivo, referer):
        """Baixar uma imagem"""
        try:
            path = os.path.join(pasta_destino, nome_arquivo)
            if os.path.exists(path):
                return True
            
            headers = self.headers.copy()
            headers['Referer'] = referer
            
            req = urllib.request.Request(url_img, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(path, 'wb') as f:
                    f.write(response.read())
            
            return True
        except Exception as e:
            self.log(f"   ❌ Erro imagem: {str(e)[:30]}", "ERRO")
            return False
    
    def processar_capitulo(self, capitulo):
        """Processar download de um capítulo usando o navegador"""
        num = capitulo['numero']
        url = capitulo['url']
        
        self.log(f"\n📖 Processando capítulo {num}", "INFO")
        
        try:
            # Navegar para o capítulo
            self.driver.get(url)
            time.sleep(int(self.delay_var.get()))
            
            # Extrair URLs das imagens
            imagens = self.driver.execute_script("""
                // Procurar todas as imagens que parecem ser páginas
                const imagens = [];
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.dataset.src;
                    if (src && (src.includes('page') || src.match(/\d+\.(jpg|png|webp)/))) {
                        imagens.push(src);
                    }
                });
                return imagens;
            """)
            
            if not imagens:
                self.log(f"   ❌ Nenhuma imagem encontrada!", "ERRO")
                self.stats['erros'] += 1
                self.atualizar_stats()
                return
            
            self.log(f"   ✅ {len(imagens)} imagens encontradas", "SUCESSO")
            
            # Criar pasta
            nome_serie = self.url_var.get().strip().split('/')[-1]
            pasta_serie = os.path.join(self.output_var.get(), nome_serie)
            pasta_cap = os.path.join(pasta_serie, f"Capítulo {num:03d}")
            os.makedirs(pasta_cap, exist_ok=True)
            
            # Baixar imagens
            imagens_baixadas = 0
            for i, img_url in enumerate(imagens, 1):
                if not self.downloading:
                    break
                
                ext = os.path.splitext(img_url.split('?')[0])[1]
                if not ext or len(ext) > 5:
                    ext = '.jpg'
                
                nome_arquivo = f"pagina_{i:03d}{ext}"
                
                if self.baixar_imagem(img_url, pasta_cap, nome_arquivo, url):
                    imagens_baixadas += 1
                    self.log(f"   📄 Página {i} OK", "INFO")
                    time.sleep(1)
                else:
                    self.stats['erros'] += 1
            
            self.stats['capitulos'] += 1
            self.stats['paginas'] += imagens_baixadas
            self.log(f"✅ Capítulo {num} concluído ({imagens_baixadas}/{len(imagens)} páginas)", "SUCESSO")
            
            # Atualizar tree
            for item in self.tree.get_children():
                valores = self.tree.item(item)['values']
                if len(valores) > 0 and valores[0] == num:
                    self.tree.set(item, 'Status', f'✅ {imagens_baixadas}/{len(imagens)}')
                    break
            
            self.atualizar_stats()
            
        except Exception as e:
            self.log(f"❌ Erro: {str(e)}", "ERRO")
            self.stats['erros'] += 1
            self.atualizar_stats()
    
    def worker(self):
        """Thread worker"""
        while self.downloading:
            try:
                capitulo = self.url_queue.get(timeout=1)
                self.processar_capitulo(capitulo)
            except queue.Empty:
                continue
    
    def iniciar_download(self):
        """Iniciar download do intervalo selecionado"""
        if not self.capitulos:
            messagebox.showwarning("Aviso", "Extraia os capítulos primeiro!")
            return
        
        if not self.driver:
            messagebox.showwarning("Aviso", "O navegador precisa estar aberto!")
            return
        
        try:
            cap_inicial = int(self.cap_inicial_var.get())
            cap_final = int(self.cap_final_var.get())
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos!")
            return
        
        if cap_inicial > cap_final:
            messagebox.showerror("Erro", "Intervalo inválido!")
            return
        
        selecionados = [c for c in self.capitulos if cap_inicial <= c['numero'] <= cap_final]
        
        if not selecionados:
            messagebox.showwarning("Aviso", "Nenhum capítulo no intervalo!")
            return
        
        # Confirmar
        if not messagebox.askyesno("Confirmar", 
            f"Baixar {len(selecionados)} capítulos (do {cap_inicial} ao {cap_final})?"):
            return
        
        # Resetar stats
        self.stats = {'capitulos': 0, 'paginas': 0, 'erros': 0}
        self.atualizar_stats()
        
        # Iniciar
        self.downloading = True
        self.progress.start()
        self.btn_download.config(state='disabled')
        self.btn_stop.config(state='normal')
        
        self.log("\n" + "="*60, "INFO")
        self.log(f"🚀 INICIANDO DOWNLOAD DOS CAPÍTULOS {cap_inicial} AO {cap_final}", "INFO")
        self.log("="*60, "INFO")
        
        # Adicionar à fila
        for cap in selecionados:
            self.url_queue.put(cap)
        
        # Iniciar thread (apenas 1 com Selenium)
        t = threading.Thread(target=self.worker, daemon=True)
        t.start()
        
        self.status_label.config(text="🔍 Download em andamento...")
    
    def parar_download(self):
        """Parar download"""
        self.downloading = False
        self.progress.stop()
        self.btn_download.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.status_label.config(text="⏹️ Interrompido")
        self.log("⏹️ Download interrompido", "AVISO")
        
        if self.driver:
            self.driver.quit()
            self.driver = None

if __name__ == "__main__":
    root = tk.Tk()
    app = LycanToonsDownloader(root)
    root.mainloop()