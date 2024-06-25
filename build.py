import subprocess
from diretorios import *
import os

def build_executable():
    # Imprime o diretório de trabalho atual para diagnóstico
    print("Current working directory:", os.getcwd())

    # Caminho absoluto para o script principal dentro do subdiretório 'licitacao360'
    main_script = os.path.join(os.getcwd(), "licitacao360", "home.py")

    # Verifica se o arquivo principal existe
    if not os.path.exists(main_script):
        print("Script file 'home.py' does not exist in the current directory.")
        return
    
    # Recursos para adicionar
    resources = [
        (DATABASE_DIR, "database"),
        (ICONS_DIR, "database/icons"),
        (IMAGE_PATH, "database/image"),
        (PLANEJAMENTO_DIR, "planejamento"),
        (TEMPLATE_PLANEJAMENTO_DIR, "planejamento/template"),
        (PASTA_TEMPLATE, "database/template"),
        (RELATORIO_PATH, "database"),
        (WEBDRIVER_DIR, "database/selenium"),
        (TEMPLATE_DIR, "database/template"),
    ]
    pyinstaller_args = [
        "pyinstaller",
        "--noconfirm",
        "--name=licitacao360",
        f"--icon={ICONE}",  # Especifique o caminho para o seu ícone aqui
        # "--windowed",  # Se você quiser que o programa rode sem console
    ]

    # Adicionando recursos com o separador correto
    for src, dest in resources:
        src_str = str(src) if isinstance(src, Path) else src
        data_string = f"{src_str};{dest}" if os.name == 'nt' else f"{src_str}:{dest}"
        pyinstaller_args.extend(["--add-data", data_string])

    pyinstaller_args.append(main_script)

    subprocess.run(pyinstaller_args)

if __name__ == "__main__":
    build_executable()