# BeachScore AI

Placar de beach tennis para telão, pensado para rodar em uma Raspberry Pi na arena.

## Telas

- `/` - placar principal para o telão da Raspberry.
- `/control` - controle da partida, configuração da arena/duplas e comandos por voz.
- `/admin` - visão administrativa com arenas, timeline e replay.

Por padrão o app usa a arena `arena-1`. Para outras arenas:

```text
/?arena_id=arena-2
/control?arena_id=arena-2
```

## Comandos de voz

No Chrome/Chromium, abra `/control` e use o botão `FALAR COMANDO`.

Comandos suportados:

- `azul`, `dupla a`, `time a` - ponto para Dupla A
- `vermelho`, `vermelha`, `dupla b`, `time b` - ponto para Dupla B
- `desfazer`, `desfaz`, `voltar` - desfaz a última ação
- `nova partida`, `novo jogo`, `zerar`, `reset` - inicia nova partida
- `virada`, `troca lado`, `trocar lado` - alterna aviso de virada

## Rodar localmente

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra:

```text
http://localhost:5000/
http://localhost:5000/control
```

## Deploy na Raspberry Pi

A Raspberry deve buscar o deploy do GitHub e rodar exatamente o que está na branch principal:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv chromium-browser

cd /opt
sudo git clone https://github.com/wcaseiro/beachscore.git
sudo chown -R "$USER":"$USER" /opt/beachscore

cd /opt/beachscore
./scripts/update_from_git.sh
```

Para atualizar depois de um novo push:

```bash
cd /opt/beachscore
./scripts/update_from_git.sh
```

Depois abra o Chromium da Raspberry em modo telão:

```bash
chromium-browser --kiosk http://localhost:5000/
```

Se a arena tiver outro ID:

```bash
chromium-browser --kiosk "http://localhost:5000/?arena_id=arena-2"
```
