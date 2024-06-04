import subprocess
from diretorios import *
import os
def build_executable():
    # Caminho para o script principal
    main_script = "home.py"
    
    # Recursos para adicionar
    resources = [
        (DATABASE_DIR, "database"),
        (ICONS_DIR, "database/icons"),
        (IMAGE_PATH, "database/image"),
        (PLANEJAMENTO_DIR, "planejamento"),
        (TEMPLATE_PLANEJAMENTO_DIR, "planejamento/template"),
        (PASTA_TEMPLATE, "database/template"),
        (RELATORIO_PATH, "database"),
        (LV_FINAL_DIR, "database/Nova pasta"),
        (LV_BASE_DIR, "database/Nova pasta"),
        (WEBDRIVER_DIR, "database/selenium"),
        (TEMPLATE_DIR, "database/template"),
        (CP_DIR, "database/template/comunicacao_padronizada"),
        (CONTROLE_CONTRATOS_DIR, "controle_contratos"),
        (DATABASE_CONTRATOS, "controle_contratos/data_contratos"),
        (CP_CONTRATOS_DIR, "controle_contratos/comunicacao_padronizada")
    ]
    pyinstaller_args = [
        "pyinstaller",
        "--noconfirm",
        "--name=licitacao360",
        f"--icon={ICONE}",  # Especifique o caminho para o seu ícone aqui
        "--windowed",  # Se você quiser que o programa rode sem console
    ]

   # Adicionando importações ocultas
    pyinstaller_args.extend(["--hidden-import", "PyQt6"])
    pyinstaller_args.extend(["--hidden-import", "qdarkstyle"])
    pyinstaller_args.extend(["--hidden-import", "pdfplumber"])
    pyinstaller_args.extend(["--hidden-import", "openpyxl"])


    # Adicionando recursos com o separador correto
    for src, dest in resources:
        src_str = str(src) if isinstance(src, Path) else src
        data_string = f"{src_str};{dest}" if os.name == 'nt' else f"{src_str}:{dest}"
        pyinstaller_args.extend(["--add-data", data_string])

    pyinstaller_args.append(main_script)

    subprocess.run(pyinstaller_args)

if __name__ == "__main__":
    build_executable()