# AI-Transcript-Scoring-Tool
AI Transcript Scoring Tool
This is a single-file Python application built with Flask that implements a data-driven rubric to evaluate a self-introduction transcript. It combines rule-based methods, natural language processing (NLP) for metrics like Vocabulary Richness (TTR), and custom scoring buckets defined by the rubric to produce a final score (0–100) and detailed, per-criterion feedback.
Setup and Running
Please refer to the accompanying deployment_guide.md for detailed installation and execution steps.
Scoring Logic and Formulas
The tool calculates a total score out of 100 points, broken down across four main criteria.
1. Content & Structure (Total Weight: 40 points)
This criterion uses simple rule-based checks and keyword matching.


Metric	Formula / Rule	Score Calculation
Salutation Level (5 pts)	Checks if the transcript starts with a clear greeting (e.g., "Hello," "Good Morning").	5 points if present; 0 points otherwise.
Key Word Presence (30 pts)	Checks for the presence of 8 required self-introduction topics: name, age, class, school, family, hobbies, goals, unique point.	Score = 30 points * (Keywords Found / 8)
Flow (5 pts)	Simplistic check: presence of a Salutation and a clear Closing phrase at the end.	5 points if both are present; 0 points otherwise.




2. Speech Rate (Total Weight: 10 points)
This metric requires the user to input the speech duration in seconds.
Metric	Formula	Rubric Range	Score
Speech Rate (WPM)	$\text{WPM} = (\text{Word Count} / \text{Duration in Seconds}) \times 60$	$111 - 140 \text{ WPM}$ (Ideal)	10
		$> 140 \text{ WPM}$ or $81 - 110 \text{ WPM}$	6
		$< 80 \text{ WPM}$ (Too Slow)	2
3. Language & Grammar (Total Weight: 20 points)Grammar Errors (10 points)Note on Implementation: In a full production environment, this would require external tools like LanguageTool. For this single-file script, the calculation logic is based on a mock error count to demonstrate the formula's application.
Metric	Formula	Rubric Range	Score
Grammar Score	$\text{Score} = 1 - \min(\frac{\text{Errors per } 100 \text{ words}}{10}, 1)$	$> 0.9$ (Ideal)	10
		$0.7 - 0.89$	8
		$0.5 - 0.69$	6
		$0.3 - 0.49$	4
		$< 0.3$	2

Vocabulary Richness (10 points)
The tool uses Type-Token Ratio (TTR) as the measure of lexical diversity.
Metric	Formula	Rubric Range	Score
Vocabulary Richness (TTR)	$\text{TTR} = \text{Distinct Words} / \text{Total Words}$	$0.9 - 1.0$ (Ideal)	10
		$0.7 - 0.89$	8
		$0.5 - 0.69$	6
		$0.3 - 0.49$	4
		$0 - 0.29$	2
4. Clarity (Total Weight: 30 points)
This score heavily weights the rate of filler words detected by simple keyword search.
Metric	Formula	Rubric Range	Score
Filler Word Rate	$\text{Rate} = (\text{Filler Words Count} / \text{Total Words}) \times 100$	$< 1.0\%$ (Ideal)	30
		$1.0\% - 1.9\%$	25
		$2.0\% - 2.9\%$	20
		$3.0\% - 3.9\%$	15
		$4.0\% - 4.9\%$	10
		$> 5.0\%$ (Too High)	5
Filler Word List Used: um, uh, like, you know, so, actually, basically, right, i mean, well, kinda, sort of, okay, hmm, ah

