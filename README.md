
# Grafuri de Atac & Patch Optim — Attack Graphs & Optimal Patching

> **Cercetări Operaționale** · Facultatea de Științe Aplicate, UNSTPB  
> Algoritmi: Ford-Fulkerson (flux maxim / tăietură minimă) · Algoritmul Ungar (KUHN) (alocare optimă)  
> Temă Aplicată: **Securitate Cibernetică — Grafuri de Atac & Patch Optim**

---

## 🇷🇴 Română

### Scopul programului

Aplicația demonstrează utilizarea a două algoritmi clasici din **Teoria Grafurilor** — studiați în cadrul materiei de Cercetări Operaționale — aplicați într-un context real de **securitate cibernetică**.

#### Modulul 1 — Grafuri de Atac (Ford-Fulkerson)

Un **graf de atac** modelează căile prin care un atacator poate progresa dintr-un punct de intrare (sursa `S`) până la o țintă valoroasă (destinația `T`), traversând noduri intermediare (servere, servicii, puncte vulnerabile).

Fiecare arc al rețelei are o **capacitate** — interpretată ca dificultatea sau costul unui atac pe acea legătură. Algoritmul **Ford-Fulkerson** determină **fluxul maxim** de atac posibil prin rețea, iar prin teorema **Max-Flow Min-Cut**, identifică automat **tăietura minimă** — adică mulțimea minimală de arce a căror blocare/patchuire oprește complet orice atac.

Aceste arce din tăietura minimă reprezintă **vulnerabilitățile critice** ale infrastructurii: patchuindu-le, se obține cel mai eficient plan de apărare din punct de vedere al costului.

#### Modulul 2 — Patch Optim (Algoritmul Ungar)

Odată identificate vulnerabilitățile critice, acestea trebuie remediate de experți în securitate. Problema **alocării optime** a experților la vulnerabilități se formulează ca o **problemă de afectare** pe un graf bipartit, unde fiecare muchie are un cost asociat (ore de remediere estimate).

**Algoritmul Ungar (KUHN)** rezolvă această problemă în timp polinomial, găsind **cuplajul maximal de cost minim** — adică alocarea experților la vulnerabilități care minimizează timpul total de remediere.

Pașii algoritmului sunt vizualizați interactiv în matricea de costuri: reducerile pe linii și coloane, procedura de etichetare cu zerouri încadrate/barate și deplasarea epsilon sunt afișate pas cu pas.

#### Baza teoretică

Implementarea urmează strict suportul de curs al materiei:

- **Curs 10**: Teoria Grafurilor — Generalități + Algoritmul Ford
- **Curs 11** : Probleme de Afectare, Algoritmul Ungar (KUHN)
- **Seminar 10**: Flux în Rețele, Algoritmul Ford-Fulkerson
- **Seminar 11**: Probleme de Afectare, Algoritmul Ungar

### Cum se pornește aplicația

Aplicația rulează ca un server local Flask și se accesează din browser. **Nu necesită instalare sau fișier executabil.**

```bash
# 1. Instalați dependențele (o singură dată)
pip install flask flask-cors

# 2. Porniți serverul
python grafuri.py

# 3. Deschideți browserul la adresa
http://localhost:5000
```

Serverul poate fi oprit oricând cu `Ctrl+C` în terminal.

### Licență
Vezi [Licență](LICENSE)


---

## 🇬🇧 English

### Purpose

This application demonstrates two classical **Graph Theory** algorithms — studied within the Operational Research course — applied to a real-world **cybersecurity** scenario.

#### Module 1 — Attack Graphs (Ford-Fulkerson)

An **attack graph** models the paths through which an attacker can progress from an entry point (source `S`) to a high-value target (sink `T`), traversing intermediate nodes (servers, services, vulnerable components).

Each arc in the network has a **capacity** — interpreted as the difficulty or cost of exploiting that link. The **Ford-Fulkerson algorithm** computes the **maximum attack flow** through the network, and via the **Max-Flow Min-Cut theorem**, automatically identifies the **minimum cut** — the minimal set of arcs whose removal completely stops any attack.

These min-cut arcs represent the **critical vulnerabilities** of the infrastructure: patching them yields the most cost-effective defense plan.

#### Module 2 — Optimal Patching (Hungarian Algorithm)

Once critical vulnerabilities are identified, they must be remediated by security experts. The **optimal assignment** of experts to vulnerabilities is formulated as an **assignment problem** on a bipartite graph, where each edge carries a cost (estimated remediation hours).

The **Hungarian Algorithm (KUHN)** solves this in polynomial time, finding the **maximum matching of minimum cost** — the assignment of experts to vulnerabilities that minimizes total remediation time.

The algorithm's steps are visualized interactively in the cost matrix: row and column reductions, the labeling procedure with boxed/crossed zeros, and epsilon shifts are displayed step by step.

#### Theoretical basis

The implementation strictly follows the course materials:

- **Lecture 10**: Graph Theory — Fundamentals + Ford's Algorithm
- **Lecture 11** : Assignment Problems, Hungarian Algorithm (KUHN)
- **Seminar 10** : Network Flow, Ford-Fulkerson Algorithm
- **Seminar 11**: Assignment Problems, Hungarian Algorithm

### How to run

The application runs as a local Flask server and is accessed from a browser. **No installation wizard or executable file required.**

```bash
# 1. Install dependencies (once)
pip install flask flask-cors

# 2. Start the server
python grafuri.py

# 3. Open your browser at
http://localhost:5000
```


Stop the server at any time with `Ctrl+C` in the terminal.

### License

See [License](LICENSE)
