# linkedin-autoridade

Conteúdo semanal do LinkedIn **pessoal** do Rapha (não a Agência Logos). Gerado pela skill `linkedin-autoridade-semanal` — local (`~/.claude/skills/linkedin-autoridade-semanal/SKILL.md`) ou pelo cloud routine `linkedin-autoridade-semanal-cloud` (roda toda segunda de manhã).

**Nunca publica direto.** O routine/skill gera → Rapha revisa neste repo → Rapha agenda no LinkedIn nativo ou Buffer, anexando a imagem/PDF manualmente.

## Estrutura

- `posicionamento.md` — referência fixa: pilares, tom, regras de escrita, paleta visual pessoal
- `banco-de-pautas.md` — banco de pautas por pilar (gera mais quando sobrarem menos de 10 não usadas)
- `historico.md` — controle de temas já publicados, evita repetição
- `templates/` + `scripts/gerar_visual.py` — motor de render (Chrome/Chromium headless + Jinja2 + Pillow). Detecta o binário certo tanto no Mac local quanto no sandbox cloud (`/opt/pw-browsers/chromium`).
- `2026-semana-XX/` — um lote por semana: 2 posts de texto + imagem, 1 carrossel PDF, `resumo-lote.md` com checklist de agendamento

## Setup (novo ambiente)

```bash
pip install -r requirements.txt
```

Ver `posicionamento.md` pra qualquer dúvida de tom/regra antes de escrever ou editar um post.
