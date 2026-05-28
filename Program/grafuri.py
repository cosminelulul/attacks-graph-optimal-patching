

import math
import random
from collections import deque

import threading
import webbrowser

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


class Graf:


    def __init__(self, orientat: bool = True):
        self.orientat = orientat
        # X — multimea varfurilor
        self.X: list = []
        # Gamma: xi -> {xj: valoare_arc}  (Definitia 1, Curs 4)
        self.Gamma: dict = {}


    def adauga_varf(self, varf) -> None:
        """Adauga varful `varf` in multimea X daca nu exista deja."""
        if varf not in self.Gamma:
            self.X.append(varf)
            self.Gamma[varf] = {}

    def adauga_arc(self, xi, xj, valoare: float = 1.0) -> None:

        self.adauga_varf(xi)
        self.adauga_varf(xj)
        self.Gamma[xi][xj] = valoare
        if not self.orientat:
            self.Gamma[xj][xi] = valoare

    def elimina_arc(self, xi, xj) -> None:
        """Elimina arcul (xi, xj) din graf."""
        if xi in self.Gamma and xj in self.Gamma[xi]:
            del self.Gamma[xi][xj]
        if not self.orientat:
            if xj in self.Gamma and xi in self.Gamma[xj]:
                del self.Gamma[xj][xi]

    def multimea_arcelor(self) -> list:

        arce = []
        vazute = set()
        for xi in self.X:
            for xj, val in self.Gamma[xi].items():
                if self.orientat:
                    arce.append((xi, xj, val))
                else:
                    pereche = tuple(sorted([str(xi), str(xj)]))
                    if pereche not in vazute:
                        arce.append((xi, xj, val))
                        vazute.add(pereche)
        return arce

    def valoare_arc(self, xi, xj) -> float:
        return self.Gamma.get(xi, {}).get(xj, math.inf)

    def exista_arc(self, xi, xj) -> bool:
        return xj in self.Gamma.get(xi, {})



    def ordin(self) -> int:
        """
        Definitia 1 (Curs 4): card(X) = |X| = n reprezinta ordinul grafului.
        """
        return len(self.X)

    def numar_arce(self) -> int:

        return len(self.multimea_arcelor())

    def gamma_plus(self, xi) -> dict:

        return dict(self.Gamma.get(xi, {}))

    def gamma_minus(self, xi) -> dict:

        pred = {}
        for xk in self.X:
            if xi in self.Gamma.get(xk, {}):
                pred[xk] = self.Gamma[xk][xi]
        return pred

    def grad_exterior(self, xi) -> int:
        return len(self.Gamma.get(xi, {}))

    def grad_interior(self, xi) -> int:
        return len(self.gamma_minus(xi))

    def grad(self, xi) -> int:
        if self.orientat:
            return self.grad_exterior(xi) + self.grad_interior(xi)
        return len(self.Gamma.get(xi, {}))

    def este_izolat(self, xi) -> bool:
        return self.grad_exterior(xi) == 0 and self.grad_interior(xi) == 0

    def varfuri_adiacente(self, xi) -> list:
        vecini = set(self.Gamma.get(xi, {}).keys())
        if self.orientat:
            vecini |= set(self.gamma_minus(xi).keys())
        return list(vecini)



    def este_finit(self) -> bool:
        return True  # implementarea suporta doar grafuri finite

    def are_bucle(self) -> bool:
        return any(xi in self.Gamma.get(xi, {}) for xi in self.X)

    def este_simplu(self) -> bool:
        return not self.are_bucle()

    def este_conex(self) -> bool:
        if not self.X:
            return True
        vizitat = set()
        coada = deque([self.X[0]])
        vizitat.add(self.X[0])
        while coada:
            varf = coada.popleft()
            for vecin in self.Gamma.get(varf, {}):
                if vecin not in vizitat:
                    vizitat.add(vecin)
                    coada.append(vecin)
            if not self.orientat:
                for vecin in self.gamma_minus(varf):
                    if vecin not in vizitat:
                        vizitat.add(vecin)
                        coada.append(vecin)
        return len(vizitat) == len(self.X)

    def este_retea(self, sursa, destinatie) -> bool:
        if not self.orientat:
            return False
        if not self.este_conex():
            return False
        if self.are_bucle():
            return False
        sursa_ok = len(self.gamma_minus(sursa)) == 0
        dest_ok = len(self.Gamma.get(destinatie, {})) == 0
        return sursa_ok and dest_ok


    def subgraf(self, X_prim: list) -> "Graf":
        g = Graf(orientat=self.orientat)
        for v in X_prim:
            if v in self.Gamma:
                g.adauga_varf(v)
        for v in X_prim:
            for u, val in self.Gamma.get(v, {}).items():
                if u in X_prim:
                    g.adauga_arc(v, u, val)
        return g

    def graf_partial(self, arce_selectate: list) -> "Graf":
        g = Graf(orientat=self.orientat)
        for v in self.X:
            g.adauga_varf(v)
        for arc in arce_selectate:
            xi, xj = arc[0], arc[1]
            if self.exista_arc(xi, xj):
                g.adauga_arc(xi, xj, self.valoare_arc(xi, xj))
        return g


    def este_drum(self, secventa: list) -> bool:
        for i in range(len(secventa) - 1):
            if not self.exista_arc(secventa[i], secventa[i + 1]):
                return False
        return True

    def este_drum_simplu(self, secventa: list) -> bool:
        """Drum simplu: arcele care il compun sunt distincte."""
        if not self.este_drum(secventa):
            return False
        arce = [(secventa[i], secventa[i + 1]) for i in range(len(secventa) - 1)]
        return len(arce) == len(set(arce))

    def este_drum_elementar(self, secventa: list) -> bool:
        return self.este_drum_simplu(secventa) and len(secventa) == len(set(secventa))

    def este_circuit(self, secventa: list) -> bool:
        return (len(secventa) > 1 and
                secventa[0] == secventa[-1] and
                self.este_drum_simplu(secventa))

    def valoare_drum(self, secventa: list) -> float:
        if not self.este_drum(secventa):
            return math.inf
        return sum(self.valoare_arc(secventa[i], secventa[i + 1])
                   for i in range(len(secventa) - 1))

    def lungime_drum(self, secventa: list) -> int:
        return len(secventa) - 1


    def capacitate_taietura(self, A: set, sursa, destinatie) -> float:
        if sursa in A or destinatie not in A:
            return math.inf
        total = 0.0
        for xi in self.X:
            if xi not in A:
                for xj, cap in self.Gamma.get(xi, {}).items():
                    if xj in A:
                        total += cap
        return total

    # ----------------------------------------------------------
    # Reprezentare text (pentru UI)
    # ----------------------------------------------------------

    def __repr__(self) -> str:
        tip = "orientat" if self.orientat else "neorientat"
        linii = [f"Graf {tip}: |X|={self.ordin()}, |U|={self.numar_arce()}"]
        for xi in self.X:
            succs = ", ".join(f"{xj}({v})" for xj, v in self.Gamma[xi].items())
            linii.append(f"  Gamma({xi}) = {{{succs}}}")
        return "\n".join(linii)

    def la_dict(self) -> dict:
        """Serializeaza graful intr-un dict simplu (util pentru UI)."""
        return {
            "orientat": self.orientat,
            "varfuri": list(self.X),
            "arce": [(xi, xj, v) for xi, xj, v in self.multimea_arcelor()],
        }



def algoritmul_ford(graf: Graf, sursa) -> dict:
    INF = math.inf
    arce = graf.multimea_arcelor()  # lista fixa de arce (orice ordine)

    # Initializare (Pasul 1 — Iteratia I0)
    lam = {v: (0.0 if v == sursa else INF) for v in graf.X}
    pred = {v: None for v in graf.X}
    arce_marcate = set()  # arcele marcate cu (*) la iteratia curenta

    iteratii_log = []
    iteratie_nr = 0

    while True:
        modificat = False
        log_iter = {
            "iteratie": iteratie_nr,
            "lambda_inainte": dict(lam),
            "modificari": [],
        }

        for xi, xj, fij in arce:
            li = lam[xi]
            lj = lam[xj]
            # Conditia de relaxare: lambda[j] > lambda[i] + f(xi, xj)
            # (Cazul ∞ - ∞ => nu se modifica)
            if li == INF:
                continue
            if lj == INF or lj > li + fij:
                lam[xj] = li + fij
                pred[xj] = xi
                arce_marcate.discard(  # daca era un arc anterior marcat spre xj
                    next((a for a in arce_marcate if a[1] == xj), None)
                )
                arce_marcate = {a for a in arce_marcate if a[1] != xj}
                arce_marcate.add((xi, xj, fij))
                modificat = True
                log_iter["modificari"].append({
                    "arc": (xi, xj),
                    "lambda_vechi": lj,
                    "lambda_nou": lam[xj],
                    "formula": f"λ({xj}) = λ({xi}) + f({xi},{xj}) = {li} + {fij} = {lam[xj]}",
                })

        log_iter["lambda_dupa"] = dict(lam)
        log_iter["TO"] = not modificat
        iteratii_log.append(log_iter)

        if not modificat:
            break  # STOP — Testul de optimalitate satisfacut

        iteratie_nr += 1

    return {
        "lambda": lam,
        "predecesori": pred,
        "iteratii": iteratii_log,
        "arce_marcate": list(arce_marcate),
        "ISTOP": iteratie_nr,
    }


def drum_minim_ford(graf: Graf, sursa, destinatie) -> dict:
    ford = algoritmul_ford(graf, sursa)
    lam = ford["lambda"]
    pred = ford["predecesori"]

    if lam[destinatie] == math.inf:
        return {
            "drum": [],
            "valoare": math.inf,
            "ford": ford,
            "mesaj": f"Nu exista drum de la {sursa} la {destinatie}.",
        }
    drum = []
    varf_curent = destinatie
    while varf_curent is not None:
        drum.append(varf_curent)
        varf_curent = pred[varf_curent]
    drum.reverse()

    return {
        "drum": drum,
        "valoare": lam[destinatie],
        "ford": ford,
        "mesaj": (f"Drumul minim: {' -> '.join(str(v) for v in drum)}\n"
                  f"Valoare (λ[{destinatie}]) = {lam[destinatie]}\n"
                  f"Iteratii efectuate: {ford['ISTOP'] + 1} (ISTOP = I{ford['ISTOP']})"),
    }



def algoritmul_ford_fulkerson(capacitati: dict, sursa, destinatie) -> dict:
    # Construim multimea varfurilor
    varfuri = set()
    for (xi, xj) in capacitati:
        varfuri.add(xi)
        varfuri.add(xj)

    # Initializare flux f0 = 0 pe toate arcele
    flux = {arc: 0.0 for arc in capacitati}

    def capacitate_reziduala(xi, xj):
        """Capacitate reziduala: rij = cij - f(xi,xj) + f(xj,xi)."""
        forward = capacitati.get((xi, xj), 0) - flux.get((xi, xj), 0)
        backward = flux.get((xj, xi), 0)
        return forward + backward

    iteratii_log = []
    iteratie_nr = 0

    while True:
        # ── Procedura de etichetare (BFS pentru drum de ameliorare) ──
        etichete = {sursa: (None, math.inf, "+")}
        # eticheta: {varf: (predecesorul, delta_min, semn)}
        coada = deque([sursa])
        drum_gasit = False

        log_etichetare = {
            "iteratie": iteratie_nr,
            "flux_curent": sum(flux.get((sursa, xj), 0)
                               for xj in varfuri if (sursa, xj) in capacitati),
            "etichete": {},
            "drum": [],
            "delta": 0,
            "descriere": "",
        }

        while coada and destinatie not in etichete:
            xi = coada.popleft()
            _, delta_xi, _ = etichete[xi]

            # Arce forward nesaturate: xi -> xj, f(xi,xj) < c(xi,xj)
            for (a, b), cap in capacitati.items():
                if a == xi and b not in etichete:
                    rez = cap - flux.get((a, b), 0)
                    if rez > 0:
                        delta = min(delta_xi, rez)
                        etichete[b] = (xi, delta, "+")
                        coada.append(b)

            # Arce backward: xj -> xi cu flux > 0 (arcul invers)
            for (a, b), f_val in flux.items():
                if b == xi and a not in etichete and f_val > 0:
                    delta = min(delta_xi, f_val)
                    etichete[a] = (xi, delta, "-")
                    coada.append(a)

        log_etichetare["etichete"] = {
            str(v): {"pred": str(e[0]), "delta": e[1], "semn": e[2]}
            for v, e in etichete.items()
        }

        if destinatie not in etichete:
            # STOP — nu exista drum de ameliorare => flux maxim
            log_etichetare["descriere"] = (
                f"[TO(I{iteratie_nr})] Etichetare: [{sursa}] -/-> [{destinatie}] => NU => STOP"
            )
            iteratii_log.append(log_etichetare)
            break

        # ── Reconstructia drumului de ameliorare ──
        drum = []
        varf_c = destinatie
        while varf_c != sursa:
            pred_c, _, semn = etichete[varf_c]
            drum.append((pred_c, varf_c, semn))
            varf_c = pred_c
        drum.reverse()

        # ── Delta (capacitatea reziduala minima pe drum) ──
        _, delta, _ = etichete[destinatie]

        # ── Actualizare flux ──
        for (xi, xj, semn) in drum:
            if semn == "+":
                flux[(xi, xj)] = flux.get((xi, xj), 0) + delta
            else:
                flux[(xj, xi)] = flux.get((xj, xi), 0) - delta

        valoare_flux = sum(flux.get((sursa, xj), 0)
                          for xj in varfuri if (sursa, xj) in capacitati)

        lant_str = " -> ".join(
            [str(sursa)] + [str(xj) for (_, xj, _) in drum]
        )
        cap_rezid_str = " ".join(
            str(int(capacitate_reziduala(xi, xj))) for (xi, xj, _) in drum
        )
        log_etichetare["drum"] = [(str(a), str(b), s) for a, b, s in drum]
        log_etichetare["delta"] = delta
        log_etichetare["valoare_flux_dupa"] = valoare_flux
        log_etichetare["descriere"] = (
            f"[TO(I{iteratie_nr})] [{sursa}] -> [{destinatie}]: DA\n"
            f"  Lant: {lant_str}\n"
            f"  Cap. reziduale: {cap_rezid_str}\n"
            f"  min = {delta}  =>  f{iteratie_nr} = f{iteratie_nr - 1 if iteratie_nr > 0 else 0} + {delta} = {valoare_flux}"
        )
        iteratii_log.append(log_etichetare)
        iteratie_nr += 1

    flux_maxim = sum(flux.get((sursa, xj), 0)
                     for xj in varfuri if (sursa, xj) in capacitati)

    A = set(etichete.keys())
    taietura = []
    for (xi, xj), cap in capacitati.items():
        if xi in A and xj not in A:
            taietura.append((xi, xj, cap, flux.get((xi, xj), 0)))

    cap_taietura = sum(cap for (_, _, cap, _) in taietura)

    return {
        "flux_maxim": flux_maxim,
        "flux": flux,
        "iteratii": iteratii_log,
        "taietura": taietura,
        "cap_taietura": cap_taietura,
        "ISTOP": iteratie_nr,
        "mesaj": (
            f"Flux maxim: fmax = {flux_maxim}\n"
            f"Taietura minima: {[(xi, xj) for xi, xj, _, _ in taietura]}\n"
            f"Capacitate taietura: CT = {cap_taietura}\n"
            f"Verificare: fmax = CT = {flux_maxim} {'✓' if abs(flux_maxim - cap_taietura) < 1e-9 else '✗'}"
        ),
    }


def verifica_flux(flux: dict, capacitati: dict, sursa, destinatie) -> dict:
    varfuri = set()
    for (xi, xj) in capacitati:
        varfuri.add(xi)
        varfuri.add(xj)

    erori = []
    # Conditia 1
    for (xi, xj), cap in capacitati.items():
        fij = flux.get((xi, xj), 0)
        if fij < 0 or fij > cap:
            erori.append(f"Conditia 1 incalcata: f({xi},{xj}) = {fij}, c = {cap}")

    # Conditia 2
    for v in varfuri:
        if v in (sursa, destinatie):
            continue
        intrare = sum(flux.get((u, v), 0) for u in varfuri if (u, v) in capacitati)
        iesire = sum(flux.get((v, u), 0) for u in varfuri if (v, u) in capacitati)
        if abs(intrare - iesire) > 1e-9:
            erori.append(f"Conditia 2 incalcata la {v}: intrare={intrare}, iesire={iesire}")

    # Conditia 3
    v_sursa = sum(flux.get((sursa, u), 0) for u in varfuri if (sursa, u) in capacitati)
    v_dest = sum(flux.get((u, destinatie), 0) for u in varfuri if (u, destinatie) in capacitati)
    valid_3 = abs(v_sursa - v_dest) < 1e-9

    return {
        "valid": len(erori) == 0 and valid_3,
        "erori": erori,
        "valoare_flux_sursa": v_sursa,
        "valoare_flux_destinatie": v_dest,
        "conservare_valoare": valid_3,
    }



class GrafBipartit:


    def __init__(self, X: list, Y: list):
        if set(X) & set(Y):
            raise ValueError("X si Y trebuie sa fie disjuncte (X ∩ Y = ∅).")
        self.X = list(X)
        self.Y = list(Y)
        # U: {xi: {yj: valoare}} — doar muchii intre X si Y
        self.U: dict = {x: {} for x in X}

    def adauga_muchie(self, xi, yj, valoare: float = 1.0) -> None:
        if xi not in self.X:
            raise ValueError(f"{xi} nu apartine lui X.")
        if yj not in self.Y:
            raise ValueError(f"{yj} nu apartine lui Y.")
        self.U[xi][yj] = valoare

    def valoare_muchie(self, xi, yj) -> float:
        return self.U.get(xi, {}).get(yj, math.inf)

    def multimea_muchiilor(self) -> list:
        return [(xi, yj, val)
                for xi in self.X
                for yj, val in self.U[xi].items()]

    def gamma(self, xi) -> list:
        return list(self.U.get(xi, {}).keys())

    def este_cuplaj(self, W: list) -> bool:

        x_folositi, y_folositi = set(), set()
        for (xi, yj) in W:
            if xi in x_folositi or yj in y_folositi:
                return False
            x_folositi.add(xi)
            y_folositi.add(yj)
        return True

    def valoare_cuplaj(self, W: list) -> float:

        return sum(self.valoare_muchie(xi, yj) for (xi, yj) in W)

    def dimensiune_cuplaj(self, W: list) -> int:
        """Numarul de muchii din cuplaj."""
        return len(W)




def algoritmul_ungar(matrice_costuri: list, minimizare: bool = True) -> dict:
    import copy

    n = len(matrice_costuri)
    # Validare: matrice patrata
    for rand in matrice_costuri:
        if len(rand) != n:
            raise ValueError("Matricea costurilor trebuie sa fie patrata (n x n).")

    # Copie de lucru (float, INF pentru cuplaje imposibile)
    INF = math.inf
    C = [[float(matrice_costuri[i][j]) for j in range(n)] for i in range(n)]

    # Daca maximizare: transformam in minimizare (negam elementele finite)
    if not minimizare:
        max_val = max(C[i][j] for i in range(n) for j in range(n)
                      if C[i][j] != INF)
        C = [[max_val - C[i][j] if C[i][j] != INF else INF
              for j in range(n)] for i in range(n)]

    iteratii_log = []

    u = []  # minimele pe linii
    for i in range(n):
        fin = [C[i][j] for j in range(n) if C[i][j] != INF]
        u.append(min(fin) if fin else 0)
        for j in range(n):
            if C[i][j] != INF:
                C[i][j] -= u[-1]

    v = []  # minimele pe coloane
    for j in range(n):
        fin = [C[i][j] for i in range(n) if C[i][j] != INF]
        col_min = min(fin) if fin else 0
        v.append(col_min)
        for i in range(n):
            if C[i][j] != INF:
                C[i][j] -= col_min

    epsiloane = []  # lista cu (epsilon, n0_iter)

    def procedura_etichetare(C):
        match_row = {}  # {i: j}
        match_col = {}  # {j: i}

        def dfs(i, visited):
            for j in range(n):
                if abs(C[i][j]) < 1e-9 and C[i][j] != INF and j not in visited:
                    visited.add(j)
                    if j not in match_col or dfs(match_col[j], visited):
                        match_row[i] = j
                        match_col[j] = i
                        return True
            return False

        for i in range(n):
            dfs(i, set())

        incadrat = dict(match_row)

        # ── Determinam zerourile barate ──
        barate = set()
        col_ocupata = set(incadrat.values())
        for i, j_ales in incadrat.items():
            # Baram celelalte zerouri de pe linia i
            for j2 in range(n):
                if j2 != j_ales and abs(C[i][j2]) < 1e-9 and C[i][j2] != INF:
                    barate.add((i, j2))
            # Baram celelalte zerouri de pe coloana j_ales
            for i2 in range(n):
                if i2 != i and abs(C[i2][j_ales]) < 1e-9 and C[i2][j_ales] != INF:
                    barate.add((i2, j_ales))

        n0 = len(incadrat)
        return incadrat, barate, n0

    def procedura_marcaj(incadrat, barate):
        # (1) Marcam liniile fara zero incadrat
        linii_marcate = set(i for i in range(n) if i not in incadrat)
        coloane_marcate = set()

        schimbare = True
        while schimbare:
            schimbare = False
            # (2) Coloane cu zero barat in linii marcate
            for (i, j) in barate:
                if i in linii_marcate and j not in coloane_marcate:
                    coloane_marcate.add(j)
                    schimbare = True
            # (3) Linii cu zero incadrat in coloane marcate
            for i, j in incadrat.items():
                if j in coloane_marcate and i not in linii_marcate:
                    linii_marcate.add(i)
                    schimbare = True

        return linii_marcate, coloane_marcate

    def deplasare_zerouri(C, linii_marcate, coloane_marcate):
        linii_nemarcate = set(range(n)) - linii_marcate  # = L(fara *) = linii taiate

        T1_vals = []
        for i in range(n):
            for j in range(n):
                if C[i][j] == INF:
                    continue
                taiere_L = i in linii_nemarcate   # linia e taiata (nemarcata cu *)
                taiere_C = j in coloane_marcate    # coloana e taiata (marcata cu *)
                # T1: nici linia nici coloana taiata, si valoarea != 0
                if not taiere_L and not taiere_C and abs(C[i][j]) > 1e-9:
                    T1_vals.append(C[i][j])

        eps = min(T1_vals) if T1_vals else 0

        C_nou = copy.deepcopy(C)
        for i in range(n):
            for j in range(n):
                if C_nou[i][j] == INF:
                    continue
                taiere_L = i in linii_nemarcate
                taiere_C = j in coloane_marcate
                if not taiere_L and not taiere_C:   # T1: scade eps
                    C_nou[i][j] -= eps
                elif taiere_L and taiere_C:          # T3: creste eps
                    C_nou[i][j] += eps
                # T2 (taiate exact o data): ramane neschimbat
        return C_nou, eps

    # ── Iteratii principale ──
    for iteratie in range(200):  # max 200 iteratii (convergenta garantata)
        incadrat, barate, n0 = procedura_etichetare(C)

        log_iter = {
            "iteratie": iteratie,
            "matrice": copy.deepcopy(C),
            "incadrat": dict(incadrat),
            "barate": list(barate),
            "n0": n0,
            "n": n,
            "STOP": n0 == n,
        }

        if n0 == n:
            # STOP — cuplaj maximal gasit
            log_iter["descriere"] = f"n[0] = {n0} = n = {n} => STOP algoritmul."
            iteratii_log.append(log_iter)
            break

        # Suport minim si deplasare
        linii_marc, col_marc = procedura_marcaj(incadrat, barate)
        C, eps = deplasare_zerouri(C, linii_marc, col_marc)
        epsiloane.append((eps, n0))

        log_iter["linii_marcate"] = list(linii_marc)
        log_iter["coloane_marcate"] = list(col_marc)
        log_iter["epsilon"] = eps
        log_iter["descriere"] = (
            f"n[0] = {n0} < n = {n}  =>  ε = {eps}\n"
            f"  Suport minim: L(fara *)={sorted(set(range(n)) - linii_marc)}, "
            f"C(*)={sorted(col_marc)}\n"
            f"  T1 - ε, T3 + ε, T2 neschimbate."
        )
        iteratii_log.append(log_iter)

    # ── Cuplajul maximal (solutia) ──
    cuplaj = [(i, incadrat[i]) for i in sorted(incadrat.keys())]

    # ── Valoarea optima a cuplajului (din matricea originala) ──
    C_orig = [[float(matrice_costuri[i][j]) for j in range(n)] for i in range(n)]
    valoare = sum(C_orig[i][j] for (i, j) in cuplaj)
    if not minimizare:
        # Daca maximizare, valoarea era negata; returnam valoarea originala
        valoare = sum(C_orig[i][j] for (i, j) in cuplaj)

    # ── Formula de verificare (Seminar 11, Pasul 6) ──
    # v(Wmax) = Σ ui + Σ vj + Σ εk * (n - n[0]k)
    verificare = sum(u) + sum(v) + sum(eps * (n - n0k) for (eps, n0k) in epsiloane)

    # ── Mesaj descriptiv (pentru UI) ──
    tip_opt = "minima" if minimizare else "maxima"
    perechi_str = ", ".join(f"(x{i + 1}, y{j + 1})" for (i, j) in cuplaj)
    mesaj = (
        f"Cuplaj maximal de valoare {tip_opt}:\n"
        f"  Wmax = {{{perechi_str}}}\n"
        f"  v(Wmax) = {valoare}\n"
        f"Verificare: Σu + Σv + Σε*(n-n0) = "
        f"{sum(u)} + {sum(v)} + {sum(eps*(n-n0k) for eps, n0k in epsiloane)} = {verificare}"
        + (" ✓" if abs(valoare - verificare) < 1e-6 else " ✗")
    )

    return {
        "cuplaj": cuplaj,
        "valoare": valoare,
        "iteratii": iteratii_log,
        "matrice_finala": C,
        "n": n,
        "minimizare": minimizare,
        "mesaj": mesaj,
        "verificare": verificare,
        "u_linii": u,
        "v_coloane": v,
        "epsiloane": epsiloane,
        "ISTOP": len(iteratii_log) - 1,
    }




def teorema_konig_hall(graf_bipartit: GrafBipartit) -> dict:
    X = graf_bipartit.X
    n = len(X)
    violari = []

    # Iteram peste toate submultimile nevide ale lui X
    for masca in range(1, 1 << n):
        A = [X[i] for i in range(n) if masca & (1 << i)]
        N_A = set()
        for xi in A:
            N_A |= set(graf_bipartit.gamma(xi))
        if len(N_A) < len(A):
            violari.append({
                "A": A,
                "Gamma_A": list(N_A),
                "conditie": f"|Γ({A})| = {len(N_A)} < |A| = {len(A)}"
            })

    satisfacut = len(violari) == 0
    return {
        "satisfacut": satisfacut,
        "cuplare_completa_posibila": satisfacut,
        "violari": violari,
        "mesaj": (
            "Conditia Hall este satisfacuta => X poate fi cuplat in Y."
            if satisfacut else
            f"Conditia Hall NU este satisfacuta ({len(violari)} violari)."
        ),
    }


def teorema_konig_ore(graf_bipartit: GrafBipartit) -> dict:
    X = graf_bipartit.X
    n = len(X)
    max_deficit = 0
    A_optim = []

    for masca in range(1, 1 << n):
        A = [X[i] for i in range(n) if masca & (1 << i)]
        N_A = set()
        for xi in A:
            N_A |= set(graf_bipartit.gamma(xi))
        deficit = len(A) - len(N_A)
        if deficit > max_deficit:
            max_deficit = deficit
            A_optim = A

    mu = n - max_deficit
    return {
        "mu": mu,
        "suport_minim_marime": mu,
        "A_optim": A_optim,
        "max_deficit": max_deficit,
        "formula": f"µ(G) = |X| - max(|A| - |Γ(A)|) = {n} - {max_deficit} = {mu}",
    }


def teorema_konig_egervary(graf_bipartit: GrafBipartit) -> dict:
    ore = teorema_konig_ore(graf_bipartit)
    mu = ore["mu"]

    # Cuplaj maxim prin BFS (algoritmul Hopcroft-Karp simplificat)
    cuplaj_X = {}  # {xi: yj}
    cuplaj_Y = {}  # {yj: xi}

    def bfs_augmentare():
        dist = {}
        coada = deque()
        for xi in graf_bipartit.X:
            if xi not in cuplaj_X:
                dist[xi] = 0
                coada.append(xi)
            else:
                dist[xi] = math.inf
        dist[None] = math.inf
        while coada:
            xi = coada.popleft()
            if dist[xi] < dist[None]:
                for yj in graf_bipartit.gamma(xi):
                    xi_cuplat = cuplaj_Y.get(yj)
                    if dist.get(xi_cuplat, math.inf) == math.inf:
                        dist[xi_cuplat] = dist[xi] + 1
                        if xi_cuplat is not None:
                            coada.append(xi_cuplat)
        return dist[None] != math.inf

    def dfs_augmentare(xi, dist):
        for yj in graf_bipartit.gamma(xi):
            xi_cuplat = cuplaj_Y.get(yj)
            if dist.get(xi_cuplat, math.inf) == dist.get(xi, 0) + 1:
                if xi_cuplat is None or dfs_augmentare(xi_cuplat, dist):
                    cuplaj_X[xi] = yj
                    cuplaj_Y[yj] = xi
                    return True
        dist[xi] = math.inf
        return False

    while bfs_augmentare():
        dist = {}
        coada = deque()
        for xi in graf_bipartit.X:
            if xi not in cuplaj_X:
                dist[xi] = 0
                coada.append(xi)
            else:
                dist[xi] = math.inf
        for xi in graf_bipartit.X:
            if xi not in cuplaj_X:
                dfs_augmentare(xi, dist)

    wmax = list(cuplaj_X.items())
    satisfacut = len(wmax) == mu

    return {
        "wmax_marime": len(wmax),
        "mu": mu,
        "wmax": wmax,
        "satisfacut": satisfacut,
        "mesaj": (
            f"|Wmax| = {len(wmax)},  µ(G) = {mu}  => "
            f"Teorema König-Egerváry {'verificata ✓' if satisfacut else 'NU verificata ✗'}"
        ),
    }


def propozitia_1_afectare(matrice_costuri: list, linie_sau_coloana: str,
                           indice: int, alfa: float) -> dict:
    import copy
    n = len(matrice_costuri)
    C_nou = copy.deepcopy(matrice_costuri)

    if linie_sau_coloana.lower() in ("linie", "l"):
        for j in range(n):
            if C_nou[indice][j] != math.inf:
                C_nou[indice][j] += alfa
    else:
        for i in range(n):
            if C_nou[i][indice] != math.inf:
                C_nou[i][indice] += alfa

    rez_orig = algoritmul_ungar(matrice_costuri)
    rez_nou = algoritmul_ungar(C_nou)

    cuplaj_orig = rez_orig["cuplaj"]
    cuplaj_nou = rez_nou["cuplaj"]
    aceleasi = sorted(cuplaj_orig) == sorted(cuplaj_nou)

    return {
        "cuplaj_original": cuplaj_orig,
        "cuplaj_modificat": cuplaj_nou,
        "acelasi_cuplaj": aceleasi,
        "valoare_originala": rez_orig["valoare"],
        "valoare_modificata": rez_nou["valoare"],
        "diferenta_valoare": rez_nou["valoare"] - rez_orig["valoare"],
        "alfa": alfa,
        "mesaj": (
            f"Propozitia 1 {'verificata ✓' if aceleasi else 'NU verificata ✗'}:\n"
            f"  Cuplajul nu s-a modificat dupa adaugarea α={alfa} pe "
            f"{'linia' if linie_sau_coloana.lower() in ('linie', 'l') else 'coloana'} {indice}."
        ),
    }



def matrice_la_text(matrice: list, zerouri_incadrate: dict = None,
                    zerouri_barate: set = None, latime_col: int = 6) -> list:
    n = len(matrice)
    linii = []
    for i in range(n):
        rand = []
        for j in range(n):
            val = matrice[i][j]
        # formatare valoare
            if val == math.inf:
                s = "INF"
            elif isinstance(val, float) and val == int(val):
                s = str(int(val))
            else:
                s = f"{val:.2f}"
            # marcaje
            if zerouri_incadrate and zerouri_incadrate.get(i) == j:
                s = f"[{s}]"
            elif zerouri_barate and (i, j) in zerouri_barate:
                s = f"({s})"
            rand.append(s.center(latime_col))
        linii.append("  ".join(rand))
    return linii


def flux_la_text(flux: dict, capacitati: dict) -> list:
    linii = []
    for (xi, xj), cap in sorted(capacitati.items(), key=lambda x: str(x)):
        f_val = flux.get((xi, xj), 0)
        linii.append(f"  ({xi}, {xj}): {int(f_val)} / {int(cap)}")
    return linii


def iteratii_ford_la_text(iteratii: list) -> list:
    linii = []
    for it in iteratii:
        linii.append(f"\n{'─' * 50}")
        linii.append(f"Iteratia I{it['iteratie']}")
        linii.append(f"{'─' * 50}")
        lam_str = "  ".join(f"λ({v})={val if val != math.inf else '∞'}"
                            for v, val in it["lambda_inainte"].items())
        linii.append(f"  λ initial: {lam_str}")
        for mod in it["modificari"]:
            linii.append(f"  * {mod['formula']}")
        if not it["modificari"]:
            linii.append("  (nicio modificare)")
        if it["TO"]:
            linii.append(f"  [TO(I{it['iteratie']})] => STOP")
    return linii


def iteratii_fulkerson_la_text(iteratii: list) -> list:
    linii = []
    for it in iteratii:
        linii.append(f"\n{'─' * 60}")
        linii.append(f"Iteratia I{it['iteratie']}")
        linii.append(f"{'─' * 60}")
        v_curent = it.get("flux_curent", 0)
        linii.append(f"  Valoare flux curenta: f = {v_curent}")
        linii.append(f"  {it.get('descriere', '')}")
    return linii


def iteratii_ungar_la_text(iteratii: list) -> list:
    linii = []
    for it in iteratii:
        linii.append(f"\n{'═' * 60}")
        linii.append(f"Iteratia I{it['iteratie'] + 1}")
        linii.append(f"{'═' * 60}")
        n0 = it["n0"]
        n = it["n"]
        linii.append(f"  n[0] = {n0}  (zerouri incadrate)")
        linii.append(f"  {it.get('descriere', '')}")
        if it.get("STOP"):
            linii.append(f"  >> STOP: n[0] = n = {n} ✓")
    return linii


def cuplaj_la_text(cuplaj: list, matrice_costuri: list,
                   etichetare_x: list = None, etichetare_y: list = None) -> list:
    linii = ["Cuplaj maximal:"]
    for (i, j) in cuplaj:
        xi = etichetare_x[i] if etichetare_x else f"x{i + 1}"
        yj = etichetare_y[j] if etichetare_y else f"y{j + 1}"
        cij = matrice_costuri[i][j]
        linii.append(f"  ({xi}, {yj})  c = {cij}")
    valoare = sum(matrice_costuri[i][j] for (i, j) in cuplaj)
    linii.append(f"\n  Valoare totala: v(Wmax) = {valoare}")
    return linii



def graf_din_lista_arce(arce: list, orientat: bool = True) -> Graf:
    g = Graf(orientat=orientat)
    for arc in arce:
        if len(arc) == 2:
            g.adauga_arc(arc[0], arc[1])
        else:
            g.adauga_arc(arc[0], arc[1], arc[2])
    return g


def graf_din_matrice_adiacenta(matrice: list, varfuri: list = None,
                                orientat: bool = True) -> Graf:
    n = len(matrice)
    etichete = varfuri if varfuri else list(range(1, n + 1))
    g = Graf(orientat=orientat)
    for v in etichete:
        g.adauga_varf(v)
    for i in range(n):
        for j in range(n):
            val = matrice[i][j]
            if val and val != 0:
                g.adauga_arc(etichete[i], etichete[j], float(val))
    return g


def capacitati_din_lista(arce_cap: list) -> dict:
    return {(xi, xj): float(cap) for xi, xj, cap in arce_cap}


def matrice_costurilor_din_dict(n: int, costuri: dict,
                                 valoare_lipsa: float = math.inf) -> list:
    C = [[valoare_lipsa] * n for _ in range(n)]
    for (i, j), cost in costuri.items():
        C[i][j] = float(cost)
    return C


# API REST (Flask)

import sys
import os


app = Flask(  __name__,)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')



def _coerce_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return val


def _generate_attack_network(min_nodes: int = 10, max_nodes: int = 20) -> dict:
    n = random.randint(min_nodes, max_nodes)
    source = 0
    sink = n - 1

    layer_count = random.randint(4, 6)
    layers = {i: [] for i in range(layer_count)}

    layers[0].append(source)
    layers[layer_count - 1].append(sink)

    mid_nodes = list(range(1, n - 1))
    random.shuffle(mid_nodes)

    for idx, node_id in enumerate(mid_nodes):
        layer = 1 + (idx % max(1, layer_count - 2))
        layers[layer].append(node_id)

    nodes = []
    server_count = 1
    for layer, node_ids in layers.items():
        for node_id in node_ids:
            if node_id == source:
                nodes.append({
                    "id": node_id,
                    "label": "S",
                    "emoji": "👾",
                    "layer": layer,
                })
            elif node_id == sink:
                nodes.append({
                    "id": node_id,
                    "label": "T",
                    "emoji": "🗄️",
                    "layer": layer,
                })
            else:
                nodes.append({
                    "id": node_id,
                    "label": f"#{server_count}",
                    "emoji": "🖥️",
                    "layer": layer,
                })
                server_count += 1

    edge_set = set()
    edges = []

    def add_edge(a, b):
        if a == b:
            return
        key = (a, b)
        if key in edge_set:
            return
        edge_set.add(key)
        edges.append({
            "from": a,
            "to": b,
            "capacitate": random.randint(1, 9),
        })

    for layer in range(layer_count - 1):
        src_nodes = layers[layer]
        target_pool = []
        for nxt in range(layer + 1, layer_count):
            target_pool.extend(layers[nxt])
        if not target_pool:
            continue
        for node_id in src_nodes:
            targets = random.sample(target_pool, k=random.randint(1, min(3, len(target_pool))))
            for t in targets:
                add_edge(node_id, t)

    extra_edges = random.randint(n, n * 2)
    all_nodes = [n["id"] for n in nodes]
    layer_of = {n["id"]: n["layer"] for n in nodes}
    for _ in range(extra_edges):
        a, b = random.sample(all_nodes, 2)
        if layer_of[a] < layer_of[b]:
            add_edge(a, b)

    return {
        "nodes": nodes,
        "edges": edges,
        "source": source,
        "sink": sink,
    }


def _ff_solve_payload(nodes, edges, source, sink):
    capacitati = {
        (e["from"], e["to"]): float(e.get("capacitate", 0))
        for e in edges
    }

    rezultat = algoritmul_ford_fulkerson(capacitati, source, sink)

    iteratii = []
    for it in rezultat.get("iteratii", []):
        drum = []
        for a, b, s in it.get("drum", []):
            drum.append([_coerce_int(a), _coerce_int(b), s])
        flux_dupa = it.get("valoare_flux_dupa", it.get("flux_curent", 0))
        iteratii.append({
            "iteratie": it.get("iteratie", 0),
            "drum": drum,
            "delta": it.get("delta", 0),
            "flux_dupa": flux_dupa,
            "stop": len(drum) == 0,
        })

    taietura_minima = []
    vulnerabilitati = []
    for xi, xj, cap, fl in rezultat.get("taietura", []):
        taietura_minima.append({
            "from": xi,
            "to": xj,
            "nod_from": xi,
            "nod_to": xj,
            "capacitate": cap,
            "flux": fl,
        })
        vulnerabilitati.append(f"Arc {xi} -> {xj}")

    return {
        "flux_maxim": rezultat.get("flux_maxim", 0),
        "cap_taietura": rezultat.get("cap_taietura", 0),
        "taietura_minima": taietura_minima,
        "vulnerabilitati_critice": vulnerabilitati,
        "iteratii": iteratii,
        "ISTOP": rezultat.get("ISTOP", 0),
        "logs": "Jurnal generat pe server.",
    }


def _hungarian_payload(matrice, experti, vulnerabilitati):
    rezultat = algoritmul_ungar(matrice_costuri=matrice, minimizare=True)

    iteratii = []
    for it in rezultat.get("iteratii", []):
        iteratii.append({
            "iteratie": it.get("iteratie", 0),
            "descriere": it.get("descriere", ""),
            "n0": it.get("n0", 0),
            "n": it.get("n", 0),
            "stop": it.get("STOP", False),
            "matrice_curenta": it.get("matrice", []),
            "linii_taiate": it.get("linii_marcate", []),
            "coloane_taiate": it.get("coloane_marcate", []),
            "zerouri_incadrate": it.get("incadrat", {}),
            "zerouri_barate": it.get("barate", []),
        })

    alocare = []
    for i, j in rezultat.get("cuplaj", []):
        if i < len(experti) and j < len(vulnerabilitati):
            cost = matrice[i][j]
            alocare.append({
                "expert": experti[i],
                "vuln": vulnerabilitati[j],
                "cost": cost,
            })

    return {
        "valoare": rezultat.get("valoare", 0),
        "alocare": alocare,
        "iteratii": iteratii,
        "cuplaj": rezultat.get("cuplaj", []),
    }


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/ff/generate", methods=["POST"])
def api_generate_ff():
    data = _generate_attack_network()
    data["status"] = "ok"
    return jsonify(data)


@app.route("/api/ff/solve", methods=["POST"])
def api_solve_ff():
    payload = request.json or {}
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    source = payload.get("source", 0)
    sink = payload.get("sink", 0)
    rezultat = _ff_solve_payload(nodes, edges, source, sink)
    return jsonify({"status": "ok", "data": rezultat})


@app.route("/api/optimal-patching", methods=["POST"])
def api_optimal_patching():
    payload = request.json or {}
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])
    source = payload.get("source", 0)
    sink = payload.get("sink", 0)
    rezultat = _ff_solve_payload(nodes, edges, source, sink)
    return jsonify({"status": "success", "min_cut_edges": rezultat.get("taietura_minima", []), "flow": rezultat.get("flux_maxim", 0), "logs": rezultat.get("logs", "")})


@app.route("/api/hun/solve", methods=["POST"])
def api_hun_solve():
    payload = request.json or {}
    matrice = payload.get("matrice", [])
    experti = payload.get("experti", [])
    vulnerabilitati = payload.get("vulnerabilitati", [])
    rezultat = _hungarian_payload(matrice, experti, vulnerabilitati)
    return jsonify({"status": "ok", "data": rezultat})


@app.route("/api/run-ford-fulkerson", methods=["POST"])
def api_run_ff_alias():
    return api_solve_ff()


@app.route("/api/run-hungarian", methods=["POST"])
def api_run_hungarian_alias():
    return api_hun_solve()


@app.route("/api/shutdown", methods=["POST"])
def api_shutdown():
    shutdown_fn = request.environ.get("werkzeug.server.shutdown")
    if shutdown_fn:
        shutdown_fn()
        return jsonify({"status": "ok"})

    def _force_exit():
        try:
            os._exit(0)
        except Exception:
            pass

    threading.Timer(0.4, _force_exit).start()
    return jsonify({"status": "ok", "mesaj": "Shutdown fortat."})


if __name__ == '__main__':
    app.run(debug=False, port=5000)

