import os
import shutil
import time
from pathlib import Path

# Configurações
PASTA_DESTINO = Path.home() / "Pictures" / "Backup_Celular"
INTERVALO_VERIFICACAO = 5  # verificar a cada 5 segundos

def obter_unidades_dcim():
    """Retorna uma lista de diretórios DCIM encontrados em unidades removíveis."""
    unidades_dcim = []
    
    # Em sistemas Windows, percorre as letras de unidade disponíveis (D: a Z:)
    for letra in range(68, 91):  # ASCII para D-Z
        caminho_drive = Path(f"{chr(letra)}:\\")
        if caminho_drive.exists():
            # Procura pela pasta DCIM comum em cartões SD ou conexões PTP/MTP que mapeiam letra
            caminho_dcim = caminho_drive / "DCIM"
            if caminho_dcim.exists() and caminho_dcim.is_dir():
                unidades_dcim.append(caminho_dcim)
                
    return unidades_dcim

def copiar_fotos(pasta_origem, pasta_destino):
    """Copia novos arquivos da pasta de origem para a de destino."""
    print(f"\n[INFO] Dispositivo com fotos detectado em: {pasta_origem}")
    print(f"[INFO] Iniciando backup para: {pasta_destino}")
    
    pasta_destino.mkdir(parents=True, exist_ok=True)
    arquivos_copiados = 0

    # Percorre recursivamente a pasta DCIM
    for raiz, _, arquivos in os.walk(pasta_origem):
        for arquivo in arquivos:
            ext = Path(arquivo).suffix.lower()
            # Filtra por extensões comuns de fotos e vídeos
            if ext in ['.jpg', '.jpeg', '.png', '.heic', '.mp4', '.mov']:
                caminho_completo_origem = Path(raiz) / arquivo
                
                # Mantém a estrutura de subpastas no destino
                caminho_relativo = caminho_completo_origem.relative_to(pasta_origem)
                caminho_completo_destino = pasta_destino / caminho_relativo
                
                # Evita sobrescrever arquivos já copiados anteriormente
                if not caminho_completo_destino.exists():
                    try:
                        caminho_completo_destino.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(caminho_completo_origem, caminho_completo_destino)
                        print(f"  [+] Copiado: {caminho_relativo}")
                        arquivos_copiados += 1
                    except Exception as e:
                        print(f"  [Erro] Falha ao copiar {arquivo}: {e}")
                        
    print(f"[FIM] Backup concluído. {arquivos_copiados} novos arquivos copiados.")

def monitorar_conexao():
    print("=" * 60)
    print("      MONITOR DE BACKUP AUTOMÁTICO DE FOTOS")
    print("=" * 60)
    print(f"Pasta de destino: {PASTA_DESTINO}")
    print("Aguardando conexão de dispositivo USB/Celular...")
    print("Nota: Lembre-se de desbloquear o celular e selecionar 'Transferir Fotos/Arquivos'.")
    print("Pressione Ctrl+C para encerrar o programa.")
    print("-" * 60)

    unidades_conhecidas = set(obter_unidades_dcim())

    try:
        while True:
            time.sleep(INTERVALO_VERIFICACAO)
            unidades_atuais = set(obter_unidades_dcim())
            
            # Detecta novas unidades que não estavam conectadas anteriormente
            novas_unidades = unidades_atuais - unidades_conhecidas
            
            for caminho_dcim in novas_unidades:
                # Executa a cópia
                copiar_fotos(caminho_dcim, PASTA_DESTINO)
                
            # Atualiza o estado das unidades conectadas
            unidades_conhecidas = unidades_atuais
            
    except KeyboardInterrupt:
        print("\n[INFO] Monitoramento encerrado pelo usuário.")

if __name__ == "__main__":
    monitorar_conexao()