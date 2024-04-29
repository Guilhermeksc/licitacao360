from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from pathlib import Path
from diretorios import *
import pandas as pd
global df_registro_selecionado
df_registro_selecionado = None
import sqlite3
from datetime import datetime

class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.database_path = Path(CONTROLE_DADOS) 
        self.setWindowTitle("Adicionar Item")
        self.layout = QVBoxLayout(self)

        self.options = [
            ("Pregão Eletrônico (PE)", "Pregão Eletrônico"),
            ("Concorrência (CC)", "Concorrência"),
            ("Dispensa Eletrônica (DE)", "Dispensa Eletrônica"),
            ("Termo de Justificativa de Dispensa Eletrônica (TJDL)", "Termo de Justificativa de Dispensa Eletrônica"),
            ("Termo de Justificativa de Inexigibilidade de Licitação (TJIL)", "Termo de Justificativa de Inexigibilidade de Licitação")
        ]

        # Linha 1: Tipo, Número, Ano
        hlayout1 = QHBoxLayout()
        self.tipo_cb = QComboBox()
        self.numero_le = QLineEdit()
        self.ano_le = QLineEdit()

        # Carregar o próximo número disponível
        self.load_next_numero()

        [self.tipo_cb.addItem(text) for text, _ in self.options]
        self.tipo_cb.setCurrentText("Pregão Eletrônico (PE)")  # Valor padrão
        hlayout1.addWidget(QLabel("Tipo:"))
        hlayout1.addWidget(self.tipo_cb)

        
        hlayout1.addWidget(QLabel("Número:"))
        hlayout1.addWidget(self.numero_le)

        # Ano QLineEdit predefinido com o ano atual e validação para quatro dígitos
        
        self.ano_le.setValidator(QIntValidator(1000, 9999))  # Restringe a entrada para quatro dígitos
        current_year = datetime.now().year
        self.ano_le.setText(str(current_year))
        hlayout1.addWidget(QLabel("Ano:"))
        hlayout1.addWidget(self.ano_le)

        self.layout.addLayout(hlayout1)

        # Linha 3: Objeto
        hlayout3 = QHBoxLayout()
        self.objeto_le = QLineEdit()
        hlayout3.addWidget(QLabel("Objeto:"))
        hlayout3.addWidget(self.objeto_le)
        self.layout.addLayout(hlayout3)

        # Linha 4: OM
        hlayout4 = QHBoxLayout()
        self.nup_le = QLineEdit()
        self.sigla_om_cb = QComboBox()  # Alterado para QComboBox
        self.update_om_btn = QPushButton("Atualizar OM")
        self.update_om_btn.clicked.connect(self.update_om)
        hlayout4.addWidget(QLabel("Nup:"))
        hlayout4.addWidget(self.nup_le)
        hlayout4.addWidget(QLabel("OM:"))
        hlayout4.addWidget(self.sigla_om_cb)  # Usando QComboBox
        hlayout4.addWidget(self.update_om_btn)
        self.layout.addLayout(hlayout4)

        # Linha 5: Material/Serviço
        hlayout5 = QHBoxLayout()
        self.material_servico_group = QButtonGroup(self)  # Grupo para os botões de rádio

        self.material_radio = QRadioButton("Material")
        self.servico_radio = QRadioButton("Serviço")
        self.material_servico_group.addButton(self.material_radio)
        self.material_servico_group.addButton(self.servico_radio)

        hlayout5.addWidget(QLabel("Material/Serviço:"))
        hlayout5.addWidget(self.material_radio)
        hlayout5.addWidget(self.servico_radio)
        self.layout.addLayout(hlayout5)

        # Configurando um valor padrão
        self.material_radio.setChecked(True)

        # Botão de Salvar
        self.save_btn = QPushButton("Salvar")
        self.save_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.save_btn)
        self.load_sigla_om()

    def load_next_numero(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(numero) FROM controle_processos")
                max_number = cursor.fetchone()[0]
                next_number = 1 if max_number is None else int(max_number) + 1
                self.numero_le.setText(str(next_number))
        except Exception as e:
            print(f"Erro ao carregar o próximo número: {e}")

    def load_sigla_om(self):
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT sigla_om, orgao_responsavel, uasg FROM controle_om ORDER BY sigla_om")
                self.om_details = {}
                self.sigla_om_cb.clear()
                ceimbra_found = False  # Variável para verificar se CeIMBra está presente
                default_index = 0  # Índice padrão se CeIMBra não for encontrado

                for index, row in enumerate(cursor.fetchall()):
                    sigla, orgao, uasg = row
                    self.sigla_om_cb.addItem(sigla)
                    self.om_details[sigla] = {"orgao_responsavel": orgao, "uasg": uasg}
                    if sigla == "CeIMBra":
                        ceimbra_found = True
                        default_index = index  # Atualiza o índice para CeIMBra se encontrado

                if ceimbra_found:
                    self.sigla_om_cb.setCurrentIndex(default_index)  # Define CeIMBra como valor padrão
        except Exception as e:
            print(f"Erro ao carregar siglas de OM: {e}")

    def get_data(self):
        sigla_selected = self.sigla_om_cb.currentText()
        material_servico = "Material" if self.material_radio.isChecked() else "Serviço"
        data = {
            'tipo': self.tipo_cb.currentText(),
            'numero': self.numero_le.text(),
            'ano': self.ano_le.text(),
            'nup': self.nup_le.text(),
            'objeto': self.objeto_le.text(),
            'sigla_om': sigla_selected,
            'orgao_responsavel': self.om_details[sigla_selected]['orgao_responsavel'],
            'uasg': self.om_details[sigla_selected]['uasg'],
            'material_servico': material_servico
        }

        # Mapeando o tipo para o valor a ser salvo no banco de dados
        type_map = {option[0]: option[1] for option in self.options}
        abrev_map = {
            "Pregão Eletrônico (PE)": "PE",
            "Concorrência (CC)": "CC",
            "Dispensa Eletrônica (DE)": "DE",
            "Termo de Justificativa de Dispensa Eletrônica (TJDL)": "TJDL",
            "Termo de Justificativa de Inexigibilidade de Licitação (TJIL)": "TJIL"
        }
        tipo_abreviado = abrev_map[data['tipo']]
        data['tipo'] = type_map[data['tipo']]
        data['id_processo'] = f"{tipo_abreviado} {data['numero']}/{data['ano']}"
        return data

    def import_uasg_to_db(self, filepath):
        # Ler os dados do arquivo Excel
        df = pd.read_excel(filepath, usecols=['uasg', 'orgao_responsavel', 'sigla_om'])
        
        # Conectar ao banco de dados e criar a tabela se não existir
        with sqlite3.connect(self.database_path) as conn:
            df.to_sql('controle_om', conn, if_exists='replace', index=False)  # Use 'replace' para substituir ou 'append' para adicionar

    def update_om(self):
        # Supondo que import_uasg_to_db atualize o banco de dados corretamente
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o arquivo Excel",
            "",  # Diretório inicial, pode ser ajustado conforme necessidade
            "Arquivos Excel (*.xlsx);;Todos os Arquivos (*)"
        )

        if filename:
            self.import_uasg_to_db(filename)
            self.load_sigla_om() 
