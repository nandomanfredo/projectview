import mpxj
import jpype
import json
from datetime import datetime
from pathlib import Path

ARQUIVO_MPP  = r"C:\Users\fernando.oliveira\OneDrive - AG CAPITAL\Documentos\Gestão de Projetos com IA\AIS 04 - Cronograma do Projeto de Implantação_Cliente_ São Paulo.mpp"
ARQUIVO_JSON = Path("saopaulo.json")
ARQUIVO_HIST = Path("historico.json")

mpxj.startJVM()
UniversalProjectReader = jpype.JClass("org.mpxj.reader.UniversalProjectReader")

reader  = UniversalProjectReader()
projeto = reader.read(ARQUIVO_MPP)

tarefas = []
for t in projeto.getTasks():
    nome = str(t.getName()) if t.getName() else None
    if not nome:
        continue
    pct = float(t.getPercentageComplete() or 0)
    recursos = t.getResourceAssignments()
    responsavel = ", ".join(
        str(r.getResource().getName())
        for r in recursos
        if r.getResource() and r.getResource().getName()
    ) or "-"
    pai_task = t.getParentTask()
    tarefas.append({
        "id":          str(t.getID()),
        "nome":        nome,
        "inicio":      str(t.getStart())[:10] if t.getStart() else "-",
        "fim":         str(t.getFinish())[:10] if t.getFinish() else "-",
        "percentual":  pct,
        "responsavel": responsavel,
        "status":      "Concluída"      if pct == 100
                       else "Em andamento" if pct > 0
                       else "Não iniciada",
        "nivel":       int(t.getOutlineLevel() or 1),
        "pai":         str(pai_task.getID()) if pai_task else None,
        "resumo":      bool(t.getSummary()),
    })

saida = {
    "projeto":    "São Paulo",
    "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    "total":      len(tarefas),
    "concluidas": sum(1 for t in tarefas if t["status"] == "Concluída"),
    "andamento":  sum(1 for t in tarefas if t["status"] == "Em andamento"),
    "nao_inic":   sum(1 for t in tarefas if t["status"] == "Não iniciada"),
    "pct_medio":  round(sum(t["percentual"] for t in tarefas) / len(tarefas), 1) if tarefas else 0,
    "tarefas":    tarefas
}

# --- Gerar diff com versão anterior ---
mudancas  = []
pct_antes = None

if ARQUIVO_JSON.exists():
    with open(ARQUIVO_JSON, encoding="utf-8") as f:
        anterior = json.load(f)

    pct_antes = anterior.get("pct_medio")
    old_map   = {t["id"]: t for t in anterior.get("tarefas", [])}
    new_map   = {t["id"]: t for t in tarefas}

    for tid, t_novo in new_map.items():
        if tid not in old_map:
            mudancas.append({
                "tipo":   "nova",
                "tarefa": t_novo["nome"],
                "detalhe": f"Tarefa adicionada ({t_novo['status']})"
            })
        else:
            t_ant    = old_map[tid]
            pct_old  = round(t_ant["percentual"])
            pct_new  = round(t_novo["percentual"])
            if pct_old != pct_new or t_ant["status"] != t_novo["status"]:
                mudancas.append({
                    "tipo":          "avanco" if pct_new >= pct_old else "reducao",
                    "tarefa":        t_novo["nome"],
                    "detalhe":       f"{pct_old}% → {pct_new}%",
                    "status_antes":  t_ant["status"],
                    "status_depois": t_novo["status"]
                })

    for tid in old_map:
        if tid not in new_map:
            mudancas.append({
                "tipo":   "removida",
                "tarefa": old_map[tid]["nome"],
                "detalhe": "Tarefa removida"
            })

# --- Salvar histórico ---
historico = []
if ARQUIVO_HIST.exists():
    with open(ARQUIVO_HIST, encoding="utf-8") as f:
        historico = json.load(f)

entrada = {
    "data":       datetime.now().strftime("%d/%m/%Y %H:%M"),
    "pct_antes":  pct_antes,
    "pct_depois": saida["pct_medio"],
    "concluidas": saida["concluidas"],
    "andamento":  saida["andamento"],
    "nao_inic":   saida["nao_inic"],
    "total":      saida["total"],
    "mudancas":   mudancas
}

historico.insert(0, entrada)

with open(ARQUIVO_HIST, "w", encoding="utf-8") as f:
    json.dump(historico, f, ensure_ascii=False, indent=2)

# --- Salvar JSON principal ---
with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
    json.dump(saida, f, ensure_ascii=False, indent=2)

print(f"Gerado: saopaulo.json com {len(tarefas)} tarefas")
print(f"Histórico: {len(mudancas)} mudança(s) registrada(s)")
