# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **online exam practice platform for the Taiwan Medical Laboratory Technician (醫檢師) national licensing exam**. The platform serves three user roles: students (學生端), teachers (老師端), and admins (管理員端). The full specification lives in `Notes.txt`.

## System Architecture

Three permission tiers with distinct capabilities:

- **Student**: Practice exams, AI feedback, personal records
- **Teacher**: Class management via invite code, student progress monitoring
- **Admin**: Full access — user management, data monitoring, question bank updates

## Subjects Covered

Six exam subjects (extensible):
1. 臨床生理學與病理學
2. 臨床血液學與血庫學
3. 醫學分子檢驗學與臨床鏡檢學
4. 微生物學與臨床微生物學
5. 生物化學與臨床生化學
6. 臨床血清免疫學與臨床病毒學

Two exam sittings per year → 12 past exam papers per year.

## Core Feature Requirements

### Authentication
- Google OAuth login/registration

### Exam Mode Settings
- Question counts: 5, 10, or full 80 (national exam standard per subject)
- Draw logic: single full paper, single random, multi-paper random, randomized answer options
- AI-based difficulty grading (easy / medium / hard)
- Timer modes: untimed or timed (per-question time + total remaining)

### Exam UI (One Question Per Screen)
- Question source label (e.g., 113年第一次臨床生理第3題)
- Elimination feature (strikethrough) on answer options
- Progress bar (e.g., 20/80)
- Prev / Next / Early Submit navigation
- Optional AI hint button (toggled before exam starts)
- Post-exam or real-time answer reveal with AI/web explanations
- PDF export of exam paper and answer record

### AI Features
- Weakness detection from answer history
- Adaptive practice (increase frequency of weak topic types)
- Growth tracking (compare historical performance, suggest study strategies)
- Time efficiency analysis (expected vs actual time per question)
- AI-generated simulated exam paper (stretch goal)

### Data Persistence
- Per-session: answer records, explanations, AI analysis report, exam date
- All stored in user profile
- Toggle whether a session is saved to history

## Platform Target
- Desktop web + mobile web (HTML) or App
- Mobile usage expected for practice; desktop for actual exam simulation
