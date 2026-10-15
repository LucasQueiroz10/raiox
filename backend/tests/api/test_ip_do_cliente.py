"""A chave do limite por IP (DT-17; ADR 0007, seção 3).

No Cloud Run a conexão chega da infraestrutura do Google, e o IP do cliente vem no X-Forwarded-For.
Cada proxy confiável acrescenta um endereço à direita; o que fica à esquerda deles pode ter sido
escrito pelo próprio cliente. A chave é o N-ésimo endereço da direita, com N configurado
(RX_PROXIES_CONFIAVEIS). Os IPs são dos blocos reservados para documentação.
"""

from hypothesis import given
from hypothesis import strategies as st

from app.api.seguranca import chave_do_limite

CONEXAO = "192.0.2.1"  # a infraestrutura do Google, no Cloud Run


def test_sem_proxies_confiaveis_usa_o_ip_da_conexao_e_ignora_o_cabecalho():
    assert chave_do_limite(["203.0.113.9"], CONEXAO, 0) == CONEXAO


def test_com_um_proxy_usa_o_ultimo_endereco():
    assert chave_do_limite(["203.0.113.9, 198.51.100.20"], CONEXAO, 1) == "198.51.100.20"


def test_com_dois_proxies_usa_o_penultimo_endereco():
    cabecalho = ["203.0.113.9, 198.51.100.20, 192.0.2.30"]

    assert chave_do_limite(cabecalho, CONEXAO, 2) == "198.51.100.20"


def test_varios_cabecalhos_contam_como_um_so_na_ordem():
    cabecalhos = ["203.0.113.9", "198.51.100.20, 192.0.2.30"]

    assert chave_do_limite(cabecalhos, CONEXAO, 2) == "198.51.100.20"


def test_espacos_em_volta_dos_enderecos_nao_contam():
    assert chave_do_limite([" 203.0.113.9 ,198.51.100.20  "], CONEXAO, 2) == "203.0.113.9"


def test_menos_enderecos_que_proxies_usa_o_ip_da_conexao():
    # O pedido não passou pelo caminho esperado: o endereço da posição não existe.
    assert chave_do_limite(["198.51.100.20"], CONEXAO, 2) == CONEXAO
    assert chave_do_limite([], CONEXAO, 1) == CONEXAO


def test_valor_que_nao_e_ip_na_posicao_usa_o_ip_da_conexao():
    for invalido in ("desconhecido", "203.0.113.9:443", "", "203.0.113.999"):
        assert chave_do_limite([f"203.0.113.9, {invalido}"], CONEXAO, 1) == CONEXAO


def test_ipv6_conta_pela_rede_64():
    # Quem tem IPv6 costuma ter uma rede /64 inteira: trocar de endereço dentro dela não pode
    # zerar o limite.
    um = chave_do_limite(["2001:db8:1:2::a"], CONEXAO, 1)
    outro_da_mesma_rede = chave_do_limite(["2001:db8:1:2:ffff::b"], CONEXAO, 1)
    de_outra_rede = chave_do_limite(["2001:db8:1:3::a"], CONEXAO, 1)

    assert um == outro_da_mesma_rede == "2001:db8:1:2::/64"
    assert de_outra_rede == "2001:db8:1:3::/64"


def test_ipv4_escrito_como_ipv6_conta_como_o_ipv4():
    assert chave_do_limite(["::ffff:203.0.113.9"], CONEXAO, 1) == "203.0.113.9"


def test_ip_da_conexao_ipv6_tambem_conta_pela_rede_64():
    assert chave_do_limite([], "2001:db8:1:2::a", 0) == "2001:db8:1:2::/64"


def test_conexao_sem_ip_valido():
    # O TestClient se apresenta como "testclient"; sem conexão, todos dividem a mesma chave.
    assert chave_do_limite([], "testclient", 0) == "testclient"
    assert chave_do_limite([], None, 0) == "sem-ip"


ips = st.ip_addresses().map(str)


@given(
    forjados=st.lists(st.text(max_size=20), max_size=5),
    confiaveis=st.lists(ips, min_size=1, max_size=3),
    no_mesmo_cabecalho=st.booleans(),
)
def test_enderecos_forjados_a_esquerda_nunca_mudam_a_chave(
    forjados, confiaveis, no_mesmo_cabecalho
):
    proxies = len(confiaveis)
    confiavel = ", ".join(confiaveis)
    if no_mesmo_cabecalho:
        com_forjados = [", ".join([*forjados, confiavel])]
    else:
        com_forjados = [*forjados, confiavel]

    assert chave_do_limite(com_forjados, CONEXAO, proxies) == chave_do_limite(
        [confiavel], CONEXAO, proxies
    )


@given(cabecalhos=st.lists(st.text(max_size=40), max_size=5))
def test_sem_proxies_confiaveis_o_cabecalho_nunca_muda_a_chave(cabecalhos):
    assert chave_do_limite(cabecalhos, CONEXAO, 0) == CONEXAO
