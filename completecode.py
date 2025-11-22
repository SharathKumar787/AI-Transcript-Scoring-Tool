import json
import re
from flask import Flask, request, jsonify, render_template_string
from nltk.tokenize import word_tokenize
from nltk.text import Text
def safe_word_tokenize(text):
    """Tokenizes text using regex as a fallback if NLTK context is missing."""
    try:
        return word_tokenize(text)
    except Exception:
        return re.findall(r'\b\w+\b', text.lower())
RUBRIC = {
    "Content & Structure": {
        "Weightage": 40,
        "Metrics": {
            "Salutation Level": {
                "Weightage": 5,
                "Rules": [
                    {"Description": "Score if a clear salutation is present (e.g., 'Hello everyone', 'Good morning').", "PassScore": 5, "Threshold": 1} # 1 = yes
                ]
            },
            "Key word Presence": {
                "Weightage": 30,
                "Keywords": ["name", "age", "class", "school", "family", "hobbies", "goals", "unique point"],
                "Rules": [
                    # Score is calculated based on the number of keywords found (max 30 points)
                    {"Description": "Points scaled by keywords found (out of 8 defined keywords).", "MaxScore": 30}
                ]
            },
            "Flow": {
                "Weightage": 5,
                "Rules": [
                    {"Description": "Score if the introduction follows a logical order (Salutation -> Details -> Closing).", "PassScore": 5, "Threshold": 1} # 1 = yes
                ]
            }
        }
    },
    "Speech Rate": {
        "Weightage": 10,
        "Metrics": {
            "Speech rate (WPM)": {
                "Weightage": 10,
                "ScoringBuckets": [
                    {"Range": "111 - 140 WPM", "Score": 10, "Feedback": "Excellent pace! Very comfortable for listening."},
                    {"Range": "> 140 WPM", "Score": 6, "Feedback": "A bit too fast. Try to slow down for better clarity."},
                    {"Range": "81 - 110 WPM", "Score": 6, "Feedback": "A bit slow. Speed up slightly to keep listeners engaged."},
                    {"Range": "< 80 WPM", "Score": 2, "Feedback": "Too slow. The pace significantly impacts engagement."}
                ]
            }
        }
    },
    "Language & Grammar": {
        "Weightage": 20, # Combined weight for the two metrics
        "Metrics": {
            "Grammar errors (Score)": {
                "Weightage": 10,
                "ScoringBuckets": [
                    {"Range": "> 0.9", "Score": 10, "Feedback": "Impeccable grammar. Very high quality language use."},
                    {"Range": "0.7 to 0.89", "Score": 8, "Feedback": "Good grammar, only minor, non-distracting errors."},
                    {"Range": "0.5 to 0.69", "Score": 6, "Feedback": "Average grammar, with a few noticeable errors."},
                    {"Range": "0.3 to 0.49", "Score": 4, "Feedback": "Needs significant improvement in grammar and sentence structure."},
                    {"Range": "< 0.3", "Score": 2, "Feedback": "Severe grammar issues that compromise clarity."}
                ]
            },
            "Vocabulary richness (TTR)": {
                "Weightage": 10,
                "ScoringBuckets": [
                    {"Range": "0.9–1.0", "Score": 10, "Feedback": "Excellent vocabulary richness (TTR). Diverse and engaging word choices."},
                    {"Range": "0.7–0.89", "Score": 8, "Feedback": "Good vocabulary. Sufficient variation in word choice."},
                    {"Range": "0.5–0.69", "Score": 6, "Feedback": "Acceptable vocabulary, but could be more diverse."},
                    {"Range": "0.3–0.49", "Score": 4, "Feedback": "Low vocabulary richness. Repetitive and basic word usage."},
                    {"Range": "0–0.29", "Score": 2, "Feedback": "Very low vocabulary richness, making the text monotonous."}
                ]
            }
        }
    },
    "Clarity": {
        "Weightage": 30,
        "Metrics": {
            "Filler Word Rate": {
                "Weightage": 30,
                "ScoringBuckets": [
                    {"Range": "< 1.0%", "Score": 30, "Feedback": "Exceptional clarity. No distracting filler words."},
                    {"Range": "1.0% - 1.9%", "Score": 25, "Feedback": "Very good clarity. Minimal use of filler words."},
                    {"Range": "2.0% - 2.9%", "Score": 20, "Feedback": "Good clarity. Filler usage is present but not excessive."},
                    {"Range": "3.0% - 3.9%", "Score": 15, "Feedback": "Average clarity. Reduce filler words for better impact."},
                    {"Range": "4.0% - 4.9%", "Score": 10, "Feedback": "Low clarity. Excessive filler words distract the listener."},
                    {"Range": "> 5.0%", "Score": 5, "Feedback": "Very low clarity. The presentation is heavily disrupted by filler words."}
                ]
            }
        }
    }
}

# --- 2. LOGIC FUNCTIONS ---

def calculate_wpm(word_count, duration_sec):
    """Calculates Words Per Minute (WPM)."""
    if duration_sec <= 0:
        return 0
    return (word_count / duration_sec) * 60

def calculate_ttr(words):
    """Calculates Type-Token Ratio (TTR)."""
    if not words:
        return 0.0
    return len(set(words)) / len(words)

def count_filler_words(text):
    """Counts common filler words in the text."""
    filler_words = ["um", "uh", "like", "you know", "so", "actually", "basically", "right", "i mean", "well", "kinda", "sort of", "okay", "hmm", "ah"]
    # Case-insensitive search
    count = 0
    text_lower = text.lower()
    for filler in filler_words:
        # Use regex to count whole word matches
        count += len(re.findall(r'\b' + re.escape(filler) + r'\b', text_lower))
    return count

def check_content_keywords(text):
    """Checks for the presence of mandatory content keywords."""
    text_lower = text.lower()
    keywords = ["name", "age", "class", "school", "family", "hobbies", "goals", "unique point"]
    found_keywords = 0
    
    # Simple semantic check based on keyword presence
    keyword_map = {
        "name": ["i am", "myself", "my name"],
        "age": ["i am", "years old"],
        "class": ["class", "grade"],
        "school": ["school", "university", "college"],
        "family": ["family", "parents", "mother", "father", "siblings"],
        "hobbies": ["enjoy", "like to", "hobbies", "interests", "play"],
        "goals": ["want to be", "my goal", "aspire to", "future"],
        "unique point": ["special thing", "fun fact", "one thing people don't know"]
    }
    
    found_details = {}
    
    for key, phrases in keyword_map.items():
        if any(phrase in text_lower for phrase in phrases):
            found_keywords += 1
            found_details[key] = True
        else:
            found_details[key] = False
            
    return found_keywords, found_details

def check_flow(text):
    """Checks for flow (Salutation -> Details -> Closing). A highly simplified check."""
    text_lower = text.lower()
    
    # 1. Salutation Check
    salutation_phrases = ["hello", "good morning", "greetings"]
    has_salutation = any(text_lower.startswith(p) for p in salutation_phrases)
    
    # 2. Closing Check (must be near the end)
    closing_phrases = ["thank you", "that is all", "i'm done"]
    has_closing = any(p in text_lower[-50:] for p in closing_phrases)
    
    # Simple flow score: 5 points if both are present.
    return 1 if has_salutation and has_closing else 0

def get_score_and_feedback(metric_value, scoring_buckets, is_filler_rate=False):
    """Finds the corresponding score and feedback based on the metric value and scoring buckets."""
    best_match = None
    
    # If the scoring is based on filler rate (lower is better, higher score at top)
    if is_filler_rate:
        for bucket in scoring_buckets:
            range_str = bucket["Range"].replace("%", "").strip()
            if range_str.startswith('<'):
                threshold = float(range_str.split('<')[1].strip())
                if metric_value < threshold:
                    best_match = bucket
                    break
            elif range_str.startswith('>'):
                threshold = float(range_str.split('>')[1].strip())
                if metric_value > threshold:
                    best_match = bucket
                    break
            else: # Format X.X - Y.Y
                low, high = map(float, [r.strip() for r in range_str.split('-')])
                if low <= metric_value <= high:
                    best_match = bucket
                    break
    else:
        for bucket in scoring_buckets:
            range_str = bucket["Range"].strip()
            
            if "WPM" in range_str: 
                wpm = metric_value
                if '111 - 140' in range_str and 111 <= wpm <= 140:
                    best_match = bucket
                    break
                elif range_str.startswith('>') and wpm > 140:
                    best_match = bucket
                    break
                elif '81 - 110' in range_str and 81 <= wpm <= 110:
                    best_match = bucket
                    break
                elif range_str.startswith('<') and wpm < 80:
                    best_match = bucket
                    break
            
            else: 
                range_str = range_str.replace('–', 'to').strip()
                if range_str.startswith('>'):
                    threshold = float(range_str.split('>')[1].strip())
                    if metric_value > threshold:
                        best_match = bucket
                        break
                elif range_str.startswith('<'):
                    threshold = float(range_str.split('<')[1].strip())
                    if metric_value < threshold:
                        best_match = bucket
                        break
                else: 
                    try:
                        low, high = map(float, [r.strip() for r in range_str.split('to')])
                        if low <= metric_value <= high:
                            best_match = bucket
                            break
                    except:
                        best_match = scoring_buckets[-1] 
    if best_match is None:
        return scoring_buckets[-1]["Score"], scoring_buckets[-1]["Feedback"]
        
    return best_match["Score"], best_match["Feedback"]

def analyze_transcript(transcript, duration_sec):
    """The main scoring and feedback generation logic."""
    
    results = {}
    total_score = 0
    
    # 1. Text Pre-processing
    words = safe_word_tokenize(transcript)
    word_count = len(words)
    
    # --- 2. Calculation of Raw Metrics ---
    
    # --- Core Metrics ---
    wpm = calculate_wpm(word_count, duration_sec)
    ttr = calculate_ttr(words)
    filler_count = count_filler_words(transcript)
    filler_rate = (filler_count / word_count) * 100 if word_count > 0 else 100.0
    found_keywords, keyword_details = check_content_keywords(transcript)
    has_salutation = 1 if re.match(r'^\s*(hello|good (morning|day)|greetings)', transcript.lower()) else 0
    has_flow = check_flow(transcript)
    mock_errors_per_100_words = 0.8 
    errors_per_100_words = mock_errors_per_100_words
    grammar_score_raw = 1 - min(errors_per_100_words / 10, 1)
    
    detailed_scores = {}
    
    content_scores = detailed_scores.setdefault("Content & Structure", {"TotalScore": 0, "Metrics": {}})
    score_salutation = 5 if has_salutation else 0
    feedback_salutation = "Clear salutation present." if has_salutation else "Missing a clear, engaging salutation."
    content_scores["Metrics"]["Salutation Level"] = {"Value": has_salutation, "Score": score_salutation, "Feedback": feedback_salutation, "Weightage": 5}
    content_scores["TotalScore"] += score_salutation
    
    keyword_max_score = RUBRIC["Content & Structure"]["Metrics"]["Key word Presence"]["Rules"][0]["MaxScore"]
    score_keyword = int(keyword_max_score * (found_keywords / 8))
    feedback_keyword = f"Found {found_keywords} out of 8 key self-introduction details. (Missing: {', '.join([k for k, v in keyword_details.items() if not v])})"
    content_scores["Metrics"]["Key word Presence"] = {"Value": f"{found_keywords}/8", "Score": score_keyword, "Feedback": feedback_keyword, "Weightage": 30}
    content_scores["TotalScore"] += score_keyword
    
    score_flow = 5 if has_flow else 0
    feedback_flow = "The introduction follows a logical start-to-end structure." if has_flow else "The flow is hard to follow. Ensure a clear start and end."
    content_scores["Metrics"]["Flow"] = {"Value": has_flow, "Score": score_flow, "Feedback": feedback_flow, "Weightage": 5}
    content_scores["TotalScore"] += score_flow

    total_score += content_scores["TotalScore"]

    speech_scores = detailed_scores.setdefault("Speech Rate", {"TotalScore": 0, "Metrics": {}})
    metric_name = "Speech rate (WPM)"
    score_wpm, feedback_wpm = get_score_and_feedback(wpm, RUBRIC["Speech Rate"]["Metrics"][metric_name]["ScoringBuckets"])
    speech_scores["Metrics"][metric_name] = {"Value": f"{wpm:.2f}", "Score": score_wpm, "Feedback": feedback_wpm, "Weightage": 10}
    speech_scores["TotalScore"] += score_wpm
    total_score += score_wpm
    
    lang_scores = detailed_scores.setdefault("Language & Grammar", {"TotalScore": 0, "Metrics": {}})
    
   
    metric_name = "Grammar errors (Score)"
    score_grammar, feedback_grammar = get_score_and_feedback(grammar_score_raw, RUBRIC["Language & Grammar"]["Metrics"][metric_name]["ScoringBuckets"])
    lang_scores["Metrics"][metric_name] = {"Value": f"{grammar_score_raw:.2f}", "Score": score_grammar, "Feedback": feedback_grammar, "Weightage": 10}
    lang_scores["TotalScore"] += score_grammar
    
   
    metric_name = "Vocabulary richness (TTR)"
    score_ttr, feedback_ttr = get_score_and_feedback(ttr, RUBRIC["Language & Grammar"]["Metrics"][metric_name]["ScoringBuckets"])
    lang_scores["Metrics"][metric_name] = {"Value": f"{ttr:.2f}", "Score": score_ttr, "Feedback": feedback_ttr, "Weightage": 10}
    lang_scores["TotalScore"] += score_ttr
    
    total_score += lang_scores["TotalScore"]
    
    clarity_scores = detailed_scores.setdefault("Clarity", {"TotalScore": 0, "Metrics": {}})
    metric_name = "Filler Word Rate"
    score_filler, feedback_filler = get_score_and_feedback(filler_rate, RUBRIC["Clarity"]["Metrics"][metric_name]["ScoringBuckets"], is_filler_rate=True)
    clarity_scores["Metrics"][metric_name] = {"Value": f"{filler_rate:.2f}% ({filler_count} filler words)", "Score": score_filler, "Feedback": feedback_filler, "Weightage": 30}
    clarity_scores["TotalScore"] += score_filler
    total_score += score_filler

  
    if total_score >= 90:
        overall_feedback = "Outstanding introduction! All criteria were met with high marks, demonstrating excellent preparation and delivery."
    elif total_score >= 75:
        overall_feedback = "Very strong performance. Good grasp of content, flow, and clarity. Review areas with scores below 10 for continuous improvement."
    elif total_score >= 50:
        overall_feedback = "Solid effort. The core content is present, but work on one or two specific areas (like WPM or Filler Rate) could significantly boost your score."
    else:
        overall_feedback = "Needs improvement. Focus on ensuring all mandatory content points are covered and practicing your delivery for better pace and clarity."

    return {
        "final_score": round(total_score, 0),
        "total_word_count": word_count,
        "total_duration_sec": duration_sec,
        "detailed_feedback": detailed_scores,
        "overall_feedback": overall_feedback
    }

# --- 3. FLASK APP SETUP ---

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Renders the single-page application (SPA) HTML."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/score', methods=['POST'])
def score_transcript():
    """API endpoint for scoring the transcript."""
    try:
        data = request.json
        transcript = data.get('transcript', '')
        duration_sec = data.get('duration_sec', 0)
        
        if not transcript or not isinstance(transcript, str):
            return jsonify({"error": "Transcript text is required."}), 400
        
        try:
            duration_sec = float(duration_sec)
        except ValueError:
            return jsonify({"error": "Duration must be a valid number in seconds."}), 400
            
        if duration_sec <= 0:
            duration_sec = 60 
        result = analyze_transcript(transcript, duration_sec)
        
        return jsonify(result)
        
    except Exception as e:
        # Generic error handling
        print(f"An error occurred: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# --- 4. HTML TEMPLATE (Frontend) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Transcript Scorer</title>
    <!-- Load Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f3f4f6; }
        .score-card { transition: transform 0.3s ease-in-out; }
        .score-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
        .score-display { 
            background: linear-gradient(145deg, #10b981, #059669); 
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body class="p-4 sm:p-8">
    <div class="max-w-4xl mx-auto bg-white shadow-xl rounded-xl p-6 lg:p-10">
        <h1 class="text-3xl font-bold text-gray-800 mb-6 border-b pb-2">Self-Introduction Scoring Tool</h1>
        
        <!-- Input Form -->
        <div id="input-section" class="mb-8">
            <h2 class="text-xl font-semibold text-gray-700 mb-4">Input Transcript and Duration</h2>
            
            <div class="mb-4">
                <label for="transcript" class="block text-sm font-medium text-gray-700 mb-1">Transcript Text (Paste your self-introduction here):</label>
                <textarea id="transcript" rows="8" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-green-500 focus:border-green-500 shadow-sm" 
                    placeholder="E.g., Hello everyone, my name is Jane Doe and I am 22 years old..."></textarea>
            </div>
            
            <div class="mb-6">
                <label for="duration" class="block text-sm font-medium text-gray-700 mb-1">Duration (in Seconds, e.g., 52):</label>
                <input type="number" id="duration" class="w-full sm:w-1/3 p-3 border border-gray-300 rounded-lg focus:ring-green-500 focus:border-green-500 shadow-sm" placeholder="e.g., 52" value="52">
            </div>
            
            <button onclick="submitTranscript()" class="w-full sm:w-auto px-6 py-3 bg-green-600 text-white font-semibold rounded-lg shadow-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition duration-150">
                Analyze & Score
            </button>
        </div>
        
        <!-- Loading and Error Messages -->
        <div id="loading" class="text-center py-4 hidden">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
            <p class="text-green-600">Analyzing the transcript...</p>
        </div>
        <div id="error-message" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative hidden" role="alert">
            <span id="error-text"></span>
        </div>

        <!-- Results Section -->
        <div id="results-section" class="hidden mt-8 pt-6 border-t border-gray-200">
            <h2 class="text-2xl font-bold text-gray-800 mb-6">Evaluation Results</h2>

            <!-- Overall Score Card -->
            <div class="flex flex-col sm:flex-row items-center justify-between p-6 mb-8 rounded-xl shadow-lg score-display text-white">
                <div>
                    <p class="text-sm font-medium opacity-80 mb-1">Final Score (0-100)</p>
                    <p id="final-score" class="text-6xl font-extrabold"></p>
                </div>
                <div class="mt-4 sm:mt-0 sm:max-w-md">
                    <p class="font-semibold text-lg mb-2">Overall Feedback</p>
                    <p id="overall-feedback" class="text-sm italic opacity-90"></p>
                </div>
            </div>

            <!-- Detailed Metrics -->
            <h3 class="text-xl font-semibold text-gray-700 mb-4">Criterion-Based Feedback</h3>
            <div id="detailed-feedback" class="space-y-6">
                <!-- Scores will be injected here -->
            </div>
            
            <div class="mt-8 pt-4 border-t border-gray-200 text-sm text-gray-500">
                <p>Note: Grammar scoring is based on a complex formula in the rubric. In this live demo, a mock error rate is used to simulate the scoring logic.</p>
                <p id="raw-metrics" class="mt-2"></p>
            </div>
        </div>

    </div>

    <script>
        // Sample data for demonstration, matching the CSV example
        const sampleTranscript = "Hello everyone, myself Muskan, studying in class 8th B section from Christ Public School. I am 13 years old. I live with my family. There are 3 people in my family, me, my mother and my father. One special thing about my family is that they are very kind hearted to everyone and soft spoken. One thing I really enjoy is play, playing cricket and taking wickets. A fun fact about me is that I see in mirror and talk by myself. One thing people don't know about me is that I once stole a toy from one of my cousin. My favorite subject is science because it is very interesting. Through science I can explore the whole world and make the discoveries and improve the lives of others. Thank you for listening.";
        
        document.addEventListener('DOMContentLoaded', () => {
            document.getElementById('transcript').value = sampleTranscript;
            // The default duration is already set in the HTML input.
        });
        
        function getStatusColor(score) {
            if (score >= 20) return 'bg-green-100 text-green-800';
            if (score >= 10) return 'bg-yellow-100 text-yellow-800';
            return 'bg-red-100 text-red-800';
        }
        
        async function submitTranscript() {
            const transcript = document.getElementById('transcript').value;
            const duration_sec = document.getElementById('duration').value;
            
            const loading = document.getElementById('loading');
            const errorDiv = document.getElementById('error-message');
            const resultsSection = document.getElementById('results-section');

            loading.classList.remove('hidden');
            errorDiv.classList.add('hidden');
            resultsSection.classList.add('hidden');

            try {
                const response = await fetch('/score', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ transcript, duration_sec })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                displayResults(result);

            } catch (error) {
                document.getElementById('error-text').textContent = 'Error: ' + error.message;
                errorDiv.classList.remove('hidden');
            } finally {
                loading.classList.add('hidden');
            }
        }

        function displayResults(data) {
            document.getElementById('final-score').textContent = data.final_score;
            document.getElementById('overall-feedback').textContent = data.overall_feedback;
            document.getElementById('raw-metrics').textContent = `Word Count: ${data.total_word_count} | Duration: ${data.total_duration_sec}s`;
            
            const feedbackContainer = document.getElementById('detailed-feedback');
            feedbackContainer.innerHTML = '';

            for (const [categoryName, categoryData] of Object.entries(data.detailed_feedback)) {
                // Main Category Card
                let categoryHTML = `
                    <div class="bg-gray-50 p-4 rounded-xl shadow-md">
                        <h4 class="text-lg font-bold text-gray-800 border-b pb-2 mb-3 flex justify-between items-center">
                            <span>${categoryName}</span>
                            <span class="${getStatusColor(categoryData.TotalScore)}" style="padding: 4px 8px; border-radius: 6px; font-size: 0.9em;">
                                Total: ${categoryData.TotalScore} / ${Object.values(categoryData.Metrics).reduce((sum, m) => sum + m.Weightage, 0)}
                            </span>
                        </h4>
                        <div class="space-y-3">
                `;
                
                // Individual Metrics
                for (const [metricName, metricData] of Object.entries(categoryData.Metrics)) {
                    categoryHTML += `
                        <div class="flex items-start p-3 bg-white rounded-lg border border-gray-200">
                            <div class="flex-grow">
                                <p class="font-semibold text-gray-700">${metricName} (Max: ${metricData.Weightage})</p>
                                <p class="text-sm text-gray-500 italic">Value: ${metricData.Value}</p>
                                <p class="text-sm mt-1">${metricData.Feedback}</p>
                            </div>
                            <div class="flex-shrink-0 ml-4">
                                <span class="px-3 py-1 text-sm font-semibold rounded-full text-white bg-blue-600">
                                    ${metricData.Score}
                                </span>
                            </div>
                        </div>
                    `;
                }
                
                categoryHTML += `
                        </div>
                    </div>
                `;
                feedbackContainer.innerHTML += categoryHTML;
            }

            document.getElementById('results-section').classList.remove('hidden');
            window.scrollTo({ top: document.getElementById('results-section').offsetTop, behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':        
    app.run(debug=True, host='0.0.0.0', port=5000)