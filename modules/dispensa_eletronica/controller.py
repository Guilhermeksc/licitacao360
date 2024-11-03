from modules.dispensa_eletronica.models import DispensaEletronicaModel
from modules.dispensa_eletronica.views import DispensaEletronicaWidget
from modules.dispensa_eletronica.dialogs.add_item import AddItemDialog
from modules.dispensa_eletronica.dialogs.salvar_tabela import SaveTableDialog
from modules.dispensa_eletronica.dialogs.graficos import GraficTableDialog
from modules.dispensa_eletronica.dialogs.gerar_tabela import TabelaResumidaManager
from modules.dispensa_eletronica.dialogs.editar_dados import EditDataDialog
from modules.dispensa_eletronica.utils.db_manager import carregar_dados_dispensa
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
import pandas as pd

class DispensaEletronicaController(QObject):
    def __init__(self, view, model):
        super().__init__()
        self.view = view
        self.model = model
        self.database_path = model.database_manager.db_path
        self.setup_connections()

    def setup_connections(self):
        # Conecta os sinais da view aos métodos do controlador
        self.view.addItem.connect(self.handle_add_item)
        self.view.deleteItem.connect(self.handle_delete_item)
        self.view.salvar_tabela.connect(self.handle_save_table)
        self.view.salvar_graficos.connect(self.handle_save_charts)
        self.view.salvar_print.connect(self.handle_save_print)

    def handle_add_item(self):
        """Trata a ação de adicionar item."""
        dialog = AddItemDialog(self.model.database_manager.db_path, self.view)  # Passa o caminho do banco de dados
        if dialog.exec():
            item_data = dialog.get_data()
            # Adiciona a situação padrão 'Planejamento' antes de salvar
            item_data['situacao'] = 'Planejamento'
            self.model.insert_or_update_data(item_data)  # Salva no banco de dados
            self.view.refresh_model()   # Salva no banco de dados

    def handle_delete_item(self):
        """Trata a ação de exclusão de um item selecionado."""
        selection_model = self.view.table_view.selectionModel()
        if selection_model.hasSelection():
            index = selection_model.selectedRows(0)[0]  # Assumindo que a coluna 0 é 'id_processo'
            id_processo = index.data()
            if id_processo:
                confirmation = QMessageBox.question(
                    self.view, "Confirmação",
                    f"Tem certeza que deseja excluir o registro com ID '{id_processo}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if confirmation == QMessageBox.StandardButton.Yes:
                    self.model.delete_data(id_processo)
                    self.view.refresh_model()
        else:
            QMessageBox.warning(self.view, "Nenhuma Seleção", "Por favor, selecione um item para excluir.")

    def handle_save_table(self):
        """Trata a ação de salvar a tabela."""
        dialog = SaveTableDialog(self.view)  # Supondo que SaveTableDialog está implementado
        dialog.exec()

    def handle_save_charts(self):
        """Trata a ação de salvar gráficos."""
        dialog = GraficTableDialog(self.view)  # Supondo que GraficTableDialog está implementado
        dialog.exec()

    def handle_save_print(self):
        """Trata a ação de salvar uma imagem da tabela."""
        # Implementação de salvar print da tabela
        output_image_path = "tabela_resumida.png"
        # Supondo que um método `tirar_print_da_tabela` exista para salvar a tabela como imagem
        self.view.salvar_tabela_resumida()
        QMessageBox.information(self.view, "Imagem Salva", f"A tabela foi salva em {output_image_path}")

    def refresh_view(self):
        # Atualiza a visualização da tabela após alterações nos dados
        self.view.model.select()  # Recarrega os dados no modelo


def show_warning_if_view_exists(view, title, message):
    if view is not None:
        QMessageBox.warning(view, title, message)
    else:
        print(message)  # Mensagem para o log, caso `view` esteja indisponível