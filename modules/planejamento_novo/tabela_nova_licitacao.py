from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

def create_table_equipe_planejamento(db: QSqlDatabase):
    query = QSqlQuery(db)
    query.exec(
        '''
        CREATE TABLE IF NOT EXISTS equipe_planejamento
            id_processo PRIMARY KEY,
            portaria TEXT,
            coordenador TEXT,
            posto_grad_coordenador TEXT,
            nome_coordenador TEXT,
            telefone_coordenador TEXT,
            email_coordenador TEXT,
            membro1 TEXT,
            posto_grad_membro1 TEXT,
            nome_membro1 TEXT,
            telefone_membro1 TEXT,
            email_membro1 TEXT,
            membro2 TEXT,
            posto_grad_membro2 TEXT,
            nome_membro2 TEXT,
            telefone_membro2 TEXT,
            email_membro2 TEXT
            '''
    )

def create_table_licitacao(db: QSqlDatabase):
    query = QSqlQuery(db)
    query.exec(
        '''
        CREATE TABLE IF NOT EXISTS controle_processos (
            etapa TEXT,
            id_processo PRIMARY KEY,
            nup TEXT,
            objeto TEXT,
            uasg TEXT,
            sigla_om TEXT,
            pregoeiro TEXT,
            tipo TEXT,
            numero TEXT,
            ano TEXT,
            objeto_completo TEXT,
            valor_estimado_total TEXT,
            material_servico TEXT,
            criterio_julgamento TEXT,
            tipo_contratacao TEXT,
            vigencia TEXT,
            prioridade TEXT,
            emenda_parlamentar TEXT,
            srp TEXT,
            atividade_custeio TEXT,
            processo_parametrizado TEXT,
            sequencial_pncp TEXT,
            cnpj_matriz TEXT,
            orgao_responsavel TEXT,
            setor_responsavel TEXT,
            item_pca TEXT,
            portaria_PCA TEXT,
            data_sessao TEXT,
            data_limite_entrega_tr TEXT,
            nup_portaria_planejamento TEXT,
            srp TEXT,
            material_servico TEXT,
            parecer_agu TEXT,
            msg_irp TEXT,
            data_limite_manifestacao_irp TEXT,
            data_limite_confirmacao_irp TEXT,
            num_irp TEXT,
            om_participantes TEXT,
            link_pncp TEXT,
            link_portal_marinha TEXT,
            comentarios TEXT,
        )
        '''
    )
    if query.isActive():
        print("Tabela 'controle_processos' verificada/criada com sucesso.")
    else:
        print("Erro ao criar/verificar a tabela 'controle_processos':", query.lastError().text())
    # Verificar/criar tabela controle_prazos
    query.exec(
        '''
        CREATE TABLE IF NOT EXISTS controle_prazos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave_processo TEXT,
            etapa TEXT,
            data_inicial TEXT,
            data_final TEXT,
            dias_na_etapa INTEGER,
            comentario TEXT,
            sequencial INTEGER
        )
        '''
    )
    if query.isActive():
        print("Tabela 'controle_prazos' verificada/criada com sucesso.")
    else:
        print("Erro ao criar/verificar a tabela 'controle_prazos':", query.lastError().text())
                    