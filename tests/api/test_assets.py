import requests


def test_evidenciar_erro_ativos_duplicados(base_url):
    """Evidencia e imprime no terminal o bug de ativos duplicados."""
    response = requests.get(f"{base_url}/api/assets")
    assert response.status_code == 200

    data = response.json()
    nomes_ativos = [ativo["asset_name"] for ativo in data]
    nomes_unicos = set(nomes_ativos)

    if len(nomes_ativos) != len(nomes_unicos):
        print("\n" + "=" * 60)
        print(" [BUG ENCONTRADO] ATIVOS DUPLICADOS NA API")
        print("=" * 60)
        print(f"Total de registos retornados: {len(nomes_ativos)}")
        print(f"Total de nomes únicos: {len(nomes_unicos)}")
        
        # Identifica quais nomes estão duplicados
        duplicados = {nome for nome in nomes_ativos if nomes_ativos.count(nome) > 1}
        print(f"Ativos duplicados encontrados: {list(duplicados)}")
        print("=" * 60)

    assert len(nomes_ativos) == len(nomes_unicos), (
        f"Erro de Integridade: Foram encontradas duplicidades de ativos na API. "
        f"Total: {len(nomes_ativos)}, Únicos: {len(nomes_unicos)}"
    )


def test_evidenciar_erro_massa_de_dados_suja(base_url):
    """Evidencia e imprime no terminal a presença de dados de teste/lixo na base."""
    response = requests.get(f"{base_url}/api/assets")
    assert response.status_code == 200

    data = response.json()
    invalidos = [
        ativo["asset_name"]
        for ativo in data
        if "TESTE" in ativo["asset_name"].upper()
        or "XYZ" in ativo["asset_name"].upper()
        or ativo["asset_name"] == "string"
    ]

    if len(invalidos) > 0:
        print("\n" + "=" * 60)
        print(" [BUG ENCONTRADO] MASSA DE DADOS SUJA / DADOS DE TESTE")
        print("=" * 60)
        print(f"Registos inválidos/lixo detetados: {invalidos}")
        print("=" * 60)

    assert len(invalidos) == 0, (
        f"Erro de Qualidade de Dados: Foram encontrados ativos de teste "
        f"não sanitizados: {invalidos}"
    )


def test_evidenciar_erro_inconsistencia_escala_taxas(base_url):
    """Evidencia e imprime no terminal a mistura de escalas nas taxas anuais."""
    response = requests.get(f"{base_url}/api/assets")
    assert response.status_code == 200

    data = response.json()
    poupancas = [a for a in data if a["asset_name"] == "Poupança"]
    taxas = [p["annual_rate"] for p in poupancas]

    todas_percentuais = all(t >= 1.0 for t in taxas)
    todas_decimais = all(t < 1.0 for t in taxas)

    if not (todas_percentuais or todas_decimais):
        print("\n" + "=" * 60)
        print(" [BUG ENCONTRADO] INCONSISTÊNCIA NA ESCALA DAS TAXAS")
        print("=" * 60)
        print(f"Taxas registadas para o mesmo ativo ('Poupança'): {taxas}")
        print("Problema: Mistura de taxas percentuais (ex: 6.17) com decimais (ex: 0.0125).")
        print("=" * 60)

    assert todas_percentuais or todas_decimais, (
        f"Erro de Padronização: A Poupança possui taxas misturando "
        f"porcentagem e valor decimal: {taxas}"
    )