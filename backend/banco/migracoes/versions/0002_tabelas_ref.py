"""Tabelas do esquema ref, visões dos dados vigentes e permissões.

Revisão: 0002
Anterior: 0001
Criada em: 2026-10-08
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Formatos do ADR 0005. CUSIP, SEDOL e ISIN de país fora da lista permitida não cabem em nenhum
    # deles, então nunca entram no banco. ZZ é o prefixo sintético dos testes: não é país nem
    # identificador real.
    op.execute(
        r"""
        CREATE DOMAIN ref.isin_permitido AS text
            CHECK (VALUE ~ '^(BR|IE|LU|ZZ)[A-Z0-9]{9}[0-9]$');

        CREATE DOMAIN ref.ativo_id AS text CHECK (
            VALUE ~ '^(BR|IE|LU|ZZ)[A-Z0-9]{9}[0-9]$'
            OR VALUE ~ '^US:[A-Z]{1,5}(\.[A-Z])?$'
            OR VALUE ~ '^CNPJ:[0-9]{14}$'
        );

        CREATE DOMAIN ref.empresa_id AS text CHECK (
            VALUE ~ '^BR:CNPJ:[0-9]{14}$'
            OR VALUE ~ '^US:CIK:[0-9]{10}$'
            OR VALUE ~ '^LEI:[A-Z0-9]{18}[0-9]{2}$'
            OR VALUE ~ '^ZZ:[A-Z0-9]{1,20}$'
        );

        CREATE DOMAIN ref.origem_classificacao AS text
            CHECK (VALUE IN ('manual', 'oficial', 'wikidata', 'ia', 'modelo_irrae'));

        CREATE DOMAIN ref.status_revisao AS text CHECK (VALUE IN ('rascunho', 'aprovado'));
        """
    )

    # Cargas (seções 3 e 5): toda linha de dado pertence a uma carga. A carga nasce "carregando" e
    # termina "publicada" ou "com_erro", uma vez só; a data da publicação vem do próprio banco.
    op.execute(
        """
        CREATE TABLE ref.carga (
            carga_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            tipo text NOT NULL CHECK (tipo IN (
                'composicoes_cvm', 'composicoes_nport', 'identificacao', 'classificacao', 'ptax'
            )),
            fonte text NOT NULL,
            data_referencia date,
            status text NOT NULL DEFAULT 'carregando'
                CHECK (status IN ('carregando', 'publicada', 'com_erro')),
            iniciada_em timestamptz NOT NULL DEFAULT clock_timestamp(),
            publicada_em timestamptz,
            linhas bigint CHECK (linhas >= 0),
            motivo_erro text,
            CONSTRAINT publicada_tem_data
                CHECK ((status = 'publicada') = (publicada_em IS NOT NULL)),
            CONSTRAINT erro_tem_motivo CHECK ((status = 'com_erro') = (motivo_erro IS NOT NULL))
        );

        CREATE FUNCTION ref.conferir_andamento_da_carga() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.status <> 'carregando' THEN
                RAISE EXCEPTION 'carga % já está %: não muda mais', OLD.carga_id, OLD.status;
            END IF;
            IF (NEW.carga_id, NEW.tipo, NEW.fonte, NEW.iniciada_em, NEW.data_referencia)
                IS DISTINCT FROM
                (OLD.carga_id, OLD.tipo, OLD.fonte, OLD.iniciada_em, OLD.data_referencia) THEN
                RAISE EXCEPTION 'carga %: só o andamento muda', OLD.carga_id;
            END IF;
            NEW.publicada_em := CASE WHEN NEW.status = 'publicada' THEN clock_timestamp() END;
            RETURN NEW;
        END
        $$;

        CREATE TRIGGER conferir_andamento BEFORE UPDATE ON ref.carga
            FOR EACH ROW EXECUTE FUNCTION ref.conferir_andamento_da_carga();
        """
    )

    # Identificação (ADR 0005): uma foto completa por carga, montada a partir da curadoria e das
    # fontes liberadas. Os fundos também são ativos; o UCITS aponta para o ETF americano que o
    # aproxima.
    op.execute(
        r"""
        CREATE TABLE ref.empresa (
            carga_id bigint NOT NULL REFERENCES ref.carga,
            empresa_id ref.empresa_id NOT NULL,
            nome text NOT NULL,
            cnpj text CHECK (cnpj ~ '^[0-9]{14}$'),
            cik text CHECK (cik ~ '^[0-9]{10}$'),
            lei text CHECK (lei ~ '^[A-Z0-9]{18}[0-9]{2}$'),
            PRIMARY KEY (carga_id, empresa_id)
        );

        -- Identificador antigo ou de menor prioridade que aponta para o empresa_id atual.
        CREATE TABLE ref.empresa_apelido (
            carga_id bigint NOT NULL,
            apelido ref.empresa_id NOT NULL,
            empresa_id ref.empresa_id NOT NULL,
            PRIMARY KEY (carga_id, apelido),
            FOREIGN KEY (carga_id, empresa_id) REFERENCES ref.empresa (carga_id, empresa_id),
            CHECK (apelido <> empresa_id)
        );

        CREATE TABLE ref.ativo (
            carga_id bigint NOT NULL REFERENCES ref.carga,
            ativo_id ref.ativo_id NOT NULL,
            tipo text NOT NULL CHECK (tipo IN ('acao', 'fundo')),
            empresa_id ref.empresa_id,
            ticker_b3 text CHECK (ticker_b3 ~ '^[A-Z]{4}[0-9]{1,2}$'),
            ticker_eua text CHECK (ticker_eua ~ '^[A-Z]{1,5}(\.[A-Z])?$'),
            isin ref.isin_permitido,
            nome text,
            aproximado_por ref.ativo_id,
            PRIMARY KEY (carga_id, ativo_id),
            FOREIGN KEY (carga_id, empresa_id) REFERENCES ref.empresa (carga_id, empresa_id),
            CONSTRAINT acao_tem_empresa CHECK ((tipo = 'acao') = (empresa_id IS NOT NULL)),
            CONSTRAINT so_fundo_e_aproximado CHECK (aproximado_por IS NULL OR tipo = 'fundo'),
            UNIQUE (carga_id, ticker_b3),
            UNIQUE (carga_id, ticker_eua),
            UNIQUE (carga_id, isin)
        );
        """
    )

    # Composições (seção 4): valor como a fonte informa, na moeda da composição (R$ na CVM, US$ no
    # N-PORT), o percentual que a fonte informa (pctVal do N-PORT) e o peso calculado na carga.
    op.execute(
        """
        CREATE TABLE ref.composicao (
            composicao_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            carga_id bigint NOT NULL REFERENCES ref.carga,
            fundo_id ref.ativo_id NOT NULL,
            nome_fundo text,
            data_referencia date NOT NULL,
            moeda text NOT NULL CHECK (moeda IN ('BRL', 'USD')),
            patrimonio numeric,
            UNIQUE (carga_id, fundo_id)
        );

        CREATE INDEX composicao_por_fundo ON ref.composicao (fundo_id, data_referencia);

        CREATE TABLE ref.composicao_item (
            composicao_id bigint NOT NULL REFERENCES ref.composicao,
            ordem integer NOT NULL CHECK (ordem > 0),
            ativo_id ref.ativo_id,
            empresa_id ref.empresa_id,
            tipo text NOT NULL CHECK (tipo IN (
                'acao', 'fundo', 'caixa', 'derivativo', 'credito', 'titulo_publico', 'outro'
            )),
            valor numeric,
            percentual_fonte numeric,
            peso numeric NOT NULL,
            ativo_objeto ref.ativo_id,
            emissor ref.empresa_id,
            PRIMARY KEY (composicao_id, ordem),
            -- Ação sem ativo_id (N-PORT sem ticker) aponta direto para a empresa (ADR 0005).
            CONSTRAINT empresa_so_em_acao_sem_ativo
                CHECK (empresa_id IS NULL OR (tipo = 'acao' AND ativo_id IS NULL)),
            CONSTRAINT ativo_objeto_so_em_derivativo
                CHECK (ativo_objeto IS NULL OR tipo = 'derivativo'),
            CONSTRAINT emissor_so_em_credito CHECK (emissor IS NULL OR tipo = 'credito')
        );
        """
    )

    # Classificação simples antes do P3 (seção 9): setor e linhas de tema, cada versão uma foto
    # completa. Faixa do IrRAE e execução de origem entram depois do P3.
    op.execute(
        """
        CREATE TABLE ref.classificacao (
            carga_id bigint NOT NULL REFERENCES ref.carga,
            empresa_id ref.empresa_id NOT NULL,
            setor text NOT NULL,
            setor_origem ref.origem_classificacao NOT NULL,
            setor_status ref.status_revisao NOT NULL,
            PRIMARY KEY (carga_id, empresa_id)
        );

        CREATE TABLE ref.classificacao_tema (
            carga_id bigint NOT NULL,
            empresa_id ref.empresa_id NOT NULL,
            tema text NOT NULL,
            subtema text NOT NULL,
            peso numeric NOT NULL CHECK (peso > 0 AND peso <= 1),
            origem ref.origem_classificacao NOT NULL,
            status ref.status_revisao NOT NULL,
            PRIMARY KEY (carga_id, empresa_id, tema, subtema),
            FOREIGN KEY (carga_id, empresa_id) REFERENCES ref.classificacao (carga_id, empresa_id)
        );

        -- Uma correção é uma carga nova: a mesma data pode aparecer em mais de uma carga.
        CREATE TABLE ref.ptax (
            carga_id bigint NOT NULL REFERENCES ref.carga,
            data_cotacao date NOT NULL,
            valor numeric NOT NULL CHECK (valor > 0),
            PRIMARY KEY (carga_id, data_cotacao)
        );

        CREATE INDEX ptax_por_data ON ref.ptax (data_cotacao);
        """
    )

    # Linha só entra em carga "carregando" e do tipo certo: depois de publicada, a carga não muda.
    # Conferido por comando (e não por linha), para não pesar nas cargas grandes da CVM.
    op.execute(
        """
        CREATE FUNCTION ref.conferir_carga_aberta() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            -- TG_ARGV: os tipos de carga que podem receber linhas desta tabela.
            IF EXISTS (
                SELECT 1 FROM novas n LEFT JOIN ref.carga c ON c.carga_id = n.carga_id
                WHERE c.status IS DISTINCT FROM 'carregando' OR NOT (c.tipo = ANY (TG_ARGV))
            ) THEN
                RAISE EXCEPTION 'ref.%: linha só entra em carga carregando do tipo %',
                    TG_TABLE_NAME, TG_ARGV;
            END IF;
            RETURN NULL;
        END
        $$;

        CREATE FUNCTION ref.conferir_carga_aberta_do_item() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM novas n
                JOIN ref.composicao p ON p.composicao_id = n.composicao_id
                JOIN ref.carga c ON c.carga_id = p.carga_id
                WHERE c.status <> 'carregando'
            ) THEN
                RAISE EXCEPTION 'ref.composicao_item: linha só entra em carga carregando';
            END IF;
            RETURN NULL;
        END
        $$;

        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.composicao REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT
            EXECUTE FUNCTION ref.conferir_carga_aberta('composicoes_cvm', 'composicoes_nport');
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.composicao_item
            REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta_do_item();
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.empresa REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta('identificacao');
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.empresa_apelido
            REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta('identificacao');
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.ativo REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta('identificacao');
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.classificacao
            REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta('classificacao');
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.classificacao_tema
            REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta('classificacao');
        CREATE TRIGGER carga_aberta AFTER INSERT ON ref.ptax REFERENCING NEW TABLE AS novas
            FOR EACH STATEMENT EXECUTE FUNCTION ref.conferir_carga_aberta('ptax');
        """
    )

    # Visões dos dados vigentes (seção 3): a API lê só por elas e só vê cargas publicadas.
    op.execute(
        """
        CREATE VIEW ref.carga_publicada AS
        SELECT carga_id, tipo, fonte, data_referencia, publicada_em
        FROM ref.carga
        WHERE status = 'publicada';

        -- Identificação e classificação são fotos completas: vale a última publicada de cada tipo.
        -- Visão interna, sem permissão para a API.
        CREATE VIEW ref.foto_vigente AS
        SELECT DISTINCT ON (tipo) tipo, carga_id
        FROM ref.carga
        WHERE status = 'publicada' AND tipo IN ('identificacao', 'classificacao')
        ORDER BY tipo, publicada_em DESC, carga_id DESC;

        CREATE VIEW ref.empresa_vigente AS
        SELECT e.empresa_id, e.nome
        FROM ref.empresa e
        JOIN ref.foto_vigente f ON f.tipo = 'identificacao' AND f.carga_id = e.carga_id;

        CREATE VIEW ref.empresa_apelido_vigente AS
        SELECT a.apelido, a.empresa_id
        FROM ref.empresa_apelido a
        JOIN ref.foto_vigente f ON f.tipo = 'identificacao' AND f.carga_id = a.carga_id;

        CREATE VIEW ref.ativo_vigente AS
        SELECT a.ativo_id, a.tipo, a.empresa_id, a.ticker_b3, a.ticker_eua, a.isin, a.nome,
            a.aproximado_por
        FROM ref.ativo a
        JOIN ref.foto_vigente f ON f.tipo = 'identificacao' AND f.carga_id = a.carga_id;

        -- Só linhas aprovadas entram no produto; mostrar as preliminares é decisão pendente com
        -- o M1 (seção 3).
        CREATE VIEW ref.classificacao_vigente AS
        SELECT c.carga_id, c.empresa_id, c.setor, c.setor_origem, c.setor_status
        FROM ref.classificacao c
        JOIN ref.foto_vigente f ON f.tipo = 'classificacao' AND f.carga_id = c.carga_id
        WHERE c.setor_status = 'aprovado';

        CREATE VIEW ref.classificacao_tema_vigente AS
        SELECT t.carga_id, t.empresa_id, t.tema, t.subtema, t.peso, t.origem, t.status
        FROM ref.classificacao_tema t
        JOIN ref.classificacao_vigente c
            ON c.carga_id = t.carga_id AND c.empresa_id = t.empresa_id
        WHERE t.status = 'aprovado';

        -- Composição vigente de cada fundo: a do mês mais recente entre as cargas publicadas; no
        -- mesmo mês, a publicada por último.
        CREATE VIEW ref.composicao_vigente AS
        SELECT DISTINCT ON (p.fundo_id)
            p.composicao_id, p.fundo_id, p.nome_fundo, p.data_referencia, p.moeda, p.patrimonio,
            p.carga_id, c.fonte
        FROM ref.composicao p
        JOIN ref.carga c ON c.carga_id = p.carga_id
        WHERE c.status = 'publicada'
        ORDER BY p.fundo_id, date_trunc('month', p.data_referencia) DESC, c.publicada_em DESC,
            c.carga_id DESC;

        CREATE VIEW ref.composicao_item_vigente AS
        SELECT v.composicao_id, v.fundo_id, i.ordem, i.ativo_id, i.empresa_id, i.tipo, i.peso,
            i.ativo_objeto, i.emissor
        FROM ref.composicao_item i
        JOIN ref.composicao_vigente v ON v.composicao_id = i.composicao_id;

        -- PTAX de cada dia: a da carga publicada por último que traz esse dia.
        CREATE VIEW ref.ptax_vigente AS
        SELECT DISTINCT ON (x.data_cotacao) x.data_cotacao, x.valor, x.carga_id
        FROM ref.ptax x
        JOIN ref.carga c ON c.carga_id = x.carga_id
        WHERE c.status = 'publicada'
        ORDER BY x.data_cotacao, c.publicada_em DESC, c.carga_id DESC;
        """
    )

    # Permissões (seção 6). A API só lê as visões. A ingestão lê as tabelas, só acrescenta linhas
    # e, na carga, só abre (tipo, fonte e data) e muda o andamento; nunca altera nem apaga dados.
    op.execute(
        """
        GRANT SELECT ON ref.carga, ref.composicao, ref.composicao_item, ref.empresa,
            ref.empresa_apelido, ref.ativo, ref.classificacao, ref.classificacao_tema, ref.ptax
            TO rx_ingestao;
        GRANT INSERT ON ref.composicao, ref.composicao_item, ref.empresa, ref.empresa_apelido,
            ref.ativo, ref.classificacao, ref.classificacao_tema, ref.ptax
            TO rx_ingestao;
        GRANT INSERT (tipo, fonte, data_referencia), UPDATE (status, linhas, motivo_erro)
            ON ref.carga TO rx_ingestao;

        GRANT SELECT ON ref.carga_publicada, ref.composicao_vigente, ref.composicao_item_vigente,
            ref.empresa_vigente, ref.empresa_apelido_vigente, ref.ativo_vigente,
            ref.classificacao_vigente, ref.classificacao_tema_vigente, ref.ptax_vigente
            TO rx_api, rx_ingestao;
        """
    )


def downgrade() -> None:
    raise NotImplementedError("Migrações só vão para frente (ADR 0006): corrija com uma nova.")
