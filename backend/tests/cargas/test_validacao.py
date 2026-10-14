"""Varredura de CPF antes de publicar uma carga (pedido do M1; ADR 0008, seção 3)."""

import pytest

from cargas.rotina import ErroDeValidacao
from cargas.validacao import conferir_sem_cpf, cpf_valido

# Base 000000001 com os dígitos verificadores certos: um número de teste, para exercitar a
# varredura. O "11111111111" tem dígitos repetidos e nunca é CPF válido.
CPF_DE_TESTE = "00000000191"


def test_cpf_valido_confere_os_digitos_verificadores():
    assert cpf_valido(CPF_DE_TESTE)
    assert not cpf_valido("00000000192")  # dígito errado
    assert not cpf_valido("11111111111")  # dígitos repetidos


@pytest.mark.parametrize(
    "texto",
    [
        CPF_DE_TESTE,
        f"FUNDO {CPF_DE_TESTE} RESPONSABILIDADE LIMITADA",
        "CPF 000.000.001-91",
        f"CPF:{CPF_DE_TESTE}",
    ],
)
def test_acha_cpf_solto_ou_com_mascara(texto):
    with pytest.raises(ErroDeValidacao, match="nome_fundo") as erro:
        conferir_sem_cpf([("ZZ", texto)], ("fundo_id", "nome_fundo"))

    assert "191" not in str(erro.value)  # a mensagem nunca repete o número


@pytest.mark.parametrize(
    "texto",
    [
        "BR:CNPJ:00000000000191",  # 14 dígitos: CNPJ, não CPF
        f"CNPJ:ZZZ{CPF_DE_TESTE}",  # dentro de um identificador com letras
        "FUNDO 00000000192",  # dígito verificador errado
        "FUNDO 11111111111",  # dígitos repetidos
        None,
    ],
)
def test_nao_confunde_cpf_com_outros_numeros(texto):
    conferir_sem_cpf([(texto,)], ("coluna",))


def test_mensagem_aponta_o_id_publico_da_linha():
    linhas = [("CNPJ:ZZ1", "FUNDO SEM NUMERO"), ("CNPJ:ZZ2", f"FUNDO {CPF_DE_TESTE}")]

    with pytest.raises(ErroDeValidacao) as erro:
        conferir_sem_cpf(linhas, ("fundo_id", "nome_fundo"), chave="fundo_id")

    assert str(erro.value) == "número com formato de CPF na coluna nome_fundo (fundo_id CNPJ:ZZ2)"


def test_cpf_na_propria_coluna_do_id_nao_e_repetido():
    with pytest.raises(ErroDeValidacao) as erro:
        conferir_sem_cpf([(CPF_DE_TESTE, "NOME")], ("ativo_id", "nome"), chave="ativo_id")

    assert str(erro.value) == "número com formato de CPF na coluna ativo_id"


def test_id_que_tambem_tem_cpf_fica_fora_da_mensagem():
    linha = (f"NOME {CPF_DE_TESTE}", f"ID {CPF_DE_TESTE}")

    with pytest.raises(ErroDeValidacao) as erro:
        conferir_sem_cpf([linha], ("nome", "ativo_id"), chave="ativo_id")

    assert str(erro.value) == "número com formato de CPF na coluna nome"
