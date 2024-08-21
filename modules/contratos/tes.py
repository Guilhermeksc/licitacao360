class SqlModel:
    def __init__(self, icons_dir, database_manager, parent=None):
        self.icons_dir = icons_dir
        self.database_manager = database_manager
        self.parent = parent
        self.init_database()

    def init_database(self):
        if QSqlDatabase.contains("my_conn"):
            QSqlDatabase.removeDatabase("my_conn")
        self.db = QSqlDatabase.addDatabase('QSQLITE', "my_conn")
        self.db.setDatabaseName(str(self.database_manager.db_path))
        if not self.db.open():
            print("Não foi possível abrir a conexão com o banco de dados.")
        else:
            print("Conexão com o banco de dados aberta com sucesso.")
            self.adjust_table_structure()

    def adjust_table_structure(self):
        query = QSqlQuery(self.db)
        if not query.exec("SELECT name FROM sqlite_master WHERE type='table' AND name='controle_contratos'"):
            print("Erro ao verificar existência da tabela:", query.lastError().text())
        if not query.next():
            print("Tabela 'controle_contratos' não existe. Criando tabela...")
            self.create_table_if_not_exists()
        else:
            print("Tabela 'controle_contratos' existe. Verificando estrutura da coluna...")
            self.ensure_numero_contrato_primary_key()

    def ensure_numero_contrato_primary_key(self):
        query = QSqlQuery(self.db)
        query.exec("PRAGMA table_info(controle_contratos)")
        numero_contrato_is_primary = False
        while query.next():
            if query.value(1) == 'numero_contrato' and query.value(5) == 1:
                numero_contrato_is_primary = True
                break
        if not numero_contrato_is_primary:
            print("Atualizando 'numero_contrato' para ser PRIMARY KEY.")
            query.exec("ALTER TABLE controle_contratos ADD COLUMN new_numero_contrato TEXT PRIMARY KEY")
            query.exec("UPDATE controle_contratos SET new_numero_contrato = numero_contrato")
            query.exec("ALTER TABLE controle_contratos DROP COLUMN numero_contrato")
            query.exec("ALTER TABLE controle_contratos RENAME COLUMN new_numero_contrato TO numero_contrato")
            if not query.isActive():
                print("Erro ao atualizar chave primária:", query.lastError().text())

    def create_table_if_not_exists(self):
        query = QSqlQuery(self.db)
        if not query.exec("""
            CREATE TABLE IF NOT EXISTS controle_contratos (
                status TEXT,
                dias TEXT,     
                pode_renovar TEXT,                          
                custeio TEXT,
                numero_contrato TEXT PRIMARY KEY,
                tipo TEXT,  
                id_processo TEXT,
                empresa TEXT,                                          
                objeto TEXT,
                valor_global TEXT, 
                uasg TEXT,
                nup TEXT,
                cnpj TEXT,                        
                natureza_continuada TEXT,
                om TEXT,
                indicativo_om TEXT,
                om_extenso TEXT,
                material_servico TEXT,
                link_pncp TEXT,
                portaria TEXT,
                posto_gestor TEXT,
                gestor TEXT,
                posto_gestor_substituto TEXT,
                gestor_substituto TEXT,
                posto_fiscal TEXT,
                fiscal TEXT,
                posto_fiscal_substituto TEXT,
                fiscal_substituto TEXT,
                posto_fiscal_administrativo TEXT,
                fiscal_administrativo TEXT,
                vigencia_inicial TEXT,
                vigencia_final TEXT,
                setor TEXT,
                cp TEXT,
                msg TEXT,
                comentarios TEXT,
                registro_status TEXT,                    
                termo_aditivo TEXT,
                atualizacao_comprasnet TEXT,
                instancia_governanca TEXT,
                comprasnet_contratos TEXT,
                assinatura_contrato TEXT
            )
        """):
            print("Falha ao criar a tabela 'controle_contratos':", query.lastError().text())
        else:
            print("Tabela 'controle_contratos' criada com sucesso.")

    def setup_model(self, table_name, editable=False):
        self.model = CustomSqlTableModel(parent=self.parent, db=self.db, non_editable_columns=None, icons_dir=self.icons_dir)
        self.model.setTable(table_name)
        if editable:
            self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.model.select()
        return self.model

    def configure_columns(self, table_view, visible_columns):
        for column in range(self.model.columnCount()):
            header = self.model.headerData(column, Qt.Orientation.Horizontal)
            if column not in visible_columns:
                table_view.hideColumn(column)
            else:
                self.model.setHeaderData(column, Qt.Orientation.Horizontal, header)

class CustomSqlTableModel(QSqlTableModel):
    def __init__(self, parent=None, db=None, non_editable_columns=None, icons_dir=None):
        super().__init__(parent, db)
        self.non_editable_columns = non_editable_columns if non_editable_columns is not None else []
        self.icons_dir = icons_dir

    def flags(self, index):
        default_flags = super().flags(index)
        if index.column() in self.non_editable_columns:
            return default_flags & ~Qt.ItemFlag.ItemIsEditable
        return default_flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.column() in self.non_editable_columns:
            return False
        return super().setData(index, value, role)
    
    def update_record(self, row, data):
        record = self.record(row)
        for column, value in data.items():
            record.setValue(column, value)
        if not self.setRecord(row, record):
            print("Erro ao definir registro:", self.lastError().text())
        if not self.submitAll():
            print("Erro ao submeter alterações:", self.lastError().text())

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if self.icons_dir and role == Qt.ItemDataRole.DecorationRole:
            if index.column() == self.fieldIndex("pode_renovar"):
                pode_renovar = self.index(index.row(), self.fieldIndex("pode_renovar")).data()
                if pode_renovar == 'Sim':
                    return QIcon(str(self.icons_dir / 'thumb-up.png'))
                elif pode_renovar == 'Não':
                    return QIcon(str(self.icons_dir / 'unchecked.png'))
            elif index.column() == self.fieldIndex("custeio"):
                custeio = self.index(index.row(), self.fieldIndex("custeio")).data()
                if custeio == 'Sim':
                    return QIcon(str(self.icons_dir / 'thumb-up.png'))
                elif custeio == 'Não':
                    return QIcon(str(self.icons_dir / 'unchecked.png'))

        if self.icons_dir and role == Qt.ItemDataRole.DecorationRole and index.column() == self.fieldIndex("status"):
            status = self.index(index.row(), self.fieldIndex("status")).data()
            status_icons = {
                'Minuta': 'status_secao_contratos.png',
                'Nota Técnica': 'status_nt.png',
                'Aguardando': 'status_cp_msg.png',
                'AGU': 'status_agu.png'
            }
            if status in status_icons:
                return QIcon(str(self.icons_dir / status_icons[status]))

        if role == Qt.ItemDataRole.DisplayRole and index.column() == self.fieldIndex("dias"):
            vigencia_final_index = self.fieldIndex("vigencia_final")
            vigencia_final = self.index(index.row(), vigencia_final_index).data()
            if vigencia_final:
                try:
                    vigencia_final_date = datetime.strptime(vigencia_final, '%d/%m/%Y')
                    hoje = datetime.today()
                    dias = (vigencia_final_date - hoje).days
                    return dias
                except ValueError:
                    return "Data Inválida"
        return super().data(index, role)
class CustomTableView(QTableView):
    def __init__(self, main_app, config_manager, parent=None):
        super().__init__(parent)
        self.main_app = main_app
        self.config_manager = config_manager
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            contextMenu = TableMenu(self.main_app, index, self.model(), config_manager=self.config_manager)
            contextMenu.exec(self.viewport().mapToGlobal(pos))