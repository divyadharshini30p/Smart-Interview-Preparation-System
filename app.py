from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- Database Models --------------------
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False, default=60)
    topic_scores = db.relationship('TopicScore', backref='quiz', lazy=True, cascade='all, delete-orphan')

    @property
    def percentage(self):
        return round((self.score / self.total) * 100, 1)

class TopicScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('score.id'), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    correct = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)

    @property
    def percentage(self):
        return (self.correct / self.total) * 100 if self.total > 0 else 0

with app.app_context():
    db.create_all()

# -------------------- 60 Questions with Topics --------------------
questions_db = [
    # Averages
    {"topic": "Averages", "question": "The average of 5 numbers is 20. If one number is 24, what is the average of the remaining four?",
     "options": ["18", "19", "20", "21"], "answer": "19",
     "explanation": "Sum of 5 numbers = 5*20 = 100. Subtract 24 → sum of 4 = 76. Average = 76/4 = 19."},
    {"topic": "Averages", "question": "Find the average of first 10 natural numbers.",
     "options": ["5", "5.5", "6", "6.5"], "answer": "5.5",
     "explanation": "Sum of first 10 natural numbers = 55, average = 55/10 = 5.5."},
    # Calendar
    {"topic": "Calendar", "question": "What day of the week was 1st January 2000?",
     "options": ["Monday", "Tuesday", "Friday", "Saturday"], "answer": "Saturday",
     "explanation": "31 Dec 1999 was Friday → 1 Jan 2000 = Saturday."},
    {"topic": "Calendar", "question": "How many Sundays are there in February 2024?",
     "options": ["4", "5", "6", "7"], "answer": "4",
     "explanation": "Feb 2024 is a leap year starting Thursday. Sundays: 4th, 11th, 18th, 25th → 4."},
    # Blood Relations
    {"topic": "Blood Relations", "question": "A is the brother of B. B is the sister of C. How is A related to C?",
     "options": ["Brother", "Sister", "Cousin", "Uncle"], "answer": "Brother",
     "explanation": "A and B are siblings, B and C are siblings → A and C are siblings. A is male → brother."},
    {"topic": "Blood Relations", "question": "Pointing to a man, a woman said, 'He is the son of my mother's only daughter.' How is the man related to the woman?",
     "options": ["Brother", "Son", "Nephew", "Husband"], "answer": "Son",
     "explanation": "My mother's only daughter is me. Son of me is my son."},
    # Probability
    {"topic": "Probability", "question": "What is the probability of getting an even number on a fair die?",
     "options": ["1/2", "1/3", "1/6", "2/3"], "answer": "1/2",
     "explanation": "Even numbers: 2,4,6 → 3 out of 6 = 1/2."},
    {"topic": "Probability", "question": "A bag contains 3 red and 2 blue balls. What is the probability of drawing a red ball?",
     "options": ["3/5", "2/5", "1/5", "4/5"], "answer": "3/5",
     "explanation": "Total balls = 5, red = 3 → probability = 3/5."},
    # Percentages
    {"topic": "Percentages", "question": "What is 20% of 150?",
     "options": ["20", "25", "30", "35"], "answer": "30",
     "explanation": "20% of 150 = 0.2 * 150 = 30."},
    {"topic": "Percentages", "question": "If a shirt costs $40 after a 20% discount, what was its original price?",
     "options": ["$48", "$50", "$52", "$55"], "answer": "$50",
     "explanation": "Let original = x. x - 0.2x = 40 → 0.8x = 40 → x = 50."},
    # Time and Work
    {"topic": "Time and Work", "question": "A can do a work in 10 days, B in 15 days. How many days together?",
     "options": ["5", "6", "7", "8"], "answer": "6",
     "explanation": "Combined work per day = 1/10 + 1/15 = 1/6 → 6 days."},
    {"topic": "Time and Work", "question": "If 5 men can complete a work in 10 days, how many men needed to complete it in 2 days?",
     "options": ["15", "20", "25", "30"], "answer": "25",
     "explanation": "Work = 5*10 = 50 man-days. For 2 days, men needed = 50/2 = 25."},
    # Time and Distance
    {"topic": "Time and Distance", "question": "A train covers 60 km in 1 hour. What is its speed in m/s?",
     "options": ["16.67", "20", "25", "30"], "answer": "16.67",
     "explanation": "60 km/h = 60 * 1000 / 3600 = 16.67 m/s."},
    {"topic": "Time and Distance", "question": "If a car travels at 40 km/h, how far will it go in 3 hours?",
     "options": ["100 km", "120 km", "140 km", "160 km"], "answer": "120 km",
     "explanation": "Distance = speed * time = 40 * 3 = 120 km."},
    # Logical Reasoning
    {"topic": "Logical Reasoning", "question": "Find the next number: 2, 4, 8, 16, ?",
     "options": ["24", "30", "32", "36"], "answer": "32",
     "explanation": "Each term multiplied by 2: 16*2 = 32."},
    {"topic": "Logical Reasoning", "question": "If all cats are dogs and some dogs are birds, which is true?",
     "options": ["All cats are birds", "Some cats are birds", "No cat is bird", "Cannot be determined"],
     "answer": "Cannot be determined",
     "explanation": "No direct relation between cats and birds."},
    # Ratio and Proportion
    {"topic": "Ratio", "question": "Divide 60 in the ratio 2:3.",
     "options": ["20,40", "24,36", "30,30", "15,45"], "answer": "24,36",
     "explanation": "Total parts = 5. 60/5 = 12. 2*12=24, 3*12=36."},
    {"topic": "Ratio", "question": "If a:b = 3:4 and b = 20, find a.",
     "options": ["15", "16", "18", "20"], "answer": "15",
     "explanation": "a/20 = 3/4 → a = 20 * 3/4 = 15."},
    # Permutations and Combinations
    {"topic": "Permutations", "question": "How many ways to arrange the letters of 'CAT'?",
     "options": ["3", "4", "5", "6"], "answer": "6",
     "explanation": "3! = 6."},
    {"topic": "Permutations", "question": "Find 5C2.",
     "options": ["10", "15", "20", "25"], "answer": "10",
     "explanation": "5!/(2!3!) = (5*4)/(2*1) = 10."},
    # Profit and Loss
    {"topic": "Profit & Loss", "question": "CP = 100, SP = 120. Profit %?",
     "options": ["10%", "15%", "20%", "25%"], "answer": "20%",
     "explanation": "Profit = 20, profit% = (20/100)*100 = 20%."},
    {"topic": "Profit & Loss", "question": "If loss = 10% and CP = 200, find SP.",
     "options": ["180", "190", "200", "210"], "answer": "180",
     "explanation": "SP = CP * (100 - loss%)/100 = 200 * 0.9 = 180."},
    # Simple and Compound Interest
    {"topic": "SI & CI", "question": "SI on 1000 at 10% for 2 years?",
     "options": ["100", "150", "200", "250"], "answer": "200",
     "explanation": "SI = (1000*10*2)/100 = 200."},
    {"topic": "SI & CI", "question": "CI on 1000 at 10% for 2 years?",
     "options": ["200", "210", "220", "230"], "answer": "210",
     "explanation": "Amount = 1000*(1.1^2)=1210, CI = 210."},
    # Data Interpretation
    {"topic": "Data Interpretation", "question": "If a pie chart shows 40% for A and total is 500, value of A?",
     "options": ["150", "200", "250", "300"], "answer": "200",
     "explanation": "40% of 500 = 200."},
    {"topic": "Data Interpretation", "question": "A bar chart shows sales: 2010:100, 2011:150, 2012:200. % increase from 2010 to 2012?",
     "options": ["50%", "75%", "100%", "125%"], "answer": "100%",
     "explanation": "Increase = 100, base = 100 → 100%."},
    # Coding Questions
    {"topic": "Coding", "question": "What is output of print(2**3) in Python?",
     "options": ["5", "6", "8", "9"], "answer": "8",
     "explanation": "2**3 = 8."},
    {"topic": "Coding", "question": "Which data type is mutable?",
     "options": ["tuple", "list", "string", "int"], "answer": "list",
     "explanation": "List is mutable; others are immutable."},
]

# Ensure exactly 60 questions
while len(questions_db) < 60:
    questions_db.extend(questions_db[:60-len(questions_db)])

# -------------------- Routes --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/practice')
def practice():
    return render_template('practice.html')

@app.route('/quiz/start')
def quiz_start():
    shuffled = random.sample(questions_db, len(questions_db))
    for q in shuffled:
        random.shuffle(q['options'])
    session['quiz_questions'] = shuffled
    session['quiz_answers'] = [None] * len(shuffled)
    session['current_question'] = 0
    return redirect(url_for('quiz_question', q_index=0))

@app.route('/quiz/question/<int:q_index>')
def quiz_question(q_index):
    questions = session.get('quiz_questions')
    if not questions or q_index < 0 or q_index >= len(questions):
        return redirect(url_for('quiz_start'))
    question = questions[q_index]
    total = len(questions)
    answers = session.get('quiz_answers', [None] * total)
    selected = answers[q_index]
    return render_template('quiz_question.html',
                           question=question,
                           q_index=q_index,
                           total=total,
                           selected=selected)

@app.route('/quiz/answer', methods=['POST'])
def quiz_answer():
    q_index = int(request.form.get('q_index'))
    answer = request.form.get('answer')
    questions = session.get('quiz_questions')
    answers = session.get('quiz_answers')
    if questions and answers and 0 <= q_index < len(questions):
        answers[q_index] = answer
        session['quiz_answers'] = answers
    if 'next' in request.form:
        next_index = q_index + 1
        if next_index < len(questions):
            return redirect(url_for('quiz_question', q_index=next_index))
        else:
            return redirect(url_for('quiz_submit'))
    elif 'prev' in request.form:
        prev_index = max(0, q_index - 1)
        return redirect(url_for('quiz_question', q_index=prev_index))
    elif 'submit' in request.form:
        return redirect(url_for('quiz_submit'))
    return redirect(url_for('quiz_question', q_index=q_index))

@app.route('/quiz/submit')
def quiz_submit():
    questions = session.get('quiz_questions')
    answers = session.get('quiz_answers')
    if not questions or not answers:
        return redirect(url_for('quiz_start'))
    
    score = 0
    topic_correct = {}
    topic_total = {}
    results = []
    
    for i, q in enumerate(questions):
        user_ans = answers[i]
        correct = q['answer']
        is_correct = (user_ans == correct)
        if is_correct:
            score += 1
        # Topic tracking
        topic = q.get('topic', 'General')
        topic_correct[topic] = topic_correct.get(topic, 0) + (1 if is_correct else 0)
        topic_total[topic] = topic_total.get(topic, 0) + 1
        
        results.append({
            'question': q['question'],
            'user_answer': user_ans,
            'correct_answer': correct,
            'explanation': q['explanation'],
            'is_correct': is_correct
        })
    
    total = len(questions)
    percentage = (score / total) * 100
    
    # Save overall score
    new_score = Score(score=score, total=total)
    db.session.add(new_score)
    db.session.flush()  # get id
    
    # Save topic scores
    for topic, corr in topic_correct.items():
        tot = topic_total[topic]
        ts = TopicScore(quiz_id=new_score.id, topic=topic, correct=corr, total=tot)
        db.session.add(ts)
    
    db.session.commit()
    
    session.pop('quiz_questions', None)
    session.pop('quiz_answers', None)
    session.pop('current_question', None)
    
    return render_template('quiz_result.html', results=results, score=score, total=total, percentage=percentage)

@app.route('/dashboard')
def dashboard():
    scores = Score.query.order_by(Score.date).all()
    
    # Prepare data for charts (JSON serializable)
    chart_data = []
    for s in scores:
        chart_data.append({
            'date': s.date.strftime('%Y-%m-%d'),
            'percentage': s.percentage
        })
    
    # Aggregate topic performance (same as before)
    topic_data = {}
    for score in scores:
        for ts in score.topic_scores:
            if ts.topic not in topic_data:
                topic_data[ts.topic] = {'correct': 0, 'total': 0}
            topic_data[ts.topic]['correct'] += ts.correct
            topic_data[ts.topic]['total'] += ts.total
    
    topic_averages = []
    for topic, data in topic_data.items():
        avg = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        topic_averages.append({'name': topic, 'avg': round(avg, 1)})
    
    weak_topics = sorted([t for t in topic_averages if t['avg'] < 60], key=lambda x: x['avg'])
    strong_topics = sorted([t for t in topic_averages if t['avg'] >= 60], key=lambda x: x['avg'], reverse=True)
    
    return render_template('dashboard.html',
                         scores=scores,           # still needed for stats & topics
                         chart_data=chart_data,   # new variable for charts
                         weak_topics=weak_topics,
                         strong_topics=strong_topics,
                         topic_averages=topic_averages)
    
    # Aggregate topic performance
    topic_data = {}
    for score in scores:
        for ts in score.topic_scores:
            if ts.topic not in topic_data:
                topic_data[ts.topic] = {'correct': 0, 'total': 0}
            topic_data[ts.topic]['correct'] += ts.correct
            topic_data[ts.topic]['total'] += ts.total
    
    topic_averages = []
    for topic, data in topic_data.items():
        avg = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        topic_averages.append({'name': topic, 'avg': round(avg, 1)})
    
    weak_topics = sorted([t for t in topic_averages if t['avg'] < 60], key=lambda x: x['avg'])
    strong_topics = sorted([t for t in topic_averages if t['avg'] >= 60], key=lambda x: x['avg'], reverse=True)
    
    return render_template('dashboard.html', 
                         scores=scores, 
                         weak_topics=weak_topics,
                         strong_topics=strong_topics,
                         topic_averages=topic_averages)

@app.route('/history')
def history():
    scores = Score.query.order_by(Score.date.desc()).all()
    return render_template('history.html', scores=scores)

@app.route('/delete/<int:id>')
def delete(id):
    score = Score.query.get_or_404(id)
    db.session.delete(score)
    db.session.commit()
    return redirect(url_for('history'))

@app.route('/delete-all')
def delete_all():
    Score.query.delete()
    db.session.commit()
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)