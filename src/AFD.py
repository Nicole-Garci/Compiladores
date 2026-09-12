import json
import re

class AFD:
    def __init__(self, json_filepath):
        # Carrega as configurações do autômato a partir do JSON
        with open(json_filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        self.estado_inicial = data["initial_state"]
        self.estados = {int(k): v for k, v in data["states"].items()}
        self.estados_finais = set(data["final_states"])
        
        # Mapeamento de transições: self.transicoes[from_state] = [(to_state, condition_string)]
        self.transicoes = {}
        for t in data["transitions"]:
            from_st = t["from"]
            to_st = t["to"]
            read_cond = t["read"]
            
            if from_st not in self.transicoes:
                self.transicoes[from_st] = []
            self.transicoes[from_st].append((to_st, read_cond))
            
        self.estado_atual = self.estado_inicial

    def reiniciar(self):
        # Reinicia o autômato para o estado inicial.
        self.estado_atual = self.estado_inicial

    def eh_estado_final(self):
        # Verifica se o autômato parou em um estado de aceitação.
        return self.estado_atual in self.estados_finais

    def obter_estado_atual(self):
        # Retorna o nome do estado atual (ex: qID, qNUMINT).
        return self.estados.get(self.estado_atual, "qUNKNOWN")

    def eh_estado_de_erro(self):
        # Verifica se o autômato está em um estado de erro (ex: estado 40)
        return self.estado_atual == 40

    def transicionar(self, caractere: str) -> bool:
        # Calcula o próximo estado com base no caractere lido.
        # Retorna True se houve transição válida, ou False se travou/erro.
        if self.estado_atual not in self.transicoes:
            return False
            
        for para_estado, condicao in self.transicoes[self.estado_atual]:
            if self._avaliar_condicao(caractere, condicao):
                self.estado_atual = para_estado
                return True
                
        # Se nenhuma transição casou, envia para estado de erro (40)
        self.estado_atual = 40
        return False

    def _avaliar_condicao(self, caractere: str, condicao: str) -> bool:
        # Lógica interna que avalia se o caractere satisfaz a string de transição usando Regex.
        if caractere == condicao:
            return True
            
        if condicao == "letra":
            return bool(re.match(r'[a-zA-Z]', caractere))

        if condicao == "dígito":
            return bool(re.fullmatch(r'[0-9]', caractere))

        if condicao == "letra | dígito":
            return bool(re.match(r'[a-zA-Z0-9]', caractere))

        if "whitespace" in condicao:
            return caractere in (" ", "\t", "\n", "\r")

        if condicao == "caractere ≠ *":
            return caractere != "*"

        if condicao == "caractere ≠ * e ≠ /":
            return caractere not in ('*', '/')

        if condicao == "caractere ≠ \" e ≠ quebra de linha":
            return caractere != '"' and caractere != '\n'

        if condicao == "ASCII válido":
            return len(caractere) == 1 and caractere.isascii() and caractere not in ("'", "\n", "\r")
            
        return False