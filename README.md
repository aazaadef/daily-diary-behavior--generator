# Daily Diary Behavior Generator

A Tkinter-based desktop application for generating a structured `daily_diary.xlsx` dataset from:

- a detailed behavioral observation Excel file
- a participant metadata Excel file
- a user-provided country value
- a user-provided group value

The application summarizes dyadic interactions and solitary play, calculates observation durations, and enriches the output with participant sex and age in months.

---

## Features

- Desktop GUI built with Tkinter
- Accepts two Excel input files
- Generates `daily_diary.xlsx`
- Computes:
  - dyadic interaction summaries
  - solitary play summaries
  - actor/receiver sex
  - actor/receiver age in months
- Adds:
  - `country`
  - `group`
- Works with flexible column order
- Supports multiple duration formats

---

## Required Inputs

The application requires:

1. **Detailed observation file**  
   Excel file containing behavioral observation records

2. **Metadata file**  
   Excel file containing participant name, sex, and date of birth

3. **Country**  
   Entered manually by the user in the application

4. **Group**  
   Entered manually by the user in the application

---

## Input File 1: Detailed Observation File

The following columns must exist in the detailed observation file:

- `date`
- `actor`
- `receiver`
- `target behaviours`
- `contact play`
- `play with object`
- `play type`
- `dyad`
- `Duration`

### Notes
- Column order does **not** matter
- Column names must be recognizable
- Solitary play rows should use:
  - `receiver = *`
  - `target behaviour = solpl`

---

## Input File 2: Metadata File

The metadata file must include:

- participant name
- sex
- date of birth

### Accepted metadata column types

**Name**
- Name
- Nome
- Child Name
- Participant

**Sex**
- Sex
- Gender
- Sexo

**Date of birth**
- DOB
- Birth date
- Date of birth
- Data de nascimento

---

## Duration Format

The application supports these duration formats:

- `16.20` → minutes.seconds
- `16:20` → minutes:seconds
- `0:05:40` → hours:minutes:seconds

---

## Name Matching

Names should match between the detailed file and metadata file.

### Good example
- `Maria Alice` ↔ `Maria Alice`

### Problematic example
- `Victoria` vs `Viktoria`
- `MariaAlice` vs `Maria Alice`

---

## Output

The program generates:

```text
daily_diary.xlsx