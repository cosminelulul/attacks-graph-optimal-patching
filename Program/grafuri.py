"""
grafuri.py — Biblioteca Teoria Grafurilor
==========================================
Bazata pe suportul de curs:
  - Curs 10 Teoria Grafurilor (Generalitati) + Algoritmul Ford
  - Curs 11: Probleme de Afectare, Algoritmul Ungar (KUHN)
  - Seminar 10: Flux in Retele, Algoritmul Ford-Fulkerson
  - Seminar 11: Probleme de Afectare, Algoritmul Ungar
Toate functiile returneaza structuri de date (dict, list, tuple) si jurnale
de pasi compatibile cu afisarea prin interfata Tkinter.
Fara dependente externe — doar biblioteca standard Python.
"""

import math
import random
from collections import deque

import threading
import webbrowser

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


# ============================================================
# SECTIUNEA I — DEFINITII SI STRUCTURI DE DATE DE BAZA
# ============================================================

class Graf:
    """
    Definitia 1-2 (Curs 4):
      G = (X, U) unde X = multimea varfurilor, U = multimea arcelor.
    Suporta:
      - grafuri orientate (digraf)
      - grafuri neorientate (muchii)
      - capacitati / valori pe arce
    Reprezentare interna: lista de adiacenta (dict of dict).
    """

    def __init__(self, orientat: bool = True):
        """
        Parametri
        ---------
        orientat : True  => graf orientat (digraf)   — arcele (xi, xj) au sens
                   False => graf neorientat            — muchiile nu au sens
        """
        self.orientat = orientat
        # X — multimea varfurilor
        self.X: list = []
        # Gamma: xi -> {xj: valoare_arc}  (Definitia 1, Curs 4)
        self.Gamma: dict = {}

    # ----------------------------------------------------------
    # Constructie graf
    # ----------------------------------------------------------

    def adauga_varf(self, varf) -> None:
        """Adauga varful `varf` in multimea X daca nu exista deja."""
        if varf not in self.Gamma:
            self.X.append(varf)
            self.Gamma[varf] = {}

    def adauga_arc(self, xi, xj, valoare: float = 1.0) -> None:
        """
        Adauga arcul (xi, xj) cu capacitatea/valoarea data.
        Definitia 2 (Curs 4): perechea (xi, xj) ∈ U se numeste arc.
        Pentru grafuri neorientate se adauga ambele sensuri.
        """
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
        """
        Returneaza U = {(xi, xj, valoare)} — multimea arcelor grafului.
        Observatie 1.2 punctul 4 (Curs 4):
          U = {(x, y) | x ∈ X, y ∈ Gamma(x)}
        """
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
        """Returneaza valoarea / capacitatea arcului (xi, xj). INF daca nu exista."""
        return self.Gamma.get(xi, {}).get(xj, math.inf)

    def exista_arc(self, xi, xj) -> bool:
        """Verifica daca arcul (xi, xj) exista in graf."""
        return xj in self.Gamma.get(xi, {})

    # ----------------------------------------------------------
    # Proprietati de baza (Observatia 1.2, Curs 4)
    # ----------------------------------------------------------

    def ordin(self) -> int:
        """
        Definitia 1 (Curs 4): card(X) = |X| = n reprezinta ordinul grafului.
        """
        return len(self.X)

    def numar_arce(self) -> int:
        """Numarul total de arce |U|."""
        return len(self.multimea_arcelor())

    def gamma_plus(self, xi) -> dict:
        """
        Gamma+(xi) = {xj ∈ X | (xi, xj) ∈ U} — multimea succesorilor lui xi.
        Observatie 1.2 punctul 3 (Curs 4).
        """
        return dict(self.Gamma.get(xi, {}))

    def gamma_minus(self, xi) -> dict:
        """
        Gamma-(xi) = {xk ∈ X | (xk, xi) ∈ U} — multimea predecesorilor lui xi.
        """
        pred = {}
        for xk in self.X:
            if xi in self.Gamma.get(xk, {}):
                pred[xk] = self.Gamma[xk][xi]
        return pred

    def grad_exterior(self, xi) -> int:
        """d+(xi) = |Gamma+(xi)| — gradul exterior al varfului xi."""
        return len(self.Gamma.get(xi, {}))

    def grad_interior(self, xi) -> int:
        """d-(xi) = |Gamma-(xi)| — gradul interior al varfului xi."""
        return len(self.gamma_minus(xi))

    def grad(self, xi) -> int:
        """
        Pentru grafuri neorientate: d(xi) = numarul muchiilor incidente cu xi.
        Pentru grafuri orientate: d(xi) = d+(xi) + d-(xi).
        """
        if self.orientat:
            return self.grad_exterior(xi) + self.grad_interior(xi)
        return len(self.Gamma.get(xi, {}))

    def este_izolat(self, xi) -> bool:
        """Varful xi este izolat daca Gamma+(xi) = ∅ si Gamma-(xi) = ∅."""
        return self.grad_exterior(xi) == 0 and self.grad_interior(xi) == 0

    def varfuri_adiacente(self, xi) -> list:
        """Returneaza lista varfurilor adiacente cu xi."""
        vecini = set(self.Gamma.get(xi, {}).keys())
        if self.orientat:
            vecini |= set(self.gamma_minus(xi).keys())
        return list(vecini)

    # ----------------------------------------------------------
    # Clasificarea grafurilor (Observatia 1.3, Curs 4)
    # ----------------------------------------------------------

    def este_finit(self) -> bool:
        """Un graf este finit daca multimea X este finita (card(X) = n, n ∈ N*)."""
        return True  # implementarea suporta doar grafuri finite

    def are_bucle(self) -> bool:
        """Verifica daca graful are bucle (xi, xi) ∈ U."""
        return any(xi in self.Gamma.get(xi, {}) for xi in self.X)

    def este_simplu(self) -> bool:
        """Un graf simplu nu are bucle si nu are arce multiple."""
        return not self.are_bucle()

    def este_conex(self) -> bool:
        """
        Observatie (Seminar 10): G finit, conex daca pentru orice 2 varfuri x, y
        exista un lant care le uneste.
        Verificare prin BFS din primul varf.
        """
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
        """
        Definitie (Seminar 10): G = (X, U) finit, conex, fara bucle este
        graf-retea daca exista sursa xS cu Gamma-(xS) = ∅ si destinatie xt
        cu Gamma+(xt) = ∅.
        """
        if not self.orientat:
            return False
        if not self.este_conex():
            return False
        if self.are_bucle():
            return False
        sursa_ok = len(self.gamma_minus(sursa)) == 0
        dest_ok = len(self.Gamma.get(destinatie, {})) == 0
        return sursa_ok and dest_ok

    # ----------------------------------------------------------
    # Subgraf si Graf Partial (Definitiile 3-4, Curs 4)
    # ----------------------------------------------------------

    def subgraf(self, X_prim: list) -> "Graf":
        """
        Definitia 3 (Curs 4): G' = (X', Gamma') subgraf al lui G daca
        X' ⊂ X si Gamma'(x) = X' ∩ Gamma(x) pentru orice x ∈ X'.
        """
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
        """
        Definitia 4 (Curs 4): G' = (X, Gamma') graf partial al lui G daca
        multimea suport X este aceeasi si Gamma' ⊆ Gamma, pentru orice x ∈ X.
        `arce_selectate` — lista de tuple (xi, xj).
        """
        g = Graf(orientat=self.orientat)
        for v in self.X:
            g.adauga_varf(v)
        for arc in arce_selectate:
            xi, xj = arc[0], arc[1]
            if self.exista_arc(xi, xj):
                g.adauga_arc(xi, xj, self.valoare_arc(xi, xj))
        return g

    # ----------------------------------------------------------
    # Drumuri si lanturi (Definitia 5+, Curs 4)
    # ----------------------------------------------------------

    def este_drum(self, secventa: list) -> bool:
        """
        Un drum este o succesiune de arce {u1, u2, ..., uk} ale caror
        extremitati se potrivesc (Curs 4, Def. drum).
        `secventa` — lista de varfuri [x0, x1, ..., xk].
        """
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
        """
        Drum elementar: nu trece de 2 ori prin acelasi varf
        (xi ≠ xj, ∀i ≠ j, i,j = 1,...,k+1). Curs 4.
        """
        return self.este_drum_simplu(secventa) and len(secventa) == len(set(secventa))

    def este_circuit(self, secventa: list) -> bool:
        """
        Circuit: drum care pleaca si se termina in acelasi varf [x0...xk, x0].
        Curs 4.
        """
        return (len(secventa) > 1 and
                secventa[0] == secventa[-1] and
                self.este_drum_simplu(secventa))

    def valoare_drum(self, secventa: list) -> float:
        """
        Definitia valorii unui drum (Curs 4):
          f(µ) = suma valorilor arcelor care il compun.
        """
        if not self.este_drum(secventa):
            return math.inf
        return sum(self.valoare_arc(secventa[i], secventa[i + 1])
                   for i in range(len(secventa) - 1))

    def lungime_drum(self, secventa: list) -> int:
        """Lungimea drumului = numarul de arce (Curs 4)."""
        return len(secventa) - 1

    # ----------------------------------------------------------
    # Taietura (Seminar 10)
    # ----------------------------------------------------------

    def capacitate_taietura(self, A: set, sursa, destinatie) -> float:
        """
        Seminar 10: A ⊂ X, xS ∉ A, xt ∈ A reprezinta o taietura.
        Capacitatea taieturii:
          C(UA-) = suma c(u) pentru u ∈ UA-,
          UA- = {(xi, xj) | xi ∉ A, xj ∈ A}
        """
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


# ============================================================
# SECTIUNEA II — ALGORITMUL FORD (drumuri de valoare minima)
# ============================================================

def algoritmul_ford(graf: Graf, sursa) -> dict:
    """
    Algoritmul Ford (Curs 4, II.2) — drumuri de valoare minima intr-un graf
    cu pondere, incepand din varful sursa xS.

    Pasul 1 (Iteratia I0):
      lambda[i] = 0   daca i == S
      lambda[i] = INF daca i != S
      Se parcurge lista arcelor; daca lambda[j] - lambda[i] > f(xi, xj)
      atunci lambda[j] <- lambda[i] + f(xi, xj)  (si se marcheaza arcul).

    Iteratia Ik (k >= 1):
      Se repeta parcurgerea arcelor cu aceeasi regula de relaxare.

    Test de optimalitate (TO):
      Daca la o parcurgere completa nu s-a facut nicio modificare => STOP.
      Iteratia ISTOP reprezinta solutia.

    Parametri
    ---------
    graf   : Graf orientat cu valori pe arce (f(xi, xj) >= 0)
    sursa  : varful de start xS

    Returneaza
    ----------
    dict cu:
      "lambda"       : {varf: valoare_minima} — distantele minime de la sursa
      "predecesori"  : {varf: predecesorul pe drumul minim} (pentru reconstructia drumului)
      "iteratii"     : lista de dict-uri — jurnalul fiecarei iteratii (pentru UI)
      "arce_marcate" : lista arcelor marcate cu (*) la ISTOP (graful solutie)
      "ISTOP"        : numarul iteratiei de stop
    """
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
    """
    Determina drumul de valoare minima de la sursa la destinatie
    folosind Algoritmul Ford.

    Pasul 2 — Solutia problemei (Curs 4, Observatia 2.2):
      Drumul minim µ1 = [xS, xl1, xl2, ..., xDest] se reconstituie
      urmand predecesorii marcati cu (*) de la destinatie la sursa.

    Returneaza
    ----------
    dict cu:
      "drum"       : lista de varfuri de la sursa la destinatie
      "valoare"    : valoarea (lungimea ponderata) a drumului
      "ford"       : rezultatul complet al algoritmului Ford
      "mesaj"      : text descriptiv (pentru UI)
    """
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

    # Reconstructia drumului (Pasul 2 — graful solutie)
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


# ============================================================
# SECTIUNEA III — ALGORITMUL FORD-FULKERSON (flux maxim in retele)
# ============================================================

def algoritmul_ford_fulkerson(capacitati: dict, sursa, destinatie) -> dict:
    """
    Algoritmul Ford-Fulkerson (Seminar 10) — determinarea fluxului maxim
    intr-un graf-retea G = (X, U).

    Functia flux f: U -> R satisface:
      1. 0 <= f(u) <= c(u),  ∀u ∈ U  (conditia de capacitate)
      2. Σ f(xi,xk) = Σ f(xk,xj),  ∀k != S, t  (conservarea fluxului)
      3. V(f) = Σ f(xS,xi) = Σ f(xj,xt)  (valoarea fluxului)

    Procedura de etichetare (Pasul 2, Seminar 10):
      Arc nesaturat (xi -> xj, f < c) si xi etichetat => xj primeste [+xi]
      Arc cu flux > 0 (xj -> xi) si xj etichetat  => xi primeste [-xj]
        (doar daca xi nu poate fi etichetat altfel)

    Iteratii:
      I0   : se determina un flux initial f0 (lanturi de la S la t)
      Ik   : procedura de etichetare; se cauta drum de ameliorare;
             daca se atinge destinatia => crestem fluxul cu min rezidual;
             daca NU se atinge         => STOP (flux maxim atins).

    Parametri
    ---------
    capacitati : dict {(xi, xj): capacitate} — capacitatile arcelor
    sursa      : varful sursa xS
    destinatie : varful destinatie xt

    Returneaza
    ----------
    dict cu:
      "flux_maxim"  : valoarea fluxului maxim V(f)
      "flux"        : {(xi,xj): valoare_flux} — fluxul pe fiecare arc
      "iteratii"    : jurnalul tuturor iteratiilor (pentru UI)
      "taietura"    : multimea arcelor care formeaza taietura minima
      "cap_taietura": capacitatea taieturii minime (= flux maxim)
      "ISTOP"       : iteratia de stop
    """
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

    # ── Valoarea fluxului maxim ──
    flux_maxim = sum(flux.get((sursa, xj), 0)
                     for xj in varfuri if (sursa, xj) in capacitati)

    # ── Determinarea taieturii minime ──
    # A = multimea varfurilor accesibile din sursa in graful rezidual la ISTOP
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
    """
    Verifica conditiile de flux (Seminar 10):
      1. 0 <= f(u) <= c(u) pentru orice arc u
      2. Conservarea fluxului: Σ f(xk,xi) = Σ f(xi,xj) pentru xi != S, t
      3. V(f) = Σ f(xS,xi) = Σ f(xj,xt)

    Returneaza dict cu rezultatele verificarii (pentru UI).
    """
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


# ============================================================
# SECTIUNEA IV — GRAFUL BIPARTIT (pentru Algoritmul Ungar)
# ============================================================

class GrafBipartit:
    """
    Definitia 1-2 (Curs 6): G = (X ∪ Y, U) graf simplu bipartit finit.
    Conditii:
      i)  X, Y ≠ ∅
      ii) X ∪ Y = V
      iii)X ∩ Y = ∅
      Orice muchie (xi, yj) ∈ U are o extremitate in X si cealalta in Y.
    """

    def __init__(self, X: list, Y: list):
        if set(X) & set(Y):
            raise ValueError("X si Y trebuie sa fie disjuncte (X ∩ Y = ∅).")
        self.X = list(X)
        self.Y = list(Y)
        # U: {xi: {yj: valoare}} — doar muchii intre X si Y
        self.U: dict = {x: {} for x in X}

    def adauga_muchie(self, xi, yj, valoare: float = 1.0) -> None:
        """Adauga muchia (xi, yj) cu valoarea data."""
        if xi not in self.X:
            raise ValueError(f"{xi} nu apartine lui X.")
        if yj not in self.Y:
            raise ValueError(f"{yj} nu apartine lui Y.")
        self.U[xi][yj] = valoare

    def valoare_muchie(self, xi, yj) -> float:
        """Valoarea muchiei (xi, yj). INF daca nu exista cuplaj posibil."""
        return self.U.get(xi, {}).get(yj, math.inf)

    def multimea_muchiilor(self) -> list:
        """Returneaza U = [(xi, yj, val)] — multimea muchiilor."""
        return [(xi, yj, val)
                for xi in self.X
                for yj, val in self.U[xi].items()]

    def gamma(self, xi) -> list:
        """Gamma(xi) = {yj ∈ Y | (xi, yj) ∈ U} — vecinii lui xi in Y."""
        return list(self.U.get(xi, {}).keys())

    def este_cuplaj(self, W: list) -> bool:
        """
        Definitia 3 (Curs 6): W ⊆ U este cuplaj daca oricare doua muchii
        din W nu sunt adiacente (nu impart un varf comun).
        """
        x_folositi, y_folositi = set(), set()
        for (xi, yj) in W:
            if xi in x_folositi or yj in y_folositi:
                return False
            x_folositi.add(xi)
            y_folositi.add(yj)
        return True

    def valoare_cuplaj(self, W: list) -> float:
        """
        Definitia 6 (Curs 6): Valoarea unui cuplaj = suma valorilor
        muchiilor care il formeaza. V(W) = Σ c(xi,yj) pentru (xi,yj) ∈ W.
        """
        return sum(self.valoare_muchie(xi, yj) for (xi, yj) in W)

    def dimensiune_cuplaj(self, W: list) -> int:
        """Numarul de muchii din cuplaj."""
        return len(W)


# ============================================================
# SECTIUNEA V — ALGORITMUL UNGAR (KUHN)
# ============================================================

def algoritmul_ungar(matrice_costuri: list, minimizare: bool = True) -> dict:
    """
    Algoritmul Ungar (KUHN) — Curs 6 + Seminar 11.
    Determina cuplajul maximal de valoare optima (minima sau maxima)
    pentru o problema de afectare n x n.

    Etapele algoritmului:
    ─────────────────────
    Pasul 1 — Matricea costurilor (Seminar 11, Pasul 1):
      Se construieste matricea patrata C = (cij). Daca nu exista cuplaj
      intre xi si yj => cij = ∞.

    Pasul 2 — Crearea de zerouri (Seminar 11, Pasul 2):
      a) Se scade din fiecare linie minimul sau:
           ui = min_j(cij),  c^ij = cij - ui
      b) Daca exista coloane fara zero:
           vj = min_i(c^ij),  c~ij = c^ij - vj

    Pasul 3 — Procedura de etichetare {0, 0̄} (Seminar 11, Pasul 3):
      - Se cauta liniile cu cele mai putine zerouri;
      - Se incadreaza un zero [0] si se bareaza [0̄] celelalte zerouri
        de pe linia si coloana respectiva;
      - Se numara zerourile incadrate n[0].
      - Daca n[0] = n => STOP, solutia e cuplajul maximal.
      - Daca n[0] < n => continuam cu Pasul 4.

    Pasul 4 — Suportul minim — procedura de marcaj (Seminar 11, Pasul 4):
      (1) Marcam cu (*) liniile fara 0 incadrat;
      (2) Marcam cu (*) coloanele cu 0 barat pe linii marcate L(*);
      (3) Marcam cu (*) liniile cu 0 incadrat pe coloane marcate C(*);
      (4) Repetam (2)-(3) pana la STOP marcaj.
      S = {linii nemarcate} ∪ {coloane marcate}

    Pasul 5 — Deplasarea de zerouri (Seminar 11, Pasul 5):
      T1 = elemente netaiate \ {0}
      T2 = elemente taiate o singura data
      T3 = elemente taiate de doua ori
      ε = min(T1)
      T1 <- T1 - ε,  T3 <- T3 + ε,  T2 neschimbate
      Se reia de la Pasul 3.

    Pasul 6 — Valoarea cuplajului maxim (Seminar 11, Pasul 6):
      v(Wmax) = Σ ui + Σ vj + Σ εk * (n - n[0]k)

    Parametri
    ---------
    matrice_costuri : lista 2D (n x n) cu valorile cij
    minimizare      : True => min v(W),  False => max v(W)

    Returneaza
    ----------
    dict cu:
      "cuplaj"          : lista [(i, j)] — perechile din cuplajul maximal
      "valoare"         : v(Wmax) — valoarea optima a cuplajului
      "iteratii"        : jurnalul tuturor iteratiilor (pentru UI)
      "matrice_finala"  : matricea modificata la ISTOP
      "n"               : dimensiunea problemei
      "minimizare"      : tipul optimizarii
      "mesaj"           : text descriptiv (pentru UI)
      "verificare"      : valoarea calculata prin formula de verificare
    """
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

    # ── Pasul 1: Minimele pe linii (ui) ──
    u = []  # minimele pe linii
    for i in range(n):
        fin = [C[i][j] for j in range(n) if C[i][j] != INF]
        u.append(min(fin) if fin else 0)
        for j in range(n):
            if C[i][j] != INF:
                C[i][j] -= u[-1]

    # ── Pasul 2: Minimele pe coloane (vj) ──
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
        """
        Pasul 3 — Etichetare {0, 0̄}.
        Determina cuplajul MAXIM de zerouri folosind augmenting paths
        (algoritmul Hopcroft-Karp simplificat), apoi bareaza celelalte zerouri
        de pe liniile si coloanele cu zero incadrat.
        Returneaza (cuplaj_incadrat, zerouri_barate, n0).
        cuplaj_incadrat: {i: j} — zero incadrat pe linia i, coloana j
        zerouri_barate:  set of (i, j) — zerouri barate
        """
        # ── Gasim cuplajul maxim de zerouri prin augmenting paths ──
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
        """
        Pasul 4 — Suport minim.
        Returneaza (linii_marcate, coloane_marcate, suport_min).
        """
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
        """
        Pasul 5 — Deplasare zerouri (Seminar 11, Pasul 5).
        Definitii:
          Linii taiate   = L(fara *)  = linii NEMARCATE   = set(range(n)) - linii_marcate
          Coloane taiate = C(*)       = coloane MARCATE    = coloane_marcate
          T1 = elemente NETAIATE (nici linia nici coloana taiata), exclusiv 0
          T2 = elemente taiate O SINGURA data (ori linie ori coloana, nu ambele)
          T3 = elemente taiate DE DOUA ORI (linia SI coloana taiata)
        Formula: eps = min(T1); T1 <- T1 - eps; T3 <- T3 + eps; T2 neschimbat.
        """
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


# ============================================================
# SECTIUNEA VI — TEOREME SI PROPRIETATI STRUCTURALE
# ============================================================

def teorema_konig_hall(graf_bipartit: GrafBipartit) -> dict:
    """
    Teorema 1 (König-Hall, Curs 6):
      Se poate cupla X in Y <=> |Γ(A)| >= |A| pentru toate submultimile A ⊆ X.
    Verificare prin conditia Hall: pentru fiecare A ⊆ X, |N(A)| >= |A|.

    Returneaza dict cu rezultatul verificarii.
    """
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
    """
    Teorema 2 (König-Ore, Curs 6):
      µ(G) = |X| - max_{A ⊆ X} (|A| - |Γ(A)|)
    Numarul varfurilor unui suport minim.
    """
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
    """
    Teorema 3 (König-Egerváry, Curs 6):
      Intr-un graf simplu bipartit, numarul arcelor unui cuplaj maxim
      coincide cu numarul varfurilor unui suport minim.
    Verificare: |Wmax| = µ(G).
    """
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
    """
    Propozitia 1 (Curs 6):
      Solutia unei probleme de afectare nu se modifica daca la toate elementele
      unei linii sau coloane se aduna acelasi numar real α.
    Demonstreaza prin calculul valorii cuplajului inainte si dupa.
    """
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


# ============================================================
# SECTIUNEA VII — UTILITARE PENTRU UI (Tkinter-friendly)
# ============================================================

def matrice_la_text(matrice: list, zerouri_incadrate: dict = None,
                    zerouri_barate: set = None, latime_col: int = 6) -> list:
    """
    Converteste o matrice 2D intr-o lista de siruri formatate
    (compatibil cu Text widget Tkinter).
    zerouri_incadrate: {i: j} — pozitiile zerourilor incadrate [0]
    zerouri_barate:    {(i,j)} — pozitiile zerourilor barate [0̄]
    Returneaza lista de siruri (cate una per rand).
    """
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
    """
    Afiseaza fluxul pe arce in format: (xi, xj): f / c
    Returneaza lista de siruri (pentru UI).
    """
    linii = []
    for (xi, xj), cap in sorted(capacitati.items(), key=lambda x: str(x)):
        f_val = flux.get((xi, xj), 0)
        linii.append(f"  ({xi}, {xj}): {int(f_val)} / {int(cap)}")
    return linii


def iteratii_ford_la_text(iteratii: list) -> list:
    """
    Formateaza jurnalul iteratiilor Algoritmului Ford pentru afisare in UI.
    """
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
    """
    Formateaza jurnalul iteratiilor Ford-Fulkerson pentru afisare in UI.
    """
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
    """
    Formateaza jurnalul iteratiilor Algoritmului Ungar pentru afisare in UI.
    """
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
    """
    Afiseaza cuplajul in format tabelar cu valori (pentru UI).
    etichetare_x / etichetare_y: liste de etichete pentru linii / coloane.
    """
    linii = ["Cuplaj maximal:"]
    for (i, j) in cuplaj:
        xi = etichetare_x[i] if etichetare_x else f"x{i + 1}"
        yj = etichetare_y[j] if etichetare_y else f"y{j + 1}"
        cij = matrice_costuri[i][j]
        linii.append(f"  ({xi}, {yj})  c = {cij}")
    valoare = sum(matrice_costuri[i][j] for (i, j) in cuplaj)
    linii.append(f"\n  Valoare totala: v(Wmax) = {valoare}")
    return linii


# ============================================================
# SECTIUNEA VIII — FUNCTII AUXILIARE DE CONSTRUCTIE RAPIDA
# ============================================================

def graf_din_lista_arce(arce: list, orientat: bool = True) -> Graf:
    """
    Construieste un Graf din lista de tuple (xi, xj) sau (xi, xj, valoare).
    """
    g = Graf(orientat=orientat)
    for arc in arce:
        if len(arc) == 2:
            g.adauga_arc(arc[0], arc[1])
        else:
            g.adauga_arc(arc[0], arc[1], arc[2])
    return g


def graf_din_matrice_adiacenta(matrice: list, varfuri: list = None,
                                orientat: bool = True) -> Graf:
    """
    Construieste un Graf din matricea de adiacenta.
    0 / None => nu exista arc; orice alta valoare => capacitatea arcului.
    """
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
    """
    Construieste dict {(xi, xj): capacitate} din lista de tuple
    (xi, xj, capacitate) — format cerut de algoritmul_ford_fulkerson.
    """
    return {(xi, xj): float(cap) for xi, xj, cap in arce_cap}


def matrice_costurilor_din_dict(n: int, costuri: dict,
                                 valoare_lipsa: float = math.inf) -> list:
    """
    Construieste matricea n x n din dict {(i, j): cost}.
    Indicii i, j sunt 0-based.
    """
    C = [[valoare_lipsa] * n for _ in range(n)]
    for (i, j), cost in costuri.items():
        C[i][j] = float(cost)
    return C


# ============================================================
# SECTIUNEA IX — API REST (Flask)
# ============================================================

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

