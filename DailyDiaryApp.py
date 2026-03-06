#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [re.sub(r"\s+", " ", str(c).strip()) for c in df.columns]
    return df


def find_col(cols, pattern_list) -> str:
    for pat in pattern_list:
        for c in cols:
            if re.search(pat, str(c), flags=re.IGNORECASE):
                return c
    raise KeyError(f"Column not found by patterns: {pattern_list}")


def dur_to_seconds(x) -> int:
    if pd.isna(x):
        return 0
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return 0

    if ":" in s:
        try:
            return int(pd.to_timedelta(s).total_seconds())
        except Exception:
            return 0

    if "." in s:
        try:
            m, sec = s.split(".", 1)
            return int(m) * 60 + int(sec)
        except Exception:
            return 0

    try:
        val = float(s)
        return int(round(val * 60))
    except Exception:
        return 0


def sec_to_mmss(x) -> str:
    try:
        total = int(x)
    except Exception:
        return ""
    m = total // 60
    s = total % 60
    return f"{m:02d}:{s:02d}"


def norm_name(x: str) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s\-]", "", s)
    return s


def sex_to_code(x) -> float:
    if pd.isna(x):
        return np.nan
    s = str(x).strip().lower()

    if s in {"m", "male", "masculino", "boy", "menino", "0"}:
        return 0
    if s in {"f", "female", "feminino", "girl", "menina", "1"}:
        return 1

    if "masc" in s or "menino" in s or "boy" in s:
        return 0
    if "fem" in s or "menina" in s or "girl" in s:
        return 1

    return np.nan


def age_months(on_date, dob) -> float:
    if pd.isna(on_date) or pd.isna(dob):
        return np.nan
    try:
        on = pd.to_datetime(on_date)
        bd = pd.to_datetime(dob)
    except Exception:
        return np.nan
    if pd.isna(on) or pd.isna(bd) or on < bd:
        return np.nan

    months = (on.year - bd.year) * 12 + (on.month - bd.month)
    if on.day < bd.day:
        months -= 1
    return float(months)


def build_base_daily_from_detailed(detailed_df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(detailed_df)

    date_col = find_col(df.columns, [r"^date$"])
    actor_col = find_col(df.columns, [r"^actor\b"])
    recv_col = find_col(df.columns, [r"^receiver\b"])
    beh_col = find_col(df.columns, [r"target behaviours"])
    contact_col = find_col(df.columns, [r"contact play"])
    obj_col = find_col(df.columns, [r"play with object"])
    ptype_col = find_col(df.columns, [r"PF\s*="])
    dyad_col = find_col(df.columns, [r"^dyad\b"])
    dur_col = find_col(df.columns, [r"Duration"])

    for c in [date_col, actor_col, recv_col, beh_col, contact_col, obj_col, ptype_col, dyad_col, dur_col]:
        df[c] = df[c].astype(str).str.strip()

    df["date_clean"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    df["dur_sec"] = df[dur_col].apply(dur_to_seconds)

    df["beh"] = df[beh_col].str.lower().str.strip()
    df["contact"] = df[contact_col].str.upper().str.strip()
    df["obj"] = df[obj_col].str.upper().str.strip()
    df["ptype"] = df[ptype_col].str.upper().str.strip()

    dy = df[
        (df[recv_col].notna()) &
        (df[recv_col] != "*") &
        (df[recv_col].str.lower() != "nan")
    ].copy()

    group_cols = ["date_clean", actor_col, recv_col, dyad_col]

    def dyad_summary(g: pd.DataFrame) -> pd.Series:
        dur_sec = int(g["dur_sec"].sum())
        return pd.Series({
            "daily observation minutes of actor (from scan)": dur_sec,
            "daily observation minutes of receiver (from scan)": dur_sec,
            "daily observation minutes for dyad (from scan)": dur_sec,

            "total number of daily aggression of the dyad": int((g["beh"] == "ag").sum()),
            "total number of daily social play interaction of the dyad": int((g["beh"] == "socpl").sum()),
            "total number of social play with body contact of the dyad": int(((g["beh"] == "socpl") & (g["contact"] == "C")).sum()),
            "total number of social play without body contact of the dyad": int(((g["beh"] == "socpl") & (g["contact"] == "NC")).sum()),
            "total number of social play with object of the dyad": int(((g["beh"] == "socpl") & (g["obj"] == "OB")).sum()),
            "total number of social play without object of the dyad": int(((g["beh"] == "socpl") & (g["obj"] == "NOB")).sum()),
            "total number of play fighting  of the dyad": int((g["ptype"] == "PF").sum()),
            "total number of locomotor/acrobatic play  of the dyad": int((g["ptype"] == "L").sum()),
            "total number of tickle of the dyad": int((g["ptype"] == "TK").sum()),
            "total number of other of the dyad": int((g["ptype"] == "O").sum()),
            "total number of body contact interactions of dyad": int((g["beh"] == "bc").sum()),
            "total number of food sharing of dyad": int((g["beh"] == "fs").sum()),
            "total number of other affiliation of dyad": int(g["beh"].isin(["aff", "caress"]).sum()),

            "total number of daily solitary play of child": 0,
            "total number of solitary play with object": 0,
            "total number of solitary play without object": 0,
        })

    dyad_df = (
        dy.groupby(group_cols, dropna=False).apply(dyad_summary).reset_index()
        if len(dy) > 0 else pd.DataFrame(columns=group_cols)
    )

    dyad_df = dyad_df.rename(columns={
        "date_clean": "date",
        actor_col: "actor",
        recv_col: "receiver",
        dyad_col: "dyad (AB is different from BA)",
    })

    all_actors = df[["date_clean", actor_col]].dropna().drop_duplicates()
    all_actors = all_actors.rename(columns={"date_clean": "date", actor_col: "actor"})

    sol = df[df["beh"] == "solpl"].copy()
    sol_group = sol.groupby(["date_clean", actor_col], dropna=False)

    sol_total = sol_group.size().rename("total number of daily solitary play of child")
    sol_ob = (
        sol[sol["obj"] == "OB"]
        .groupby(["date_clean", actor_col], dropna=False)
        .size()
        .rename("total number of solitary play with object")
    )
    sol_nob = (
        sol[sol["obj"] == "NOB"]
        .groupby(["date_clean", actor_col], dropna=False)
        .size()
        .rename("total number of solitary play without object")
    )
    sol_dur = sol_group["dur_sec"].sum().rename("sol_dur_sec")

    sol_stats = pd.concat([sol_total, sol_ob, sol_nob, sol_dur], axis=1).reset_index().fillna(0)
    sol_stats = sol_stats.rename(columns={"date_clean": "date", actor_col: "actor"})
    sol_rows = all_actors.merge(sol_stats, on=["date", "actor"], how="left").fillna(0)

    sol_rows["daily observation minutes of actor (from scan)"] = sol_rows["sol_dur_sec"].astype(int)
    sol_rows["daily observation minutes of receiver (from scan)"] = 0
    sol_rows["daily observation minutes for dyad (from scan)"] = 0

    sol_rows["receiver"] = pd.NA
    sol_rows["dyad (AB is different from BA)"] = pd.NA

    for c in [
        "total number of daily aggression of the dyad",
        "total number of daily social play interaction of the dyad",
        "total number of social play with body contact of the dyad",
        "total number of social play without body contact of the dyad",
        "total number of social play with object of the dyad",
        "total number of social play without object of the dyad",
        "total number of play fighting  of the dyad",
        "total number of locomotor/acrobatic play  of the dyad",
        "total number of tickle of the dyad",
        "total number of other of the dyad",
        "total number of body contact interactions of dyad",
        "total number of food sharing of dyad",
        "total number of other affiliation of dyad",
    ]:
        sol_rows[c] = 0

    base = pd.concat([dyad_df, sol_rows], ignore_index=True)

    for c in [
        "daily observation minutes of actor (from scan)",
        "daily observation minutes of receiver (from scan)",
        "daily observation minutes for dyad (from scan)",
    ]:
        base[c] = base[c].apply(sec_to_mmss)

    base["date"] = pd.to_datetime(base["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return base


def enrich_with_meta(daily: pd.DataFrame, meta_df: pd.DataFrame, country_value: str, group_value: str) -> pd.DataFrame:
    meta = normalize_columns(meta_df)

    name_col = find_col(meta.columns, [r"^name$", r"child\s*name", r"participant", r"subject", r"^nome$", r"\bnome\b"])
    sex_col = find_col(meta.columns, [r"sex", r"gender", r"^sexo$", r"\bsexo\b", r"genero", r"gênero"])
    dob_col = find_col(meta.columns, [r"dob", r"birth", r"date\s*of\s*birth", r"data\s*de\s*nascimento", r"nascimento"])

    meta = meta.copy()
    meta["_key"] = meta[name_col].apply(norm_name)
    meta["_sex"] = meta[sex_col].apply(sex_to_code)
    meta["_dob"] = pd.to_datetime(meta[dob_col], errors="coerce", dayfirst=True)

    meta = meta.sort_values(by=["_key"]).drop_duplicates(subset=["_key"], keep="first")

    sex_map = dict(zip(meta["_key"], meta["_sex"]))
    dob_map = dict(zip(meta["_key"], meta["_dob"]))

    out = daily.copy()
    out["country"] = country_value
    out["group"] = group_value

    out["_actor_key"] = out["actor"].apply(norm_name)
    out["_receiver_key"] = out["receiver"].apply(norm_name)

    out["actor sex (male=0, female=1)"] = out["_actor_key"].map(sex_map)
    out["receiver sex (male=0, female=1)"] = out["_receiver_key"].map(sex_map)

    out["actor age (months)"] = [
        age_months(d, dob_map.get(k, np.nan))
        for d, k in zip(out["date"], out["_actor_key"])
    ]

    out["receiver age (months)"] = [
        age_months(d, dob_map.get(k, np.nan))
        for d, k in zip(out["date"], out["_receiver_key"])
    ]

    out.drop(columns=["_actor_key", "_receiver_key"], inplace=True, errors="ignore")
    return out


def generate_output(detailed_path: str, meta_path: str, save_path: str, country_value: str, group_value: str) -> None:
    detailed_df = pd.read_excel(detailed_path, dtype=str)
    meta_df = pd.read_excel(meta_path, dtype=str)

    base = build_base_daily_from_detailed(detailed_df)
    final = enrich_with_meta(base, meta_df, country_value=country_value, group_value=group_value)

    expected_cols = [
        "date",
        "actor",
        "receiver",
        "dyad (AB is different from BA)",
        "actor sex (male=0, female=1)",
        "receiver sex (male=0, female=1)",
        "actor age (months)",
        "receiver age (months)",
        "kinship (no kin=0, siblings =1, other kinship relation (cousins) = 2) if you do not have data NA (not applicable)",
        "daily observation minutes of actor (from scan)",
        "daily observation minutes of receiver (from scan)",
        "daily observation minutes for dyad (from scan)",
        "total number of daily aggression of the dyad",
        "total number of daily social play interaction of the dyad",
        "total number of social play with body contact of the dyad",
        "total number of social play without body contact of the dyad",
        "total number of social play with object of the dyad",
        "total number of social play without object of the dyad",
        "total number of play fighting  of the dyad",
        "total number of locomotor/acrobatic play  of the dyad",
        "total number of tickle of the dyad",
        "total number of other of the dyad",
        "total number of daily solitary play of child",
        "total number of solitary play with object",
        "total number of solitary play without object",
        "total number of body contact interactions of dyad",
        "total number of food sharing of dyad",
        "total number of other affiliation of dyad",
        "country",
        "group",
    ]

    for c in expected_cols:
        if c not in final.columns:
            final[c] = pd.NA

    final = final[expected_cols]
    final.to_excel(save_path, index=False)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Daily Diary Generator")
        self.geometry("900x360")
        self.resizable(False, False)

        self.detailed_path = tk.StringVar()
        self.meta_path = tk.StringVar()
        self.country_value = tk.StringVar()
        self.group_value = tk.StringVar()
        self.save_path = tk.StringVar(value="daily_diary.xlsx")

        self.build_ui()

    def build_ui(self):
        pad = {"padx": 10, "pady": 8}

        tk.Label(self, text="1) Select detailed_diary.xlsx:").grid(row=0, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.detailed_path, width=78).grid(row=0, column=1, **pad)
        tk.Button(self, text="Browse...", command=self.pick_detailed).grid(row=0, column=2, **pad)

        tk.Label(self, text="2) Select metadata file (e.g., Papoilas.xlsx):").grid(row=1, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.meta_path, width=78).grid(row=1, column=1, **pad)
        tk.Button(self, text="Browse...", command=self.pick_meta).grid(row=1, column=2, **pad)

        tk.Label(self, text="3) Country:").grid(row=2, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.country_value, width=30).grid(row=2, column=1, sticky="w", **pad)

        tk.Label(self, text="4) Group:").grid(row=3, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.group_value, width=30).grid(row=3, column=1, sticky="w", **pad)

        tk.Label(self, text="5) Save output as:").grid(row=4, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.save_path, width=78).grid(row=4, column=1, **pad)
        tk.Button(self, text="Save As...", command=self.pick_save).grid(row=4, column=2, **pad)

        tk.Button(self, text="Generate daily_diary.xlsx", command=self.run, width=32, height=2).grid(row=5, column=1, **pad)

        self.status = tk.Label(self, text="", fg="blue")
        self.status.grid(row=6, column=0, columnspan=3, sticky="w", **pad)

    def pick_detailed(self):
        p = filedialog.askopenfilename(
            title="Select detailed_diary.xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if p:
            self.detailed_path.set(p)

    def pick_meta(self):
        p = filedialog.askopenfilename(
            title="Select metadata file",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if p:
            self.meta_path.set(p)

    def pick_save(self):
        p = filedialog.asksaveasfilename(
            title="Save daily_diary.xlsx",
            defaultextension=".xlsx",
            initialfile="daily_diary.xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if p:
            self.save_path.set(p)

    def run(self):
        det = self.detailed_path.get().strip()
        meta = self.meta_path.get().strip()
        country = self.country_value.get().strip()
        group = self.group_value.get().strip()
        out = self.save_path.get().strip()

        if not det or not Path(det).exists():
            messagebox.showerror("Error", "Please select a valid detailed_diary.xlsx file.")
            return

        if not meta or not Path(meta).exists():
            messagebox.showerror("Error", "Please select a valid metadata file.")
            return

        if not country:
            messagebox.showerror("Error", "Please enter Country.")
            return

        if not group:
            messagebox.showerror("Error", "Please enter Group.")
            return

        if not out:
            messagebox.showerror("Error", "Please choose an output filename.")
            return

        try:
            self.status.config(text="Processing... please wait.")
            self.update_idletasks()

            generate_output(
                detailed_path=det,
                meta_path=meta,
                save_path=out,
                country_value=country,
                group_value=group
            )

            self.status.config(text=f"Done! Output saved to: {out}")
            messagebox.showinfo("Success", f"daily_diary generated successfully.\n\nSaved to:\n{out}")

        except Exception as e:
            self.status.config(text="")
            messagebox.showerror("Error", f"Failed:\n{e}")


if __name__ == "__main__":
    App().mainloop()