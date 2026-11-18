<!-- AI AGENT INSTRUCTIONS -->
<!--
1. This template produces TWO files in the user's submission folder:
   - PART A  -> <submission_folder>/hackathon_rules.md   (injected into every judge prompt as "OFFICIAL JUDGING GUIDE")
   - PART B  -> <submission_folder>/challenge_brief.md   (injected into every judge prompt as "CHALLENGE BRIEF")
2. Fill each section ONLY from the official hackathon pages (rules, judging, prizes, track/challenge page) that the
   user gives you. Copy official wording verbatim where possible and keep the source URL + capture date at the top.
3. If a section does not exist in the official rules, write "Not specified by the organizers." Never invent rules,
   limits, prizes or deadlines.
4. Keep the numbers consistent with hackathon_settings.json (slide limit, video limit, language, required keywords,
   criteria names, award names). The criteria names here must match `criteria[].name` exactly.
5. Delete these instruction comments and the "PART A / PART B" separators in the final files.
6. Write in English unless the hackathon itself is run in another language.
-->

<!-- ===================== PART A -> hackathon_rules.md ===================== -->

# <Hackathon name> — Judging & Rules Guide
Source: <official rules URL> (and <judging / prizes URL>)
Captured: <YYYY-MM-DD>

## ELIGIBILITY — minimum requirements
- <Team size rules>
- <Required submission fields / platform (Devpost, ETHGlobal, custom portal...)>
- <Demo requirement: slide limit and/or video length limit, or "no demo required">
- <Language requirement>
- <Deadline with time zone>
- <Originality, licensing, references and AI-usage disclosure rules>
- <Sponsor / track technology that must be used, if any>

## JUDGING CRITERIA
<!-- One "###" block per criterion, same names and order as hackathon_settings.json "criteria". -->

### <Criterion 1 name>
<Official description of the criterion.>
Score of 5 (<official top-score label, if any>): <What an outstanding project looks like for this criterion.>

### <Criterion 2 name>
<Official description of the criterion.>
Score of 5: <What an outstanding project looks like for this criterion.>

<!-- Add or remove criterion blocks: K criteria = total score out of 5K. -->

## JUDGING PHASES
- <Phase 1: e.g. online triage by track judges (dates)>
- <Phase 2: e.g. finalist live pitches>
- <Phase 3: e.g. sponsor / grand prize deliberation>

## OFFICIAL PRIZES / AWARDS
<!-- Same names as hackathon_settings.json "awards". Write "No official award list." if none. -->
- <Award 1 name>: <official description>
- <Award 2 name>: <official description>

<!-- ===================== PART B -> challenge_brief.md ===================== -->

# <Challenge / track name> (<Hackathon name>)
Source: <official challenge or track URL>
Captured: <YYYY-MM-DD>

<One-paragraph official summary of the challenge or track.>

## BACKGROUND
<Official background / context, verbatim where possible.>

## OBJECTIVES
<What teams are asked to build or demonstrate.>

## POTENTIAL CONSIDERATIONS
<Hints, constraints, evaluation notes published by the organizers or the sponsor.>

## REQUIRED / SUGGESTED RESOURCES
- <Official datasets, APIs, SDKs or sponsor technologies (with URLs)>
