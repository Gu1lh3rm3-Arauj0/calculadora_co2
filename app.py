# app.py 

from flask import Flask, render_template, request

app = Flask(__name__)

# --- BASE DE DADOS ---

VIDA_UTIL_KM = 200000

DADOS_PRODUCAO_RECICLAGEM = {
    'compacto': {
        'icev_flex': 5.4 * 1000,
        'bev': 5.8 * 1000,
    },
    'medio': {
        'icev_flex': 5.8 * 1000,
        'hev': 7.7 * 1000,
        'phev': 7.2 * 1000,
        'bev': 5.8 * 1000,
    },
    'suv_compacto': {
        'icev_flex': 6.7 * 1000,
        'bev': 6.7 * 1000,
    }
}

# Adicionada a entrada para 'etanol_2g'
FATORES_EMISSAO_USO = {
    'combustivel': {
        'gasolina_e27': 2413.1,  # Gasolina Comum
        'etanol': 839.2,         # Etanol Comum (1G)
        'etanol_2g': 300.0,        # Etanol de 2ª Geração
        'gasolina_e0': 2994.9,    # Gasolina Pura
    },
    'eletricidade': {
        'verde': 55 * (1/0.85),
        'amarela': 75 * (1/0.85),
        'vermelha_p1': 95 * (1/0.85),
        'vermelha_p2': 125 * (1/0.85),
    }
}

DADOS_CONSUMO = {
    'compacto': {
        'icev_flex': {'combustivel': 6.6, 'eletrico': 0},
        'bev': {'combustivel': 0, 'eletrico': 23.4},
    },
    'medio': {
        'icev_flex': {'combustivel': 6.6, 'eletrico': 0},
        'hev': {'combustivel': 5.1, 'eletrico': 0},
        'phev': {'combustivel': 4.3, 'eletrico': 14.2},
        'bev': {'combustivel': 0, 'eletrico': 22.9},
    },
    'suv_compacto': {
        'icev_flex': {'combustivel': 7.7, 'eletrico': 0},
        'bev': {'combustivel': 0, 'eletrico': 20.6},
    }
}

# A sua versão mais recente do código para baterias.
FATOR_EMISSAO_BATERIA_POR_KWH = 75 
TAMANHO_BATERIA_KWH = {
    'bev': {'compacto': 50, 'medio': 75, 'suv_compacto': 100},
    'phev': {'medio': 20},
    'hev': {'medio': 5}
}
# --- FIM DA BASE DE DADOS ---


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        segmento = request.form['segmento']
        motor = request.form['motor']
        combustivel_tipo = request.form.get('combustivel_tipo')
        bandeira = request.form.get('bandeira')

        if segmento not in DADOS_PRODUCAO_RECICLAGEM or motor not in DADOS_PRODUCAO_RECICLAGEM[segmento]:
            return render_template('index.html', erro=f"A combinação '{segmento}' e '{motor}' não é válida.")
        
        emissao_veiculo_sem_bateria_kg = DADOS_PRODUCAO_RECICLAGEM[segmento][motor]
        
        emissao_bateria_kg = 0
        if motor in TAMANHO_BATERIA_KWH and segmento in TAMANHO_BATERIA_KWH[motor]:
            tamanho_bateria = TAMANHO_BATERIA_KWH[motor][segmento]
            emissao_bateria_kg = tamanho_bateria * FATOR_EMISSAO_BATERIA_POR_KWH
        
        emissao_producao_total_kg = emissao_veiculo_sem_bateria_kg + emissao_bateria_kg
        
        dados_consumo_veiculo = DADOS_CONSUMO[segmento][motor]
        emissao_uso_total_kg = 0
        consumo_combustivel = dados_consumo_veiculo.get('combustivel', 0)
        
        if consumo_combustivel > 0:
            if not combustivel_tipo: return render_template('index.html', erro="Para este motor, o tipo de combustível é necessário.")
            consumo_por_km = consumo_combustivel / 100
            fator_emissao = FATORES_EMISSAO_USO['combustivel'][combustivel_tipo]
            emissao_uso_total_kg += (consumo_por_km * fator_emissao * VIDA_UTIL_KM) / 1000
        
        consumo_eletrico = dados_consumo_veiculo.get('eletrico', 0)
        if consumo_eletrico > 0:
            if not bandeira: return render_template('index.html', erro="Para veículos que usam eletricidade (BEV, PHEV), a bandeira é necessária.")
            consumo_por_km = consumo_eletrico / 100
            fator_emissao_eletricidade = FATORES_EMISSAO_USO['eletricidade'][bandeira]
            emissao_uso_total_kg += (consumo_por_km * fator_emissao_eletricidade * VIDA_UTIL_KM) / 1000

        emissao_total_kg = emissao_producao_total_kg + emissao_uso_total_kg
        emissao_total_toneladas = emissao_total_kg / 1000

        resultado = (
            f"<h3>Resultado da Análise de Ciclo de Vida (ACV)</h3>"
            f"<h4>Detalhe da Produção e Reciclagem:</h4>"
            f"<p style='margin-left: 20px;'>Veículo: {emissao_veiculo_sem_bateria_kg:,.0f} kg de CO₂e</p>"
            f"<p style='margin-left: 20px;'>Bateria: {emissao_bateria_kg:,.0f} kg de CO₂e</p>"
            f"<p><strong>Subtotal Produção: {emissao_producao_total_kg:,.0f} kg de CO₂e</strong></p>"
            f"<h4>Fase de Uso:</h4>"
            f"<p><strong>Emissão em Uso ({VIDA_UTIL_KM:,} km): {emissao_uso_total_kg:,.0f} kg de CO₂e</strong></p>"
            f"<hr>"
            f"<p><strong>EMISSÃO TOTAL (CICLO DE VIDA):<br>{emissao_total_toneladas:.2f} toneladas de CO₂e</strong></p>"
        )

    except (ValueError, KeyError) as e:
        resultado = f"Ocorreu um erro. Verifique se todos os campos aplicáveis foram preenchidos. (Erro: {e})"
        return render_template('index.html', erro=resultado)

    return render_template('index.html', resultado=resultado)


if __name__ == '__main__':
    app.run(debug=True)
